// 通用 AI 对话页组件，三个 Agent（算命师、量化先知、工单助手）共用这一套 UI。
// 通过 props 接收标题、占位符、接口地址，各自的页面只需传入配置即可。
// SSE 流式解析：fetch → ReadableStream → TextDecoder，逐事件更新界面。

import { useState, useRef, useEffect } from 'react'
import type { SseEvent } from '../types'

interface AiChatPageProps {
  title: string           // 页面标题，如"AI 算命师"
  subtitle: string        // 副标题说明
  placeholder: string     // 输入框占位文字
  endpoint: string        // SSE 接口路径，如 /api/v1/agent/fortune
  examplePrompts?: string[] // 示例提示词，点击快速填入
}

// 消息列表中每条消息的结构
interface Message {
  role: 'user' | 'assistant'
  // 助手消息可能包含多个块（工具调用 + 文字）
  blocks: Block[]
}

type Block =
  | { kind: 'text'; content: string }
  | { kind: 'tool'; tool: string; status: 'running' | 'done'; result?: string }

export default function AiChatPage({
  title,
  subtitle,
  placeholder,
  endpoint,
  examplePrompts = [],
}: AiChatPageProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // 每次消息更新时自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setLoading(true)

    // 追加用户消息
    setMessages(prev => [...prev, { role: 'user', blocks: [{ kind: 'text', content: text }] }])

    // 追加一条空的助手消息，后续流式填充
    setMessages(prev => [...prev, { role: 'assistant', blocks: [] }])

    try {
      const token = localStorage.getItem('token')
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 部分 agent 接口需要认证
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text }),
      })

      if (!resp.ok) {
        throw new Error(`请求失败：${resp.status}`)
      }

      const reader = resp.body!.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      // 流式读取：每次读到的 chunk 可能是半行，用 buf 缓冲直到遇到 \n\n
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buf += decoder.decode(value, { stream: true })
        // SSE 事件之间用两个换行分隔
        const parts = buf.split('\n\n')
        buf = parts.pop() ?? ''

        for (const part of parts) {
          if (!part.startsWith('data:')) continue
          const jsonStr = part.slice('data:'.length).trim()
          let event: SseEvent
          try {
            event = JSON.parse(jsonStr)
          } catch {
            continue
          }

          handleSseEvent(event)
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '请求失败'
      // 在助手消息里追加错误块
      setMessages(prev => {
        const copy = [...prev]
        const last = { ...copy[copy.length - 1] }
        last.blocks = [...last.blocks, { kind: 'text', content: `❌ ${msg}` }]
        copy[copy.length - 1] = last
        return copy
      })
    } finally {
      setLoading(false)
    }
  }

  // 根据 SSE 事件类型更新最后一条助手消息的 blocks
  function handleSseEvent(event: SseEvent) {
    setMessages(prev => {
      const copy = [...prev]
      // 最后一条始终是当前助手消息
      const last = { ...copy[copy.length - 1] }
      const blocks = [...last.blocks]

      if (event.type === 'tool_start') {
        // 工具开始调用：追加一个运行中的工具块
        blocks.push({ kind: 'tool', tool: event.tool ?? '工具', status: 'running' })
      } else if (event.type === 'tool_result') {
        // 工具结束：找到对应的 running 工具块，更新为 done
        const idx = blocks.findLastIndex(
          b => b.kind === 'tool' && b.tool === event.tool && b.status === 'running'
        )
        if (idx !== -1) {
          blocks[idx] = { kind: 'tool', tool: event.tool ?? '工具', status: 'done', result: event.result }
        }
      } else if (event.type === 'text_chunk') {
        // 文字流：追加到最后一个 text 块，没有则新建
        const lastBlock = blocks[blocks.length - 1]
        if (lastBlock?.kind === 'text') {
          blocks[blocks.length - 1] = { kind: 'text', content: lastBlock.content + (event.content ?? '') }
        } else {
          blocks.push({ kind: 'text', content: event.content ?? '' })
        }
      } else if (event.type === 'error') {
        blocks.push({ kind: 'text', content: `❌ ${event.content ?? '未知错误'}` })
      }
      // done 事件不需要处理，setLoading(false) 已在 finally 里处理

      last.blocks = blocks
      copy[copy.length - 1] = last
      return copy
    })
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter 发送，Shift+Enter 换行（与主流 AI 产品保持一致）
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={styles.page}>
      {/* 页面标题 */}
      <div className="page-header">
        <div>
          <h2 className="page-title">{title}</h2>
          <p style={{ fontSize: 13, color: '#888', marginTop: 4 }}>{subtitle}</p>
        </div>
      </div>

      {/* 消息区 */}
      <div style={styles.messageArea}>
        {messages.length === 0 && (
          <div style={styles.emptyTip}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✨</div>
            <div style={{ color: '#888', fontSize: 14 }}>发送消息开始对话</div>
            {/* 示例提示词快捷入口 */}
            {examplePrompts.length > 0 && (
              <div style={styles.examples}>
                {examplePrompts.map(p => (
                  <button
                    key={p}
                    style={styles.exampleBtn}
                    onClick={() => setInput(p)}
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={msg.role === 'user' ? styles.userRow : styles.assistantRow}>
            <div style={msg.role === 'user' ? styles.userBubble : styles.assistantBubble}>
              {msg.blocks.map((block, j) => {
                if (block.kind === 'text') {
                  return (
                    <span key={j} style={{ whiteSpace: 'pre-wrap' }}>
                      {block.content}
                    </span>
                  )
                }
                // 工具调用块
                return (
                  <div key={j} style={styles.toolBlock}>
                    <span style={styles.toolIcon}>
                      {block.status === 'running' ? '⚙️' : '✅'}
                    </span>
                    <span style={styles.toolName}>{block.tool}</span>
                    {block.status === 'running' && (
                      <span style={styles.toolRunning}>执行中...</span>
                    )}
                  </div>
                )
              })}
              {/* 助手消息还在流式输出时显示光标 */}
              {loading && msg.role === 'assistant' && i === messages.length - 1 && (
                <span style={styles.cursor}>▍</span>
              )}
            </div>
          </div>
        ))}

        {/* 滚动锚点 */}
        <div ref={bottomRef} />
      </div>

      {/* 输入区 */}
      <div style={styles.inputArea}>
        <textarea
          style={styles.textarea}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={3}
          disabled={loading}
        />
        <button
          className="btn btn--primary"
          style={{ alignSelf: 'flex-end', minWidth: 80 }}
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          {loading ? '发送中...' : '发送'}
        </button>
      </div>
    </div>
  )
}

// ── 内联样式（这里的样式比较特殊，不适合放在全局 CSS 里） ──────────────────

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  messageArea: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px 0',
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  emptyTip: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 60,
  },
  examples: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
    justifyContent: 'center',
  },
  exampleBtn: {
    padding: '6px 14px',
    borderRadius: 20,
    border: '1px solid #e0e0e0',
    background: '#fff',
    color: '#555',
    fontSize: 13,
    cursor: 'pointer',
  },
  userRow: {
    display: 'flex',
    justifyContent: 'flex-end',
  },
  assistantRow: {
    display: 'flex',
    justifyContent: 'flex-start',
  },
  userBubble: {
    maxWidth: '72%',
    background: '#4f6ef7',
    color: '#fff',
    borderRadius: '12px 12px 2px 12px',
    padding: '10px 14px',
    fontSize: 14,
    lineHeight: 1.6,
  },
  assistantBubble: {
    maxWidth: '80%',
    background: '#fff',
    border: '1px solid #e8e8e8',
    borderRadius: '12px 12px 12px 2px',
    padding: '10px 14px',
    fontSize: 14,
    lineHeight: 1.8,
    boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
  },
  toolBlock: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '4px 8px',
    background: '#f5f7ff',
    border: '1px solid #e0e7ff',
    borderRadius: 6,
    fontSize: 12,
    marginBottom: 6,
  },
  toolIcon: { fontSize: 14 },
  toolName: { color: '#4f6ef7', fontWeight: 500 },
  toolRunning: { color: '#888', fontStyle: 'italic' },
  cursor: {
    display: 'inline-block',
    animation: 'blink 1s step-end infinite',
    color: '#4f6ef7',
  },
  inputArea: {
    display: 'flex',
    gap: 12,
    alignItems: 'flex-end',
    padding: '12px 0 0',
    borderTop: '1px solid #f0f0f0',
  },
  textarea: {
    flex: 1,
    padding: '9px 12px',
    border: '1px solid #ddd',
    borderRadius: 6,
    fontSize: 14,
    fontFamily: 'inherit',
    outline: 'none',
    resize: 'none',
  },
}

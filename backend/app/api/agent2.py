"""AI 工单助手 Agent — 基于 LangChain + Ollama。

流程：
  POST /agent2/ticket  →  SSE 流式返回
    LangChain AgentExecutor 自动决定调哪个工具、循环几轮，
    最终输出对话式回答。

工具：
  search_tickets      — 按状态 / 关键字搜索工单列表
  get_ticket_detail   — 按 ID 查单张工单（含关联设备）
  get_tickets_by_asset — 按设备名查该设备的所有工单历史
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.ticket import Ticket, TicketStatus
from backend.app.models.asset import Asset

router = APIRouter(prefix="/agent2", tags=["Agent2"])

OLLAMA_BASE_URL = "http://host.docker.internal:11434"
MODEL = "llama3.1:8b"

SYSTEM_PROMPT = (
    "你是一个工单管理助手，帮用户查询工单和设备信息。\n"
    "规则：\n"
    "1. 根据用户问题，选择合适的工具查询，不要凭空捏造数据。\n"
    "2. 如果用户提到设备名称，用 get_tickets_by_asset 查该设备的工单历史。\n"
    "3. 如果用户提到工单编号，用 get_ticket_detail 查详情。\n"
    "4. 如果用户想列举或筛选工单，用 search_tickets。\n"
    "5. 回答简洁，直接给出关键信息，不要重复工具返回的原始文本。\n"
    "用中文回答。"
)


# ── Tools ──────────────────────────────────────────────────────────────────

@tool
async def search_tickets(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 10,
) -> str:
    """搜索工单列表。

    Args:
        status: 状态过滤，可选值 draft / submitted / approved / running / done / failed / closed
        keyword: 在标题和描述中搜索的关键字
        limit: 返回数量上限，默认 10
    """
    async with AsyncSessionLocal() as db:
        query = select(Ticket)

        if status:
            try:
                query = query.where(Ticket.status == TicketStatus(status))
            except ValueError:
                valid = " / ".join(s.value for s in TicketStatus)
                return f"无效状态「{status}」，可用值：{valid}"

        if keyword:
            query = query.where(
                or_(
                    Ticket.title.ilike(f"%{keyword}%"),
                    Ticket.description.ilike(f"%{keyword}%"),
                )
            )

        result = await db.execute(query.order_by(Ticket.created_at.desc()).limit(limit))
        # 上面 query = select(Ticket) 和 两个 query.where 都是在 动态拼 SQL语句， 直到这里才真正发请求到数据库。
        # order_by(Ticket.created_at.desc()) 相当于 ORDER BY created_at DESC ， 按创建时间倒序（最新的在前） 。
        # .limit(limit) 相当于 LIMIT 10 ， 限制返回条数为10条。
        tickets = result.scalars().all()

        if not tickets:
            return "没有找到符合条件的工单"

        lines = [f"共 {len(tickets)} 张工单："]
        for t in tickets:
            lines.append(
                f"  #{ t.id } {t.title} "
                f"[{t.status.value}] "
                f"{t.created_at.strftime('%Y-%m-%d')}"
            )
        return "\n".join(lines)


@tool
async def get_ticket_detail(ticket_id: int) -> str:
    """查询某张工单的详细信息，包含关联的设备信息。

    Args:
        ticket_id: 工单 ID（整数）
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Ticket)
            .options(selectinload(Ticket.asset))
            .where(Ticket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            return f"工单 #{ticket_id} 不存在"

        lines = [
            f"工单 #{ticket.id}：{ticket.title}",
            f"状态：{ticket.status.value}",
            f"描述：{ticket.description or '（无）'}",
            f"创建：{ticket.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"更新：{ticket.updated_at.strftime('%Y-%m-%d %H:%M')}",
        ]

        if ticket.asset:
            a = ticket.asset
            lines.append(f"设备：{a.name}（{a.asset_type}）")
            if a.serial_number:
                lines.append(f"  序列号：{a.serial_number}")
            if a.location:
                lines.append(f"  位置：{a.location}")
        else:
            lines.append("设备：未关联")

        return "\n".join(lines)


@tool
async def get_tickets_by_asset(asset_name: str) -> str:
    """查询某台设备的所有工单历史。

    Args:
        asset_name: 设备名称，支持模糊匹配
    """
    async with AsyncSessionLocal() as db:
        asset_result = await db.execute(
            select(Asset).where(Asset.name.ilike(f"%{asset_name}%"))
        )
        assets = asset_result.scalars().all()

        if not assets:
            return f"没有找到名称包含「{asset_name}」的设备"

        lines = []
        for asset in assets:
            ticket_result = await db.execute(
                select(Ticket)
                .where(Ticket.asset_id == asset.id)
                .order_by(Ticket.created_at.desc())
            )
            tickets = ticket_result.scalars().all()
            lines.append(
                f"设备「{asset.name}」({asset.asset_type}"
                + (f"，{asset.location}" if asset.location else "")
                + f") 共 {len(tickets)} 张工单："
            )
            if tickets:
                for t in tickets:
                    lines.append(
                        f"  #{t.id} {t.title} [{t.status.value}] {t.created_at.strftime('%Y-%m-%d')}"
                    )
            else:
                lines.append("  暂无工单记录")

        return "\n".join(lines)


# ── LangChain Agent（模块级，无状态，可复用）─────────────────────────────

_llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)
_tools = [search_tickets, get_ticket_detail, get_tickets_by_asset]

_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # Agent 思考过程必须有这个占位符
])

_agent = create_tool_calling_agent(_llm, _tools, _prompt)
_executor = AgentExecutor(agent=_agent, tools=_tools)


# ── SSE helper ─────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ── Request schema ─────────────────────────────────────────────────────────

class TicketChatRequest(BaseModel):
    message: str


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("/ticket")
async def ticket_chat(req: TicketChatRequest):
    """工单助手主接口，返回 SSE 流。

    SSE 事件类型：
      tool_start  — Agent 开始调用某工具
      tool_result — 工具返回结果
      text_chunk  — 最终回答的逐字流
      error       — 出错信息
      done        — 流结束
    """

    async def generate():
        try:
            # astream_events(version="v2") 是 LangChain 推荐的流式 API，
            # 会依次触发 on_tool_start / on_tool_end / on_chat_model_stream 等事件。
            async for event in _executor.astream_events(
                {"input": req.message},
                version="v2",
            ):
                kind = event["event"]

                if kind == "on_tool_start":
                    yield _sse({
                        "type": "tool_start",
                        "tool": event["name"],
                        "args": event["data"].get("input") or {},
                    })

                elif kind == "on_tool_end":
                    yield _sse({
                        "type": "tool_result",
                        "tool": event["name"],
                        "result": str(event["data"].get("output") or ""),
                    })

                elif kind == "on_chat_model_stream":
                    # 工具调用轮次的 chunk.content 是空字符串，只有最终回答才有文字
                    chunk = event["data"]["chunk"]
                    content = chunk.content if hasattr(chunk, "content") else ""
                    if content:
                        yield _sse({"type": "text_chunk", "content": content})

        except Exception as exc:
            yield _sse({"type": "error", "content": str(exc)})

        yield _sse({"type": "done"})

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Demo page ──────────────────────────────────────────────────────────────

@router.get("/ticket/demo", response_class=HTMLResponse)
async def ticket_demo():
    """浏览器直接打开即可使用。"""
    return HTMLResponse(content=_DEMO_HTML)


_DEMO_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎫 AI 工单助手</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: linear-gradient(135deg, #0a0e1a, #0d1b2a, #0a1628);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #d0e8ff;
  }
  .container {
    width: 760px;
    max-width: 96vw;
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 24px;
  }
  h1 {
    text-align: center;
    font-size: 2rem;
    letter-spacing: .08em;
    background: linear-gradient(90deg, #4fc3f7, #0288d1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .subtitle {
    text-align: center;
    color: #3a6a8a;
    font-size: .88rem;
    margin-top: -12px;
  }
  .input-area { display: flex; gap: 10px; }
  textarea {
    flex: 1;
    background: rgba(79,195,247,.05);
    border: 1px solid rgba(79,195,247,.2);
    border-radius: 10px;
    padding: 14px 16px;
    color: #d0e8ff;
    font-size: .95rem;
    resize: none;
    outline: none;
    height: 68px;
    transition: border-color .2s;
    font-family: inherit;
  }
  textarea::placeholder { color: #2a4a5a; }
  textarea:focus { border-color: #4fc3f7; }
  button {
    background: linear-gradient(135deg, #0288d1, #0097a7);
    border: none;
    border-radius: 10px;
    padding: 0 24px;
    color: #fff;
    font-size: .95rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity .2s;
  }
  button:disabled { opacity: .4; cursor: not-allowed; }
  .chat-box {
    background: rgba(79,195,247,.03);
    border: 1px solid rgba(79,195,247,.1);
    border-radius: 14px;
    padding: 20px;
    min-height: 380px;
    max-height: 560px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .placeholder {
    margin: auto;
    text-align: center;
    color: #1e3a4a;
    font-size: .9rem;
    line-height: 2;
  }
  .step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: .85rem;
    animation: fadeIn .3s ease;
  }
  .step-icon {
    width: 28px; height: 28px;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: .8rem;
    flex-shrink: 0;
    margin-top: 1px;
  }
  .step.calling .step-icon { background: rgba(79,195,247,.2); }
  .step.result  .step-icon { background: rgba(38,198,218,.2); }
  .step-body { flex: 1; }
  .step-label { font-weight: 600; margin-bottom: 3px; }
  .step.calling .step-label { color: #4fc3f7; }
  .step.result  .step-label { color: #26c6da; }
  .step-detail { color: #2a6a8a; word-break: break-all; white-space: pre-wrap; font-size: .82rem; }
  .answer {
    background: rgba(2,136,209,.06);
    border-left: 3px solid #0288d1;
    border-radius: 0 10px 10px 0;
    padding: 16px 18px;
    color: #b8d8f0;
    line-height: 1.9;
    white-space: pre-wrap;
    animation: fadeIn .4s ease;
    font-size: .92rem;
  }
  .error-msg {
    color: #ef5350;
    font-size: .88rem;
    padding: 12px;
    background: rgba(239,83,80,.08);
    border-radius: 8px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(79,195,247,.2);
    border-top-color: #4fc3f7;
    border-radius: 50%;
    animation: spin .7s linear infinite;
    flex-shrink: 0;
  }
  @keyframes fadeIn { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:none; } }
  .tip { text-align: center; color: #1e3a4a; font-size: .78rem; }
  .quick-btns { display: flex; flex-wrap: wrap; gap: 8px; }
  .quick-btn {
    background: rgba(79,195,247,.08);
    border: 1px solid rgba(79,195,247,.2);
    border-radius: 20px;
    padding: 5px 14px;
    color: #4fc3f7;
    font-size: .82rem;
    cursor: pointer;
    transition: background .2s;
  }
  .quick-btn:hover { background: rgba(79,195,247,.15); }
</style>
</head>
<body>
<div class="container">
  <h1>🎫 AI 工单助手</h1>
  <p class="subtitle">查工单 · 查设备 · 看状态</p>

  <div class="quick-btns">
    <button class="quick-btn" onclick="fill('列出所有待审批的工单')">待审批工单</button>
    <button class="quick-btn" onclick="fill('有哪些工单正在运行中？')">运行中工单</button>
    <button class="quick-btn" onclick="fill('最近失败的工单有哪些？')">失败工单</button>
    <button class="quick-btn" onclick="fill('查一下工单 #1 的详情')">工单详情</button>
  </div>

  <div class="input-area">
    <textarea id="input" placeholder="例：查一下所有 submitted 状态的工单 / 工单 #3 是什么情况？"></textarea>
    <button id="sendBtn" onclick="sendMessage()">查询</button>
  </div>

  <div class="chat-box" id="chatBox">
    <div class="placeholder" id="placeholder">
      💬 输入你的问题<br>例：最近有哪些失败的工单？某台设备有几张工单？
    </div>
  </div>

  <p class="tip">数据来自平台工单数据库，实时查询</p>
</div>

<script>
const TOOL_NAMES = {
  search_tickets:        '搜索工单列表',
  get_ticket_detail:     '查询工单详情',
  get_tickets_by_asset:  '查询设备工单历史',
};
const TOOL_ICONS = {
  search_tickets:        '🔍',
  get_ticket_detail:     '📋',
  get_tickets_by_asset:  '🖥️',
};

function fill(text) {
  document.getElementById('input').value = text;
  document.getElementById('input').focus();
}

function sendMessage() {
  const input = document.getElementById('input');
  const msg = input.value.trim();
  if (!msg) return;

  const box = document.getElementById('chatBox');
  document.getElementById('placeholder')?.remove();

  const userBubble = document.createElement('div');
  userBubble.style.cssText = 'text-align:right;color:#3a6a8a;font-size:.88rem;padding:6px 0;';
  userBubble.textContent = '你：' + msg;
  box.appendChild(userBubble);

  const loading = document.createElement('div');
  loading.id = 'loading';
  loading.innerHTML = '<div class="spinner" style="margin:16px auto;"></div>';
  box.appendChild(loading);
  box.scrollTop = box.scrollHeight;

  document.getElementById('sendBtn').disabled = true;
  input.value = '';

  fetch('/api/v1/agent2/ticket', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg }),
  }).then(async resp => {
    document.getElementById('loading')?.remove();
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    const toolEls = {};
    let answerEl = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split('\\n\\n');
      buf = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        let event;
        try { event = JSON.parse(line.slice(5).trim()); } catch { continue; }

        if (event.type === 'tool_start') {
          const el = document.createElement('div');
          el.className = 'step calling';
          el.innerHTML = `
            <div class="step-icon">${TOOL_ICONS[event.tool] || '⚙️'}</div>
            <div class="step-body">
              <div class="step-label">${TOOL_NAMES[event.tool] || event.tool}</div>
              <div class="step-detail" style="display:flex;align-items:center;gap:8px;">
                <div class="spinner"></div><span>查询中…</span>
              </div>
            </div>`;
          box.appendChild(el);
          toolEls[event.tool] = el;
        }

        if (event.type === 'tool_result') {
          const el = toolEls[event.tool];
          if (el) {
            el.className = 'step result';
            el.querySelector('.step-label').textContent = '✓ ' + (TOOL_NAMES[event.tool] || event.tool);
            el.querySelector('.step-detail').textContent = event.result;
          }
        }

        if (event.type === 'text_chunk') {
          if (!answerEl) {
            answerEl = document.createElement('div');
            answerEl.className = 'answer';
            box.appendChild(answerEl);
          }
          answerEl.textContent += event.content;
        }

        if (event.type === 'error') {
          const el = document.createElement('div');
          el.className = 'error-msg';
          el.textContent = '出错了：' + event.content;
          box.appendChild(el);
        }

        box.scrollTop = box.scrollHeight;
      }
    }
  }).catch(err => {
    document.getElementById('loading')?.remove();
    const el = document.createElement('div');
    el.className = 'error-msg';
    el.textContent = '连接失败：' + err.message;
    box.appendChild(el);
  }).finally(() => {
    document.getElementById('sendBtn').disabled = false;
    box.scrollTop = box.scrollHeight;
  });
}

document.getElementById('input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
</script>
</body>
</html>
"""

"""AI 算命 Agent — 演示用。

流程：
  POST /agent/fortune  →  SSE 流式返回
    1. LLM 决定调哪个工具
    2. 执行工具（日期 / 天气 / 星座）
    3. 把结果还给 LLM
    4. 循环直到 LLM 不再调工具，输出最终运势报告

直接调 Ollama（localhost:11434），不走 LiteLLM，省掉网关配置。
"""

from __future__ import annotations

import json
from datetime import datetime

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/agent", tags=["Agent"])

OLLAMA_URL = "http://host.docker.internal:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

SYSTEM_PROMPT = (
    "你是一位神秘而睿智的 AI 算命师，精通中西方命理。\n"
    "规则：\n"
    "1. 必须先调用工具获取今日日期、天气、以及用户的星座生肖信息，再开始分析。\n"
    "2. 分析要结合工具返回的具体数据（天气、星座特质、生肖性格），不能泛泛而谈。\n"
    "3. 语气神秘而亲切，适当使用类比和隐喻，让普通人也能看懂。\n"
    "4. 最后给出今日在感情、事业、财运三方面的建议，各一两句话。\n"
    "用中文回答。"
)


# ── Tool schemas (OpenAI function calling 格式) ────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "获取今天的日期和星期",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市今天的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名，如 '上海'、'Beijing'",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_zodiac",
            "description": "根据出生日期推算星座、生肖和五行",
            "parameters": {
                "type": "object",
                "properties": {
                    "birth_date": {
                        "type": "string",
                        "description": "出生日期，格式 YYYY-MM-DD，如 '1990-05-15'",
                    }
                },
                "required": ["birth_date"],
            },
        },
    },
]


# ── Tool implementations ───────────────────────────────────────────────────

def _get_current_date() -> str:
# 本地计算（CPU），没有 I/O，同步就可以了。
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"{now.year}年{now.month}月{now.day}日，{weekdays[now.weekday()]}"


async def _get_weather(city: str) -> str:
# 这里发生了 HTTP 请求（外部 API） ，需要等待返回，所以需要异步。
    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            resp = await client.get(
                f"https://wttr.in/{city}?format=3",
                headers={"User-Agent": "curl/7.68.0"},
            )
        return resp.text.strip() if resp.status_code == 200 else f"天气查询失败（{resp.status_code}）"
    except Exception as exc:
        return f"天气查询失败：{exc}"


def _get_zodiac(birth_date: str) -> str:
    try:
        dt = datetime.strptime(birth_date, "%Y-%m-%d")
    except ValueError:
        return "日期格式错误，请用 YYYY-MM-DD"

    # 西方星座
    month, day = dt.month, dt.day
    signs = [
        (1, 20, "水瓶座"), (2, 19, "双鱼座"), (3, 21, "白羊座"),
        (4, 20, "金牛座"), (5, 21, "双子座"), (6, 21, "巨蟹座"),
        (7, 23, "狮子座"), (8, 23, "处女座"), (9, 23, "天秤座"),
        (10, 23, "天蝎座"), (11, 22, "射手座"), (12, 22, "摩羯座"),
    ]
    zodiac = "摩羯座"
    for m, d, name in signs:
        if month == m and day >= d:
            zodiac = name
            break
        if month == m + 1 and day < d:
            zodiac = name
            break

    # 生肖
    animals = ["鼠","牛","虎","兔","龙","蛇","马","羊","猴","鸡","狗","猪"]
    shengxiao = animals[(dt.year - 4) % 12]

    # 五行（按天干）
    wuxing = {0:"金",1:"金",2:"水",3:"水",4:"木",5:"木",6:"火",7:"火",8:"土",9:"土"}[dt.year % 10]

    return f"星座：{zodiac} | 生肖：属{shengxiao} | 五行属{wuxing}"


async def _execute_tool(name: str, args: dict) -> str:
    if name == "get_current_date":
        return _get_current_date()
    if name == "get_weather":
        return await _get_weather(args.get("city", "上海"))
    if name == "get_zodiac":
        return _get_zodiac(args.get("birth_date", ""))
    return f"未知工具：{name}"


# ── SSE helpers ────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ── Request schema ─────────────────────────────────────────────────────────

class FortuneRequest(BaseModel):
    message: str  # 用户随意输入，如"我1990年5月15日生，帮我算今日运势"


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("/fortune")
async def fortune_chat(req: FortuneRequest):
    """算命 Agent 主接口，返回 SSE 流。

    每个 SSE 事件是一个 JSON 对象，type 字段说明类型：
      tool_start  — Agent 开始调用某工具
      tool_result — 工具返回结果
      text        — 最终运势报告
      error       — 出错信息
      done        — 流结束标志
    """

    async def generate():
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.message},
        ]

        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                for _ in range(6):  # 最多 6 轮工具调用，防止死循环
                    # 始终用流式请求：文本 chunk 实时推送，tool_calls 片段累积后处理
                    tool_calls_acc: dict[int, dict] = {}  # index → {id, name, arguments}

                    async with client.stream(
                        "POST", OLLAMA_URL,
                        json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": True},
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                            except json.JSONDecodeError:
                                continue

                            delta = chunk.get("choices", [{}])[0].get("delta", {})

                            # 文本 chunk：立即推送给前端
                            content = delta.get("content") or ""
                            if content:
                                yield _sse({"type": "text_chunk", "content": content})

                            # tool_calls chunk：按 index 累积
                            for tc in delta.get("tool_calls") or []:
                                idx = tc.get("index", 0)
                                if idx not in tool_calls_acc:
                                    tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                                if tc.get("id"):
                                    tool_calls_acc[idx]["id"] = tc["id"]
                                fn = tc.get("function", {})
                                if fn.get("name"):
                                    tool_calls_acc[idx]["name"] += fn["name"]
                                if fn.get("arguments"):
                                    tool_calls_acc[idx]["arguments"] += fn["arguments"]

                    if not tool_calls_acc:
                        # 没有工具调用，文本已逐 chunk 推送完毕
                        break

                    # 组装完整 tool_calls 列表
                    tool_calls_list = [
                        {
                            "id": tool_calls_acc[i]["id"],
                            "type": "function",
                            "function": {
                                "name": tool_calls_acc[i]["name"],
                                "arguments": tool_calls_acc[i]["arguments"],
                            },
                        }
                        for i in sorted(tool_calls_acc)
                    ]

                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": tool_calls_list,
                    })

                    for tc in tool_calls_list:
                        name = tc["function"]["name"]
                        try:
                            args = json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            args = {}

                        yield _sse({"type": "tool_start", "tool": name, "args": args})
                        result = await _execute_tool(name, args)
                        yield _sse({"type": "tool_result", "tool": name, "result": result})

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        })

        except Exception as exc:
            yield _sse({"type": "error", "content": str(exc)})

        yield _sse({"type": "done"})

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Demo page ──────────────────────────────────────────────────────────────

@router.get("/fortune/demo", response_class=HTMLResponse)
async def fortune_demo():
    """直接在浏览器打开这个 URL 就能看到演示页面。"""
    return HTMLResponse(content=_DEMO_HTML)


_DEMO_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔮 AI 算命师</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #e8e0ff;
  }
  .container {
    width: 720px;
    max-width: 96vw;
    display: flex;
    flex-direction: column;
    gap: 20px;
    padding: 24px;
  }
  h1 {
    text-align: center;
    font-size: 2rem;
    letter-spacing: .1em;
    background: linear-gradient(90deg, #f5af19, #f12711);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .subtitle {
    text-align: center;
    color: #a89fcf;
    font-size: .9rem;
    margin-top: -12px;
  }
  .input-area {
    display: flex;
    gap: 10px;
  }
  textarea {
    flex: 1;
    background: rgba(255,255,255,.07);
    border: 1px solid rgba(255,255,255,.15);
    border-radius: 12px;
    padding: 14px 16px;
    color: #e8e0ff;
    font-size: 1rem;
    resize: none;
    outline: none;
    height: 72px;
    transition: border-color .2s;
  }
  textarea::placeholder { color: #7a6fa0; }
  textarea:focus { border-color: #9c88ff; }
  button {
    background: linear-gradient(135deg, #9c88ff, #6c63ff);
    border: none;
    border-radius: 12px;
    padding: 0 24px;
    color: #fff;
    font-size: 1rem;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity .2s;
  }
  button:disabled { opacity: .5; cursor: not-allowed; }
  .chat-box {
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 16px;
    padding: 20px;
    min-height: 360px;
    max-height: 520px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .placeholder {
    margin: auto;
    text-align: center;
    color: #6b6080;
    font-size: .95rem;
    line-height: 1.8;
  }
  /* Tool step */
  .step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: .88rem;
    animation: fadeIn .3s ease;
  }
  .step-icon {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: .85rem;
    flex-shrink: 0;
    margin-top: 1px;
  }
  .step.calling .step-icon { background: rgba(156,136,255,.25); }
  .step.result  .step-icon { background: rgba( 72,199,142,.25); }
  .step-body { flex: 1; }
  .step-label {
    font-weight: 600;
    margin-bottom: 2px;
  }
  .step.calling .step-label { color: #9c88ff; }
  .step.result  .step-label { color: #48c78e; }
  .step-detail { color: #b0a8cc; word-break: break-all; }
  /* Final answer */
  .answer {
    background: rgba(245,175,25,.08);
    border-left: 3px solid #f5af19;
    border-radius: 0 12px 12px 0;
    padding: 16px 18px;
    color: #f0e6c0;
    line-height: 1.9;
    white-space: pre-wrap;
    animation: fadeIn .4s ease;
  }
  .error-msg {
    color: #ff7675;
    font-size: .9rem;
    padding: 12px;
    background: rgba(255,118,117,.1);
    border-radius: 8px;
  }
  /* Spinner */
  @keyframes spin { to { transform: rotate(360deg); } }
  .spinner {
    width: 16px; height: 16px;
    border: 2px solid rgba(156,136,255,.3);
    border-top-color: #9c88ff;
    border-radius: 50%;
    animation: spin .7s linear infinite;
    margin: auto;
  }
  @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }

  .tip {
    text-align: center;
    color: #6b6080;
    font-size: .8rem;
  }
</style>
</head>
<body>
<div class="container">
  <h1>🔮 AI 算命师</h1>
  <p class="subtitle">告诉我你的生日和所在城市，我来算今日运势</p>

  <div class="input-area">
    <textarea id="input" placeholder="例：我1990年5月15日出生，现在在上海，帮我算算今日运势"></textarea>
    <button id="sendBtn" onclick="sendMessage()">占卜</button>
  </div>

  <div class="chat-box" id="chatBox">
    <div class="placeholder" id="placeholder">
      ✨ 输入你的生日和城市<br>AI 会自动查询今日天气、推算星座生肖<br>再为你生成专属运势报告
    </div>
  </div>

  <p class="tip">Agent 会自动调用工具：查今日日期 · 查实时天气 · 推算星座生肖</p>
</div>

<script>
const TOOL_NAMES = {
  get_current_date: '查询今日日期',
  get_weather: '查询实时天气',
  get_zodiac: '推算星座命盘',
};
const TOOL_ICONS = {
  get_current_date: '📅',
  get_weather: '🌤️',
  get_zodiac: '⭐',
};

function sendMessage() {
  const input = document.getElementById('input');
  const msg = input.value.trim();
  if (!msg) return;

  const box = document.getElementById('chatBox');
  document.getElementById('placeholder')?.remove();

  // 用户气泡
  const userBubble = document.createElement('div');
  userBubble.style.cssText = 'text-align:right;color:#c5b8f0;font-size:.9rem;padding:8px 0;';
  userBubble.textContent = '你：' + msg;
  box.appendChild(userBubble);

  // 加载中
  const loading = document.createElement('div');
  loading.id = 'loading';
  loading.innerHTML = '<div class="spinner"></div>';
  loading.style.cssText = 'padding:16px;';
  box.appendChild(loading);
  box.scrollTop = box.scrollHeight;

  document.getElementById('sendBtn').disabled = true;
  input.value = '';

  fetch('/api/v1/agent/fortune', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg }),
  }).then(async resp => {
    document.getElementById('loading')?.remove();
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    const toolEls = {};  // 本次请求私有的元素引用，不跨对话共享
    let answerEl = null; // 流式文本容器，首个 text_chunk 时创建

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
                <div class="spinner" style="width:12px;height:12px;flex-shrink:0;"></div>
                <span>请求中…</span>
              </div>
            </div>`;
          box.appendChild(el);
          toolEls[event.tool] = el;  // 存到本次请求的局部 map
        }

        if (event.type === 'tool_result') {
          const el = toolEls[event.tool];  // 从局部 map 取，不会找到旧对话的元素
          if (el) {
            el.className = 'step result';
            el.querySelector('.step-label').textContent = '✓ ' + (TOOL_NAMES[event.tool] || event.tool);
            el.querySelector('.step-detail').innerHTML = escapeHtml(event.result);
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

function escapeHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

document.getElementById('input').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});
</script>
</body>
</html>
"""

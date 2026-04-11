"""AI 量化先知 Agent — A 股走势分析与短期预测。

流程：
  POST /agent1/stock  →  SSE 流式返回
    1. LLM 决定调哪个工具
    2. 获取 A 股三大指数实时行情（外部 API）
    3. 本地动量模型计算未来几日价格区间（纯本地计算）
    4. LLM 输出完整分析报告

直接调 Ollama（localhost:11434），与 agent.py 保持一致。
"""

from __future__ import annotations

import json
import re
from datetime import datetime

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/agent1", tags=["Agent1"])

OLLAMA_URL = "http://host.docker.internal:11434/v1/chat/completions"
MODEL = "llama3.1:8b"

SYSTEM_PROMPT = (
    "你是一位专业的 AI 量化分析师，代号「量化先知」，擅长 A 股市场技术分析与短期走势预测。\n"
    "规则：\n"
    "1. 必须先调用 get_astock_indices 工具获取三大指数实时行情。\n"
    "2. 对每个指数分别调用 predict_trend 工具，计算未来 5 个交易日的价格区间。\n"
    "3. 综合所有工具返回的数据进行分析，不能凭空捏造数据。\n"
    "4. 给出：大盘综合判断、各指数短期预测区间、主要风险提示。\n"
    "5. 结尾必须注明：「以上内容仅供参考，不构成任何投资建议。」\n"
    "用中文回答。"
)


# ── Tool schemas ───────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_astock_indices",
            "description": "获取 A 股三大指数（上证指数、深证成指、创业板指）的实时行情",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_trend",
            "description": "自动获取指定 A 股指数的实时价格，再用动量模型计算未来 N 个交易日的价格区间预测",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol_name": {
                        "type": "string",
                        "description": "指数名称，必须是以下之一：「上证指数」「深证成指」「创业板指」",
                    },
                    "days": {
                        "type": "integer",
                        "description": "预测天数，默认 5",
                    },
                },
                "required": ["symbol_name"],
            },
        },
    },
]


# ── Tool implementations ───────────────────────────────────────────────────

async def _get_astock_indices() -> str:
    # 调新浪财经接口（外部 HTTP），所以需要异步。
    symbols = "sh000001,sz399001,sz399006"
    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            resp = await client.get(
                f"https://hq.sinajs.cn/list={symbols}",
                headers={"Referer": "https://finance.sina.com.cn"},
            )
        if resp.status_code != 200:
            return f"行情获取失败（HTTP {resp.status_code}）"

        # 新浪返回 GBK 编码
        text = resp.content.decode("gbk", errors="replace")

        results = []
        names = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指"}
        for sym, display in names.items():
            match = re.search(rf'hq_str_{sym}="([^"]+)"', text)
            if not match:
                continue
            fields = match.group(1).split(",")
            if len(fields) < 10:
                continue
            # fields: 名称,今开,昨收,当前价,最高,最低,...
            cur   = float(fields[3])
            prev  = float(fields[2])
            high  = float(fields[4])
            low   = float(fields[5])
            chg   = cur - prev
            pct   = chg / prev * 100
            sign  = "+" if chg >= 0 else ""
            results.append(
                f"{display}：{cur:.2f}  {sign}{chg:.2f}（{sign}{pct:.2f}%）"
                f"  今日区间 {low:.2f}~{high:.2f}"
            )

        return "\n".join(results) if results else "未能解析行情数据"
    except Exception as exc:
        return f"行情获取异常：{exc}"


NAME_TO_SYMBOL = {
    "上证指数": "sh000001",
    "深证成指": "sz399001",
    "创业板指": "sz399006",
}


async def _predict_trend(symbol_name: str, days: int = 5) -> str:
    # 先异步取当前价格，再本地计算——不依赖 LLM 传数字。
    sym = NAME_TO_SYMBOL.get(symbol_name)
    if not sym:
        return f"不支持的指数名称：{symbol_name}，请用「上证指数」「深证成指」或「创业板指」"

    try:
        async with httpx.AsyncClient(timeout=8.0, trust_env=False) as client:
            resp = await client.get(
                f"https://hq.sinajs.cn/list={sym}",
                headers={"Referer": "https://finance.sina.com.cn"},
            )
        text = resp.content.decode("gbk", errors="replace")
        match = re.search(rf'hq_str_{sym}="([^"]+)"', text)
        if not match:
            return "行情数据解析失败"
        fields = match.group(1).split(",")
        current_price = float(fields[3])
        prev_close    = float(fields[2])
        change_pct    = (current_price - prev_close) / prev_close * 100
    except Exception as exc:
        return f"获取行情失败：{exc}"

    # 动量模型：以今日涨跌幅的 30% 作为每日衰减动量，±1.2% 作为日波动带。
    momentum   = change_pct * 0.30
    volatility = current_price * 0.012

    lines = [f"【{symbol_name}】当前 {current_price:.2f}，今日{'+' if change_pct>=0 else ''}{change_pct:.2f}%"]
    lines.append(f"未来 {days} 个交易日预测区间（动量模型）：")
    price = current_price
    for i in range(1, days + 1):
        price = price * (1 + momentum / 100)
        lines.append(f"  第 {i} 日：{price - volatility:.2f} ~ {price + volatility:.2f}（中枢 {price:.2f}）")

    trend = "震荡偏多" if momentum > 0.1 else ("震荡偏空" if momentum < -0.1 else "窄幅震荡")
    lines.append(f"趋势判断：{trend}  |  模型置信度：低（仅供参考）")
    return "\n".join(lines)


async def _execute_tool(name: str, args: dict) -> str:
    if name == "get_astock_indices":
        return await _get_astock_indices()
    if name == "predict_trend":
        return await _predict_trend(
            symbol_name=args.get("symbol_name", "上证指数"),
            days=int(args.get("days", 5)),
        )
    return f"未知工具：{name}"


# ── SSE helpers ────────────────────────────────────────────────────────────

def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ── Request schema ─────────────────────────────────────────────────────────

class StockRequest(BaseModel):
    message: str  # 用户问题，如"帮我分析一下今天 A 股的情况"


# ── Endpoint ───────────────────────────────────────────────────────────────

@router.post("/stock")
async def stock_chat(req: StockRequest):
    """量化先知 Agent 主接口，返回 SSE 流。"""

    async def generate():
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": req.message},
        ]

        got_text = False
        try:
            async with httpx.AsyncClient(timeout=120.0, trust_env=False) as client:
                for _ in range(8):
                    resp = await client.post(
                        OLLAMA_URL,
                        json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": False},
                    )
                    resp.raise_for_status()
                    choice = resp.json()["choices"][0]
                    msg = choice["message"]
                    messages.append(msg)

                    tool_calls = msg.get("tool_calls") or []
                    if not tool_calls:
                        yield _sse({"type": "text", "content": msg.get("content", "")})
                        got_text = True
                        break

                    for tool_call in tool_calls:
                        function_call = tool_call["function"]
                        name = function_call["name"]
                        args = json.loads(function_call.get("arguments", "{}"))

                        yield _sse({"type": "tool_start", "tool": name, "args": args})
                        result = await _execute_tool(name, args)
                        yield _sse({"type": "tool_result", "tool": name, "result": result})

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result,
                        })

                # 工具调用完毕但 LLM 没有生成最终文字，强制不带 tools 再请求一次
                if not got_text:
                    messages.append({"role": "user", "content": "请根据以上所有工具返回的数据，生成完整的分析报告。"})
                    resp = await client.post(
                        OLLAMA_URL,
                        json={"model": MODEL, "messages": messages, "stream": False},
                    )
                    resp.raise_for_status()
                    final_msg = resp.json()["choices"][0]["message"]
                    yield _sse({"type": "text", "content": final_msg.get("content", "")})

        except Exception as exc:
            yield _sse({"type": "error", "content": str(exc)})

        yield _sse({"type": "done"})

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Demo page ──────────────────────────────────────────────────────────────

@router.get("/stock/demo", response_class=HTMLResponse)
async def stock_demo():
    """直接在浏览器打开查看演示页面。"""
    return HTMLResponse(content=_DEMO_HTML)


_DEMO_HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📈 AI 量化先知</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'PingFang SC', 'Microsoft YaHei', 'Courier New', monospace;
    background: #060d1a;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #c8d8e8;
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
    background: linear-gradient(90deg, #00e676, #00bcd4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .subtitle {
    text-align: center;
    color: #4a7a9b;
    font-size: .88rem;
    margin-top: -12px;
  }
  .input-area {
    display: flex;
    gap: 10px;
  }
  textarea {
    flex: 1;
    background: rgba(0,230,118,.05);
    border: 1px solid rgba(0,230,118,.2);
    border-radius: 10px;
    padding: 14px 16px;
    color: #c8d8e8;
    font-size: .95rem;
    resize: none;
    outline: none;
    height: 68px;
    transition: border-color .2s;
    font-family: inherit;
  }
  textarea::placeholder { color: #2a5a6b; }
  textarea:focus { border-color: #00e676; }
  button {
    background: linear-gradient(135deg, #00c853, #00838f);
    border: none;
    border-radius: 10px;
    padding: 0 24px;
    color: #fff;
    font-size: .95rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    letter-spacing: .05em;
    transition: opacity .2s;
  }
  button:disabled { opacity: .4; cursor: not-allowed; }
  .chat-box {
    background: rgba(0,230,118,.03);
    border: 1px solid rgba(0,230,118,.12);
    border-radius: 14px;
    padding: 20px;
    min-height: 380px;
    max-height: 540px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .placeholder {
    margin: auto;
    text-align: center;
    color: #1e4a5c;
    font-size: .9rem;
    line-height: 2;
  }
  /* Tool step */
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
  .step.calling .step-icon { background: rgba(0,188,212,.2); }
  .step.result  .step-icon { background: rgba(0,230,118,.2); }
  .step-body { flex: 1; }
  .step-label { font-weight: 600; margin-bottom: 3px; }
  .step.calling .step-label { color: #00bcd4; }
  .step.result  .step-label { color: #00e676; }
  .step-detail { color: #4a8a6b; word-break: break-all; white-space: pre-wrap; font-size: .82rem; }
  /* Final answer */
  .answer {
    background: rgba(0,230,118,.06);
    border-left: 3px solid #00e676;
    border-radius: 0 10px 10px 0;
    padding: 16px 18px;
    color: #b8e8c8;
    line-height: 1.9;
    white-space: pre-wrap;
    animation: fadeIn .4s ease;
    font-size: .92rem;
  }
  .error-msg {
    color: #ff5252;
    font-size: .88rem;
    padding: 12px;
    background: rgba(255,82,82,.08);
    border-radius: 8px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .spinner {
    width: 14px; height: 14px;
    border: 2px solid rgba(0,230,118,.2);
    border-top-color: #00e676;
    border-radius: 50%;
    animation: spin .7s linear infinite;
    flex-shrink: 0;
  }
  @keyframes fadeIn { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:none; } }
  .tip {
    text-align: center;
    color: #1e4a5c;
    font-size: .78rem;
  }
</style>
</head>
<body>
<div class="container">
  <h1>📈 AI 量化先知</h1>
  <p class="subtitle">实时拉取 A 股三大指数 · 动量模型预测未来 5 日区间</p>

  <div class="input-area">
    <textarea id="input" placeholder="例：帮我分析今天 A 股大盘走势，预测未来几天的情况"></textarea>
    <button id="sendBtn" onclick="sendMessage()">分析</button>
  </div>

  <div class="chat-box" id="chatBox">
    <div class="placeholder" id="placeholder">
      📊 输入你的问题<br>Agent 会自动获取三大指数实时行情<br>再用动量模型计算短期价格区间
    </div>
  </div>

  <p class="tip">⚠️ 以上内容仅供技术演示，不构成任何投资建议</p>
</div>

<script>
const TOOL_NAMES = {
  get_astock_indices: '拉取三大指数行情',
  predict_trend:      '动量模型预测区间',
};
const TOOL_ICONS = {
  get_astock_indices: '📡',
  predict_trend:      '🔢',
};

function sendMessage() {
  const input = document.getElementById('input');
  const msg = input.value.trim();
  if (!msg) return;

  const box = document.getElementById('chatBox');
  document.getElementById('placeholder')?.remove();

  const userBubble = document.createElement('div');
  userBubble.style.cssText = 'text-align:right;color:#4a8a6b;font-size:.88rem;padding:6px 0;';
  userBubble.textContent = '你：' + msg;
  box.appendChild(userBubble);

  const loading = document.createElement('div');
  loading.id = 'loading';
  loading.innerHTML = '<div class="spinner" style="margin:16px auto;"></div>';
  box.appendChild(loading);
  box.scrollTop = box.scrollHeight;

  document.getElementById('sendBtn').disabled = true;
  input.value = '';

  fetch('/api/v1/agent1/stock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg }),
  }).then(async resp => {
    document.getElementById('loading')?.remove();
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    const toolEls = {};

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
                <div class="spinner"></div>
                <span>请求中…</span>
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
            el.querySelector('.step-detail').innerHTML = escapeHtml(event.result);
          }
        }

        if (event.type === 'text') {
          const answerEl = document.createElement('div');
          answerEl.className = 'answer';
          answerEl.textContent = event.content;
          box.appendChild(answerEl);
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

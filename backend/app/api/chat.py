"""Chat proxy endpoint — forwards requests to LiteLLM using master key."""

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Request, Response

from backend.app.core.config import settings
from backend.app.core.dependencies import CurrentUser

router = APIRouter(prefix="/chat", tags=["Chat"])

RATE_LIMIT = 5    # requests per window
RATE_WINDOW = 60  # seconds


@router.post("/completions")
async def chat_completions(request: Request, current_user: CurrentUser):
    """
    Proxy chat completions to LiteLLM.

    - JWT 鉴权（CurrentUser dependency）
    - Redis 固定窗口限流：每用户 5 次 / 60 秒
    - 用 master key 转发请求体给 LiteLLM
    """
    # ── 限流 ──────────────────────────────────────────────────────────────────
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        rate_key = f"ratelimit:{current_user.id}"
        count = await r.incr(rate_key)
        if count == 1:
            # 第一次请求时设置过期，保证窗口 60 秒后自动重置
            await r.expire(rate_key, RATE_WINDOW)
        if count > RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {RATE_LIMIT} requests per {RATE_WINDOW}s",
            )
    finally:
        await r.aclose()

    # ── 转发给 LiteLLM ────────────────────────────────────────────────────────
    body = await request.body()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.litellm_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.litellm_master_key}",
                "Content-Type": "application/json",
            },
            content=body,
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )

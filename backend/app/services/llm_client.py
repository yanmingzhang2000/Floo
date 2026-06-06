"""底层大模型调用封装。

为什么单独抽出来：生成新闻和批改默写都需要调 LLM，
把 HTTP 调用、超时、JSON 解析、降级逻辑集中在一处，
上层 service 只关心 prompt 构造和结果消费。
"""
import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

log = logging.getLogger(__name__)


async def chat_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """调用 LLM 并解析返回的 JSON。

    为什么强制 json_object 格式：避免模型返回多余解释文字导致 json.loads 失败。
    """
    if not settings.LLM_API_KEY:
        log.debug("LLM_API_KEY 未配置，返回空 dict 让调用方走 mock")
        return {}

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    log.debug("调用 LLM model=%s temperature=%s", settings.LLM_MODEL, temperature)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    # 容错：有些模型返回时带 ```json 包裹
    content = re.sub(
        r"^```(?:json)?|```$", "", content.strip(), flags=re.MULTILINE
    ).strip()
    result = json.loads(content)
    log.debug("LLM 返回 JSON keys=%s", list(result.keys()))
    return result

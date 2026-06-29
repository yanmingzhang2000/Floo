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
    timeout: float = 90.0,  # 生成3篇文章需要更长时间，Railway冷启动也有延迟
) -> dict[str, Any] | None:
    """调用 LLM 并解析返回的 JSON。

    为什么不传 response_format：Gemini 兼容层不支持 json_object 参数，
    传了直接 400。所有调用方的 system_prompt 已明确要求只输出 JSON，
    模型会自然遵守；容错逻辑会剥掉 ```json 包裹。
    """
    if not settings.LLM_API_KEY:
        log.debug("LLM_API_KEY 未配置，返回 None 让调用方走降级")
        return None

    # response_format=json_object 是 OpenAI 专属，Gemini 兼容层不支持会返回 400
    # 所有 prompt 已在 system_prompt 里明确要求返回 JSON，模型会自然遵守
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    log.debug("调用 LLM model=%s temperature=%s", settings.LLM_MODEL, temperature)

    try:
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
    except httpx.HTTPStatusError as e:
        log.debug(
            "LLM HTTP 错误: status=%s body=%s",
            e.response.status_code,
            e.response.text[:200],
        )
        return None
    except Exception as e:
        log.debug("LLM 调用失败: %s", e)
        return None

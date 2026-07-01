"""底层大模型调用封装。

为什么单独抽出来：生成新闻和批改默写都需要调 LLM，
把 HTTP 调用、超时、JSON 解析、降级逻辑集中在一处，
上层 service 只关心 prompt 构造和结果消费。
"""
import asyncio
import json
import logging
import re
from typing import Any

import httpx

from app.config import settings

log = logging.getLogger(__name__)

# 最大重试次数；指数退避基数 1s、2s、4s
_MAX_RETRIES = 3
_RETRY_BACKOFF = 1.0


def _is_transient(exc: Exception) -> bool:
    """判断异常是否值得重试（网络超时、连接错误、429 限流、5xx、JSON 解析失败）。"""
    if isinstance(exc, httpx.TimeoutException | httpx.ConnectError):
        log.debug("瞬时异常 %s，将重试", type(exc).__name__)
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        # 429 限流和 5xx 服务端错误值得重试
        if status == 429 or status >= 500:
            log.debug("HTTP %s 将重试", status)
            return True
        log.debug("HTTP %s 不重试（客户端错误）", status)
        return False
    if isinstance(exc, json.JSONDecodeError):
        # 模型每次生成输出不同，格式错误重试可能得到正确结果
        log.debug("JSON 解析失败将重试: %s", exc)
        return True
    log.debug("未知异常 %s 不重试", type(exc).__name__)
    return False


async def chat_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    timeout: float = 90.0,
) -> dict[str, Any] | None:
    """调用 LLM 并解析返回的 JSON。

    为什么不传 response_format：Gemini 兼容层不支持 json_object 参数，
    传了直接 400。所有调用方的 system_prompt 已明确要求只输出 JSON，
    模型会自然遵守；容错逻辑会剥掉 ```json 包裹。
    """
    if not settings.LLM_API_KEY:
        log.debug("LLM_API_KEY 未配置，返回 None 让调用方走降级")
        return None

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
    url = f"{settings.LLM_BASE_URL}/chat/completions"

    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        log.debug(
            "调用 LLM attempt=%s/%s model=%s timeout=%s",
            attempt, _MAX_RETRIES, settings.LLM_MODEL, timeout,
        )
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            log.debug("LLM 原始输出前200字: %s", content[:200])

            # 从 LLM 输出中提取 JSON：找到第一个 { 和最后一个 }，
            # 忽略前后的 markdown 包裹、说明文字等干扰内容
            first_brace = content.find("{")
            last_brace = content.rfind("}")
            if first_brace != -1 and last_brace > first_brace:
                json_str = content[first_brace:last_brace + 1]
            else:
                # 兜底：尝试去掉 ```json ... ``` 包裹
                json_str = re.sub(
                    r"^```(?:json)?\s*|\s*```$",
                    "", content.strip(), flags=re.MULTILINE,
                ).strip()

            result = json.loads(json_str)
            log.debug("LLM 返回 JSON keys=%s", list(result.keys()))
            return result

        except (httpx.HTTPStatusError, httpx.TimeoutException,
                httpx.ConnectError, json.JSONDecodeError, KeyError) as e:
            last_exc = e
            log.warning(
                "LLM 第 %s 次调用失败: %s (类型=%s)",
                attempt, e, type(e).__name__,
            )
            if attempt < _MAX_RETRIES and _is_transient(e):
                wait = _RETRY_BACKOFF * (2 ** (attempt - 1))
                log.warning("%s 秒后重试", wait)
                await asyncio.sleep(wait)
            else:
                log.warning("LLM 调用最终失败 (attempt=%s)", attempt)
                return None

    log.warning("LLM 调用全部 %s 次重试后失败", _MAX_RETRIES)
    return None

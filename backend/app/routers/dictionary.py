"""
词典查询代理接口。

为什么单独建路由：有道API有CORS限制，前端无法直接调用，
后端代理解决跨域问题。
"""
import logging

import httpx
from fastapi import APIRouter, HTTPException

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])


@router.get("/lookup")
async def lookup_word(word: str):
    """代理有道词典API查询。"""
    if not word or not word.strip():
        raise HTTPException(400, "单词不能为空")

    url = f"https://dict.youdao.com/jsonapi?q={word}&dicts=ec&doctype=json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            data = resp.json()
            log.debug("词典查询 word=%s status=%s", word, resp.status_code)
            return data
    except httpx.TimeoutException:
        log.debug("词典查询超时 word=%s", word)
        raise HTTPException(504, "词典查询超时，请稍后重试")
    except Exception as e:
        log.debug("词典查询失败 word=%s error=%s", word, e)
        raise HTTPException(500, "词典查询失败")

"""
词典查询代理接口。

为什么单独建路由：有道API有CORS限制，前端无法直接调用，
后端代理解决跨域问题。

为什么加内存缓存：有道 API 单响应 20-100KB，用户连续点击同一批
常见词（the, is, real 等）时每次都走网络太慢；进程内 LRU 缓存
让热词秒返回。缓存无需失效，词典释义几乎不变；进程重启自然清空。
"""
import logging
from collections import OrderedDict
from threading import Lock

import httpx
from fastapi import APIRouter, HTTPException

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])

# LRU 缓存：key=小写单词，value=完整响应 JSON。
# 2000 条足够覆盖常见词汇量；每条约 30KB，总占用约 60MB 可接受。
_CACHE_MAX = 2000
_cache: "OrderedDict[str, dict]" = OrderedDict()
_cache_lock = Lock()


def _cache_get(key: str) -> dict | None:
    """线程安全地获取并把 key 提到 LRU 头部。"""
    with _cache_lock:
        if key not in _cache:
            return None
        _cache.move_to_end(key)
        return _cache[key]


def _cache_put(key: str, value: dict) -> None:
    """写入缓存并淘汰最老项。"""
    with _cache_lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)


@router.get("/lookup")
async def lookup_word(word: str):
    """代理有道词典API查询，进程内 LRU 缓存加速。"""
    if not word or not word.strip():
        raise HTTPException(400, "单词不能为空")

    key = word.strip().lower()
    cached = _cache_get(key)
    if cached is not None:
        log.debug("词典缓存命中 word=%s cache_size=%s", key, len(_cache))
        return cached

    url = f"https://dict.youdao.com/jsonapi?q={word}&dicts=ec&doctype=json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            data = resp.json()
            log.debug("词典查询 word=%s status=%s", word, resp.status_code)
            _cache_put(key, data)
            return data
    except httpx.TimeoutException:
        log.debug("词典查询超时 word=%s", word)
        raise HTTPException(504, "词典查询超时，请稍后重试")
    except Exception as e:
        log.debug("词典查询失败 word=%s error=%s", word, e)
        raise HTTPException(500, "词典查询失败")

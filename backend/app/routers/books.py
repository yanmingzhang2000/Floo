"""名著书本路由 - Gutendex API 代理 + Gutenberg 全文解析。"""
import logging
import re
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserBookProgress

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/books", tags=["books"])

GUTENDEX_BASE = "https://gutendex.com"
GUTENBERG_TEXT = "https://www.gutenberg.org/cache/epub"

# 热门英文公版书 ID（精心挑选适合英语学习的经典）
POPULAR_IDS = [
    1342,   # Pride and Prejudice
    11,     # Alice's Adventures in Wonderland
    84,     # Frankenstein
    1661,   # The War of the Worlds
    2701,   # Moby Dick
    1952,   # The Yellow Wallpaper
    345,    # Dracula
    120,    # Treasure Island
    219,    # Heart of Darkness
    16328,  # Beowulf
    98,     # A Tale of Two Cities
    23,     # Narrative of the Life of Frederick Douglass
    174,    # The Picture of Dorian Gray
    74,     # The Adventures of Tom Sawyer
    2600,   # War and Peace
]


@router.get("/popular")
async def get_popular_books(page: int = Query(1, ge=1)):
    """获取热门名著列表，从预设的经典书单 + Gutendex 热门补充。"""
    ids_str = ",".join(str(i) for i in POPULAR_IDS)
    url = f"{GUTENDEX_BASE}/books?ids={ids_str}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            log.debug("Gutendex popular response: %d books", len(data.get("results", [])))
            return data
        except httpx.HTTPError as e:
            log.debug("Gutendex popular request failed: %s, falling back to empty", e)
            return {"count": 0, "results": []}


@router.get("/search")
async def search_books(query: str = Query(...), page: int = Query(1, ge=1)):
    """代理 Gutendex 搜索接口，按书名/作者搜索公版书。"""
    url = f"{GUTENDEX_BASE}/books?search={query}&page={page}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            log.debug("Gutendex search '%s': %d results", query, data.get("count", 0))
            return data
        except httpx.HTTPError as e:
            log.debug("Gutendex search failed: %s", e)
            raise HTTPException(502, "书库搜索暂时不可用")


@router.get("/{gutenberg_id}")
async def get_book_detail(gutenberg_id: int):
    """获取单本书详情（元数据）。"""
    url = f"{GUTENDEX_BASE}/books/{gutenberg_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            log.debug("Gutendex detail failed for %d: %s", gutenberg_id, e)
            raise HTTPException(502, "获取书本详情失败")


def _parse_chapters(text: str) -> list[dict]:
    """将 Gutenberg 全文按章节标题拆分为章节列表。
    
    支持常见格式：Chapter X, CHAPTER X, 第X章, 以及罗马数字章节。
    如果无法识别章节标记，返回整本书作为单章。
    """
    # 常见章节标题模式
    patterns = [
        r'^(?:CHAPTER|Chapter)\s+(\d+[IVX]*)',
        r'^(?:BOOK|Book)\s+(\d+[IVX]*)',
        r'^\s*([IVX]+)\.\s+',  # 罗马数字章节 "I. Title"
        r'^\s*PART\s+(\d+)',
    ]
    
    lines = text.split('\n')
    chapter_starts = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        for pat in patterns:
            m = re.match(pat, stripped)
            if m:
                chapter_starts.append((i, stripped))
                break
    
    if len(chapter_starts) < 2:
        # 无法识别章节，截取前 5000 字作为预览
        preview = text[:5000].strip()
        return [{"title": "全文", "start": 0, "end": len(text), "preview": preview}]
    
    chapters = []
    for idx, (start_line, title) in enumerate(chapter_starts):
        end_line = chapter_starts[idx + 1][0] if idx + 1 < len(chapter_starts) else len(lines)
        chapter_text = '\n'.join(lines[start_line:end_line]).strip()
        preview = chapter_text[:500]
        chapters.append({
            "title": title,
            "start": start_line,
            "end": end_line,
            "preview": preview,
        })
    
    log.debug("Parsed %d chapters from gutenberg_id=%d", len(chapters), 0)
    return chapters


# 缓存已解析的章节结构（内存缓存，避免重复下载全文）
_chapter_cache: dict[int, list[dict]] = {}


@router.get("/{gutenberg_id}/chapters")
async def get_chapters(gutenberg_id: int):
    """获取书本章节列表（自动解析全文结构）。"""
    # 先从 Gutendex 获取 txt 下载链接
    detail_url = f"{GUTENDEX_BASE}/books/{gutenberg_id}"
    txt_url = None
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(detail_url)
            resp.raise_for_status()
            book = resp.json()
            formats = book.get("formats", {})
            txt_url = formats.get("text/plain; charset=utf-8") or formats.get("text/plain")
        except httpx.HTTPError as e:
            log.debug("Failed to get book detail for %d: %s", gutenberg_id, e)
            return {"chapters": []}
    
    if not txt_url:
        log.debug("No txt format available for %d", gutenberg_id)
        return {"chapters": []}
    
    # 检查缓存
    if gutenberg_id in _chapter_cache:
        return {"chapters": _chapter_cache[gutenberg_id]}
    
    # 下载全文并解析
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(txt_url)
            resp.raise_for_status()
            full_text = resp.text
            chapters = _parse_chapters(full_text)
            _chapter_cache[gutenberg_id] = chapters
            return {"chapters": chapters}
        except httpx.HTTPError as e:
            log.debug("Failed to download text for %d: %s", gutenberg_id, e)
            return {"chapters": []}


@router.get("/{gutenberg_id}/chapter/{chapter_idx}")
async def get_chapter_text(gutenberg_id: int, chapter_idx: int):
    """获取指定章节的完整文本。"""
    # 先获取章节列表
    if gutenberg_id not in _chapter_cache:
        detail_url = f"{GUTENDEX_BASE}/books/{gutenberg_id}"
        txt_url = None
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(detail_url)
                resp.raise_for_status()
                book = resp.json()
                formats = book.get("formats", {})
                txt_url = formats.get("text/plain; charset=utf-8") or formats.get("text/plain")
            except httpx.HTTPError:
                raise HTTPException(502, "获取书本信息失败")
        
        if not txt_url:
            raise HTTPException(404, "无可用文本格式")
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(txt_url)
                resp.raise_for_status()
                full_text = resp.text
                _chapter_cache[gutenberg_id] = _parse_chapters(full_text)
            except httpx.HTTPError:
                raise HTTPException(502, "下载书本文本失败")
    
    chapters = _chapter_cache.get(gutenberg_id, [])
    if not chapters:
        raise HTTPException(404, "章节数据为空")
    
    # -1 表示全文模式
    if chapter_idx == -1:
        # 返回全文预览（前 5000 字）
        async with httpx.AsyncClient(timeout=30) as client:
            detail_url = f"{GUTENDEX_BASE}/books/{gutenberg_id}"
            try:
                resp = await client.get(detail_url)
                book = resp.json()
                txt_url = book.get("formats", {}).get("text/plain; charset=utf-8") or book.get("formats", {}).get("text/plain")
                if txt_url:
                    resp2 = await client.get(txt_url)
                    return {"title": chapters[0]["title"] if chapters else "全文", "text": resp2.text[:5000]}
            except httpx.HTTPError:
                pass
        return {"title": "全文", "text": "加载失败，请重试"}
    
    if chapter_idx < 0 or chapter_idx >= len(chapters):
        raise HTTPException(400, "章节索引无效")
    
    ch = chapters[chapter_idx]
    
    # 下载全文提取该章节
    detail_url = f"{GUTENDEX_BASE}/books/{gutenberg_id}"
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(detail_url)
            book = resp.json()
            txt_url = book.get("formats", {}).get("text/plain; charset=utf-8") or book.get("formats", {}).get("text/plain")
            if not txt_url:
                raise HTTPException(502, "无可用文本")
        except httpx.HTTPError:
            raise HTTPException(502, "获取书本信息失败")
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(txt_url)
            resp.raise_for_status()
            lines = resp.text.split('\n')
            chapter_text = '\n'.join(lines[ch["start"]:ch["end"]]).strip()
            return {"title": ch["title"], "text": chapter_text}
        except httpx.HTTPError:
            raise HTTPException(502, "下载章节文本失败")


@router.get("/my")
async def get_my_books(user_id: int, db: Session = Depends(get_db)):
    """获取用户正在读的书列表（含阅读进度）。"""
    from sqlalchemy import func
    progress = db.query(
        UserBookProgress.gutenberg_id,
        func.count(UserBookProgress.id).label("chapters_read")
    ).filter(
        UserBookProgress.user_id == user_id
    ).group_by(UserBookProgress.gutenberg_id).all()
    
    if not progress:
        return {"books": []}
    
    # 批量获取书本元数据
    ids_str = ",".join(str(p.gutenberg_id) for p in progress)
    books_meta = {}
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{GUTENDEX_BASE}/books?ids={ids_str}")
            resp.raise_for_status()
            for book in resp.json().get("results", []):
                books_meta[book["id"]] = book
        except httpx.HTTPError:
            pass
    
    result = []
    for p in progress:
        meta = books_meta.get(p.gutenberg_id, {})
        result.append({
            "gutenberg_id": p.gutenberg_id,
            "title": meta.get("title", f"Book #{p.gutenberg_id}"),
            "author": meta.get("authors", [{}])[0].get("name", "未知"),
            "cover_url": meta.get("formats", {}).get("image/jpeg"),
            "chapters_read": p.chapters_read,
        })
    
    return {"books": result}


@router.post("/mark-read")
async def mark_chapter_read(data: dict, db: Session = Depends(get_db)):
    """标记某章节已读。"""
    user_id = data.get("user_id")
    gutenberg_id = data.get("gutenberg_id")
    chapter_idx = data.get("chapter_idx")
    
    if not all([user_id, gutenberg_id, chapter_idx is not None]):
        raise HTTPException(400, "参数不完整")
    
    # 检查是否已标记
    existing = db.query(UserBookProgress).filter_by(
        user_id=user_id, gutenberg_id=gutenberg_id, chapter_idx=chapter_idx
    ).first()
    
    if existing:
        return {"message": "已标记过"}
    
    record = UserBookProgress(
        user_id=user_id,
        gutenberg_id=gutenberg_id,
        chapter_idx=chapter_idx,
    )
    db.add(record)
    db.commit()
    log.debug("user %s marked chapter %d of book %d as read", user_id, chapter_idx, gutenberg_id)
    return {"message": "标记成功"}

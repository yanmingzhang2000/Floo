"""名著书本路由 - Gutendex API 代理 + Gutenberg 全文解析。"""
import logging
import re
from typing import Optional
from urllib.parse import quote

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
# 中文名映射方便用户搜索
POPULAR_BOOKS = [
    {"id": 1342, "title": "Pride and Prejudice", "cn": "傲慢与偏见", "author": "Jane Austen"},
    {"id": 11, "title": "Alice's Adventures in Wonderland", "cn": "爱丽丝梦游仙境", "author": "Lewis Carroll"},
    {"id": 84, "title": "Frankenstein", "cn": "科学怪人", "author": "Mary Shelley"},
    {"id": 1661, "title": "The War of the Worlds", "cn": "世界大战", "author": "H.G. Wells"},
    {"id": 2701, "title": "Moby Dick", "cn": "白鲸记", "author": "Herman Melville"},
    {"id": 1952, "title": "The Yellow Wallpaper", "cn": "黄色墙纸", "author": "Charlotte Perkins Gilman"},
    {"id": 345, "title": "Dracula", "cn": "德古拉", "author": "Bram Stoker"},
    {"id": 120, "title": "Treasure Island", "cn": "金银岛", "author": "Robert Louis Stevenson"},
    {"id": 219, "title": "Heart of Darkness", "cn": "黑暗之心", "author": "Joseph Conrad"},
    {"id": 16328, "title": "Beowulf", "cn": "贝奥武夫", "author": "Anonymous"},
    {"id": 98, "title": "A Tale of Two Cities", "cn": "双城记", "author": "Charles Dickens"},
    {"id": 23, "title": "Narrative of Frederick Douglass", "cn": "一个美国黑奴的自传", "author": "Frederick Douglass"},
    {"id": 174, "title": "The Picture of Dorian Gray", "cn": "道林格雷的画像", "author": "Oscar Wilde"},
    {"id": 74, "title": "The Adventures of Tom Sawyer", "cn": "汤姆索亚历险记", "author": "Mark Twain"},
    {"id": 2600, "title": "War and Peace", "cn": "战争与和平", "author": "Leo Tolstoy"},
    {"id": 46, "title": "A Christmas Carol", "cn": "圣诞颂歌", "author": "Charles Dickens"},
    {"id": 161, "title": "The Great Gatsby", "cn": "了不起的盖茨比", "author": "F. Scott Fitzgerald"},
    {"id": 76, "title": "Little Women", "cn": "小妇人", "author": "Louisa May Alcott"},
    {"id": 35, "title": "Jane Eyre", "cn": "简爱", "author": "Charlotte Brontë"},
    {"id": 145, "title": "Wuthering Heights", "cn": "呼啸山庄", "author": "Emily Brontë"},
]

# 中文搜索关键词 → 英文搜索词映射
_CN_SEARCH_MAP = {
    "傲慢": "pride and prejudice", "偏见": "pride and prejudice",
    "爱丽丝": "alice in wonderland", "仙境": "alice in wonderland",
    "怪人": "frankenstein", "科学怪人": "frankenstein",
    "世界大战": "war of the worlds", "白鲸": "moby dick",
    "黄色墙纸": "yellow wallpaper", "德古拉": "dracula", "吸血鬼": "dracula",
    "金银岛": "treasure island", "黑暗之心": "heart of darkness",
    "贝奥武夫": "beowulf", "双城记": "tale of two cities",
    "道林格雷": "picture of dorian gray", "画像": "picture of dorian gray",
    "汤姆": "tom sawyer", "索亚": "tom sawyer",
    "战争与和平": "war and peace", "圣诞": "christmas carol",
    "盖茨比": "great gatsby", "了不起": "great gatsby",
    "小妇人": "little women", "简爱": "jane eyre",
    "呼啸山庄": "wuthering heights",
    "傲慢与偏见": "pride and prejudice",
    "爱丽丝梦游仙境": "alice in wonderland",
    "汤姆索亚": "tom sawyer",
    "一个美国黑奴": "frederick douglass",
    "道林格雷的画像": "picture of dorian gray",
    "了不起的盖茨比": "great gatsby",
}


@router.get("/popular")
async def get_popular_books(page: int = Query(1, ge=1)):
    """获取热门名著列表，带中文标签。"""
    ids_str = ",".join(str(b["id"]) for b in POPULAR_BOOKS)
    url = f"{GUTENDEX_BASE}/books?ids={ids_str}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            # 注入中文名
            cn_map = {b["id"]: b["cn"] for b in POPULAR_BOOKS}
            for result in data.get("results", []):
                if result["id"] in cn_map:
                    result["cn_title"] = cn_map[result["id"]]
            log.debug("Gutendex popular response: %d books", len(data.get("results", [])))
            return data
        except httpx.HTTPError as e:
            log.debug("Gutendex popular request failed: %s, falling back to local", e)
            # 兜底：返回本地热门书单
            return {
                "count": len(POPULAR_BOOKS),
                "results": [{
                    "id": b["id"],
                    "title": b["title"],
                    "cn_title": b["cn"],
                    "authors": [{"name": b["author"]}],
                    "formats": {},
                } for b in POPULAR_BOOKS]
            }


@router.get("/search")
async def search_books(query: str = Query(...), page: int = Query(1, ge=1)):
    """代理 Gutendex 搜索，支持中英文关键词。"""
    # 先查本地热门书单中文映射
    query_lower = query.lower().strip()
    local_match = None
    for book in POPULAR_BOOKS:
        if query_lower in book["cn"] or query_lower in book["title"].lower():
            local_match = book
            break

    # 如果本地热门有匹配，直接返回（带 Gutendex 元数据补全封面）
    if local_match:
        ids_str = str(local_match["id"])
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            try:
                resp = await client.get(f"{GUTENDEX_BASE}/books?ids={ids_str}")
                resp.raise_for_status()
                data = resp.json()
                if data.get("results"):
                    # 注入中文名
                    data["results"][0]["cn_title"] = local_match["cn"]
                    return data
            except httpx.HTTPError:
                pass
        # 兜底：返回本地信息
        return {"count": 1, "results": [{
            "id": local_match["id"],
            "title": local_match["title"],
            "cn_title": local_match["cn"],
            "authors": [{"name": local_match["author"]}],
            "formats": {},
        }]}

    # 中文关键词 → 英文搜索词
    en_query = _CN_SEARCH_MAP.get(query_lower, query)

    encoded_query = quote(en_query)
    url = f"{GUTENDEX_BASE}/books?search={encoded_query}&page={page}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            # 给结果注入中文名（如果本地有映射）
            for result in data.get("results", []):
                title_lower = result.get("title", "").lower()
                for book in POPULAR_BOOKS:
                    if title_lower == book["title"].lower():
                        result["cn_title"] = book["cn"]
                        break
            log.debug("Gutendex search '%s' -> '%s': %d results", query, en_query, data.get("count", 0))
            return data
        except httpx.HTTPError as e:
            log.debug("Gutendex search failed: %s", e)
            raise HTTPException(502, "书库搜索暂时不可用")


@router.get("/{gutenberg_id}")
async def get_book_detail(gutenberg_id: int):
    """获取单本书详情（元数据），带中文名。"""
    url = f"{GUTENDEX_BASE}/books/{gutenberg_id}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            # 注入中文名
            for book in POPULAR_BOOKS:
                if book["id"] == gutenberg_id:
                    data["cn_title"] = book["cn"]
                    break
            return data
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
        r'^(?:CHAPTER|Chapter)\s+([\dIVX]+)',  # Chapter I / CHAPTER 1 / Chapter II
        r'^(?:BOOK|Book)\s+([\dIVX]+)',         # Book I / Book 1
        r'^\s*([IVX]+)\.\s+',                    # "I. " 罗马数字开头
        r'^\s*PART\s+([\dIVX]+)',               # PART I / PART 1
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


# 缓存：{gutenberg_id: {"chapters": [...], "text": "full_text"}}
_book_cache: dict[int, dict] = {}


async def _resolve_txt_url(gutenberg_id: int) -> str | None:
    """从 Gutendex 获取书的 txt 下载链接。"""
    detail_url = f"{GUTENDEX_BASE}/books/{gutenberg_id}"
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(detail_url)
        resp.raise_for_status()
        book = resp.json()
        formats = book.get("formats", {})
        txt_url = formats.get("text/plain; charset=utf-8") or formats.get("text/plain")
    return txt_url


async def _download_full_text(txt_url: str) -> str:
    """下载 Gutenberg 全文并缓存。"""
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        resp = await client.get(txt_url)
        resp.raise_for_status()
        return resp.text


async def _ensure_book_cache(gutenberg_id: int):
    """确保书本全文和章节结构已缓存。"""
    if gutenberg_id in _book_cache:
        return _book_cache[gutenberg_id]

    txt_url = await _resolve_txt_url(gutenberg_id)
    if not txt_url:
        raise HTTPException(404, "无可用文本格式")

    full_text = await _download_full_text(txt_url)
    chapters = _parse_chapters(full_text)
    _book_cache[gutenberg_id] = {"chapters": chapters, "text": full_text}
    log.debug("Cached book %d: %d chapters, %d bytes", gutenberg_id, len(chapters), len(full_text))
    return _book_cache[gutenberg_id]


@router.get("/{gutenberg_id}/chapters")
async def get_chapters(gutenberg_id: int):
    """获取书本章节列表。"""
    cached = await _ensure_book_cache(gutenberg_id)
    return {"chapters": cached["chapters"]}


@router.get("/{gutenberg_id}/chapter/{chapter_idx}")
async def get_chapter_text(gutenberg_id: int, chapter_idx: int):
    """获取指定章节的完整文本（从缓存提取，不重复下载）。"""
    cached = await _ensure_book_cache(gutenberg_id)
    chapters = cached["chapters"]

    if not chapters:
        raise HTTPException(404, "章节数据为空")

    # -1 表示全文预览
    if chapter_idx == -1:
        title = chapters[0]["title"] if chapters else "全文"
        return {"title": title, "text": cached["text"][:5000]}

    if chapter_idx < 0 or chapter_idx >= len(chapters):
        raise HTTPException(400, "章节索引无效")

    ch = chapters[chapter_idx]
    lines = cached["text"].split('\n')
    chapter_text = '\n'.join(lines[ch["start"]:ch["end"]]).strip()
    return {"title": ch["title"], "text": chapter_text}


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
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
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

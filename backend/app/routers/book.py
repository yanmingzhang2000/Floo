"""
书籍精读接口 —— 用户端 + admin 端。

设计要点：
  - 用户端所有查询都强制授权校验（UserBookAccess 白名单），未授权 403
  - admin 端用 X-Admin-Token header 做简单闸门。这是内部工具接口，
    不需要完整 OAuth，但明文放开也不合适 → 环境变量注入 token
  - 章节详情接口按 mode=whole|segmented 返回 content_id(s)，前端拿去
    调 /api/daily/content/{id} 复用现有 detail 页
"""
from __future__ import annotations

import json
import logging
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.repositories import book_repo, content_repo
from app.services import book_importer, book_translator

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/book", tags=["book"])


# =========================================================================
# Schemas
# =========================================================================

class BookSeriesOut(BaseModel):
    series_id: int
    name: str
    name_cn: Optional[str] = None
    author: Optional[str] = None
    cover_url: Optional[str] = None
    description: Optional[str] = None
    total_chapters: int


class BookChapterOut(BaseModel):
    chapter_id: int
    order_no: int
    title: str
    content_id: int      # 整章模式使用
    word_count: int
    segment_count: int   # 分段模式下有几段


class BookSegmentOut(BaseModel):
    segment_id: int
    order_no: int
    content_id: int
    word_count: int
    # 该段在整章 content_text 中的字符起止位置（新字段，旧数据可能为 null）
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class ChapterDetailOut(BaseModel):
    """章节详情：按 mode 返回一个或多个 content_id 供前端跳详情页。"""
    chapter_id: int
    title: str
    mode: Literal["whole", "segmented"]
    # whole 模式：单条；segmented 模式：多条按顺序
    content_ids: list[int]


class GrantRequest(BaseModel):
    user_id: int
    series_id: int


class ImportRequest(BaseModel):
    source_url: str = Field(..., description="书籍目录页 URL，如 https://novel.tingroom.com/jingdian/96/")


class ImportResponse(BaseModel):
    series_id: int
    series_name: str
    total_chapters: int
    imported_chapters: int
    skipped_chapters: int
    total_segments: int
    failed_chapters: list[str]


# =========================================================================
# 授权工具
# =========================================================================

def require_admin(x_admin_token: str = Header(default="", alias="X-Admin-Token")) -> None:
    """校验 admin token。放在 Depends 里，路由自然拒绝。"""
    if not x_admin_token or x_admin_token != settings.FLOO_ADMIN_TOKEN:
        log.debug("require_admin 拒绝 提供的 token 长度=%s", len(x_admin_token or ""))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "admin token invalid")
    log.debug("require_admin 通过")


def _ensure_user_access(db: Session, user_id: int, series_id: int) -> None:
    """用户端接口的授权闸门 —— 无权限直接抛 403。"""
    if not book_repo.has_access(db, user_id, series_id):
        log.debug("_ensure_user_access 拒绝 user=%s series=%s", user_id, series_id)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "no access to this book")


# =========================================================================
# 用户端接口
# =========================================================================

@router.get("/mine")
def list_my_books(user_id: int, db: Session = Depends(get_db)) -> dict:
    """列出当前用户可访问的所有书籍。

    未授权用户返回空列表（不是 403），这样学习页可以透明地"没有书籍卡片就不显示"，
    避免每次首页都触发 403 报错干扰。
    """
    series_list = book_repo.list_accessible_series(db, user_id)
    books = [
        BookSeriesOut(
            series_id=s.series_id,  # type: ignore[arg-type]
            name=s.name,  # type: ignore[arg-type]
            name_cn=s.name_cn,  # type: ignore[arg-type]
            author=s.author,  # type: ignore[arg-type]
            cover_url=s.cover_url,  # type: ignore[arg-type]
            description=s.description,  # type: ignore[arg-type]
            total_chapters=s.total_chapters,  # type: ignore[arg-type]
        ).model_dump()
        for s in series_list
    ]
    log.debug("list_my_books user=%s count=%s", user_id, len(books))
    return {"books": books}


@router.get("/series/{series_id}/chapters")
def list_series_chapters(series_id: int, user_id: int, db: Session = Depends(get_db)) -> dict:
    """列出书籍下所有章节。未授权 403。"""
    _ensure_user_access(db, user_id, series_id)

    series = book_repo.get_series(db, series_id)
    if not series:
        log.debug("list_series_chapters series 不存在 series_id=%s", series_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "series not found")

    chapters = book_repo.list_chapters(db, series_id)
    # 一次性查每章的分段数量，避免 N+1
    seg_counts = _count_segments_per_chapter(db, [c.chapter_id for c in chapters])  # type: ignore[misc]

    items = [
        BookChapterOut(
            chapter_id=c.chapter_id,  # type: ignore[arg-type]
            order_no=c.order_no,  # type: ignore[arg-type]
            title=c.title,  # type: ignore[arg-type]
            content_id=c.content_id,  # type: ignore[arg-type]
            word_count=c.word_count,  # type: ignore[arg-type]
            segment_count=seg_counts.get(int(c.chapter_id), 0),  # type: ignore[arg-type]
        ).model_dump()
        for c in chapters
    ]
    return {
        "series_id": series_id,
        "series_name": series.name,
        "chapters": items,
    }


def _count_segments_per_chapter(db: Session, chapter_ids: list[int]) -> dict[int, int]:
    """聚合查每章分段数，一次 SQL 搞定。"""
    if not chapter_ids:
        return {}
    from sqlalchemy import func
    from app.models import BookChapterSegment
    rows = (
        db.query(BookChapterSegment.chapter_id, func.count(BookChapterSegment.segment_id))
        .filter(BookChapterSegment.chapter_id.in_(chapter_ids))
        .group_by(BookChapterSegment.chapter_id)
        .all()
    )
    return {int(cid): int(cnt) for cid, cnt in rows}


@router.get("/chapter/{chapter_id}")
def get_chapter_detail(
    chapter_id: int,
    user_id: int,
    mode: Literal["whole", "segmented"] = "whole",
    db: Session = Depends(get_db),
) -> ChapterDetailOut:
    """章节详情：按 mode 返回 content_id 列表。前端拿去调 /api/daily/content/{id}。"""
    chapter = book_repo.get_chapter(db, chapter_id)
    if not chapter:
        log.debug("get_chapter_detail chapter 不存在 chapter_id=%s", chapter_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chapter not found")

    _ensure_user_access(db, user_id, int(chapter.series_id))  # type: ignore[arg-type]

    if mode == "whole":
        log.debug("get_chapter_detail whole mode chapter=%s content=%s", chapter_id, chapter.content_id)
        return ChapterDetailOut(
            chapter_id=chapter_id,
            title=chapter.title,  # type: ignore[arg-type]
            mode="whole",
            content_ids=[int(chapter.content_id)],  # type: ignore[arg-type]
        )

    # segmented mode
    segments = book_repo.list_segments(db, chapter_id)
    if not segments:
        # 兜底：如果没有分段（旧数据），退化到整章
        log.debug("get_chapter_detail segmented 但无分段，退化到 whole chapter=%s", chapter_id)
        return ChapterDetailOut(
            chapter_id=chapter_id,
            title=chapter.title,  # type: ignore[arg-type]
            mode="whole",
            content_ids=[int(chapter.content_id)],  # type: ignore[arg-type]
        )

    return ChapterDetailOut(
        chapter_id=chapter_id,
        title=chapter.title,  # type: ignore[arg-type]
        mode="segmented",
        content_ids=[int(s.content_id) for s in segments],  # type: ignore[arg-type]
    )


@router.get("/chapter/{chapter_id}/segments")
def list_chapter_segments(chapter_id: int, user_id: int, db: Session = Depends(get_db)) -> dict:
    """列出章节的所有分段（供 detail 页在整章上画分割线）。"""
    chapter = book_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chapter not found")
    _ensure_user_access(db, user_id, int(chapter.series_id))  # type: ignore[arg-type]

    segments = book_repo.list_segments(db, chapter_id)
    items = [
        BookSegmentOut(
            segment_id=s.segment_id,  # type: ignore[arg-type]
            order_no=s.order_no,  # type: ignore[arg-type]
            content_id=s.content_id,  # type: ignore[arg-type]
            word_count=s.word_count,  # type: ignore[arg-type]
            start_char=s.start_char,  # type: ignore[arg-type]
            end_char=s.end_char,  # type: ignore[arg-type]
        ).model_dump()
        for s in segments
    ]
    return {
        "chapter_id": chapter_id,
        "title": chapter.title,
        "segments": items,
    }


# =========================================================================
# 用户端：按需译文 + 段默写准备 + content 反查
# =========================================================================

@router.get("/content/{content_id}/context")
def get_content_context(content_id: int, user_id: int, db: Session = Depends(get_db)) -> dict:
    """detail 页反查：给一个 content_id，判断它是不是某书籍整章。

    Why 单独接口而不是把字段塞进 /api/daily/content：
      - daily/content 服务所有内容，不该背负书籍逻辑
      - 前端可以并行请求，不影响主 content 加载

    返回：
      - is_book_chapter=false：普通 daily 内容，前端不做特殊处理
      - is_book_chapter=true：附带 chapter_id + 该章 segments 列表（含 offset）
    """
    chapter = book_repo.find_chapter_by_content_id(db, content_id)
    if not chapter:
        log.debug("get_content_context content=%s 非书籍章节", content_id)
        return {"is_book_chapter": False}

    _ensure_user_access(db, user_id, int(chapter.series_id))  # type: ignore[arg-type]

    segments = book_repo.list_segments(db, int(chapter.chapter_id))  # type: ignore[arg-type]
    series = book_repo.get_series(db, int(chapter.series_id))  # type: ignore[arg-type]

    return {
        "is_book_chapter": True,
        "chapter_id": chapter.chapter_id,
        "series_id": chapter.series_id,
        "series_name": series.name if series else None,
        "chapter_title": chapter.title,
        "segments": [
            BookSegmentOut(
                segment_id=s.segment_id,  # type: ignore[arg-type]
                order_no=s.order_no,  # type: ignore[arg-type]
                content_id=s.content_id,  # type: ignore[arg-type]
                word_count=s.word_count,  # type: ignore[arg-type]
                start_char=s.start_char,  # type: ignore[arg-type]
                end_char=s.end_char,  # type: ignore[arg-type]
            ).model_dump()
            for s in segments
        ],
    }


@router.post("/chapter/{chapter_id}/translation")
async def get_chapter_translation(
    chapter_id: int,
    user_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """按需拉整章译文。首次调用触发 LLM 翻译（5-10s），之后缓存命中秒开。"""
    chapter = book_repo.get_chapter(db, chapter_id)
    if not chapter:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chapter not found")
    _ensure_user_access(db, user_id, int(chapter.series_id))  # type: ignore[arg-type]

    translation = await book_translator.ensure_chapter_translation(db, chapter_id)
    if not translation:
        log.debug("get_chapter_translation LLM 失败 chapter=%s", chapter_id)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "translation service unavailable, please retry")
    return {"chapter_id": chapter_id, "translation": translation}


@router.post("/segment/{segment_id}/translation")
async def get_segment_translation(
    segment_id: int,
    user_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """按需拉单段译文（阅读态）。

    首次调用触发 LLM 翻译该段（5-8s），之后缓存命中秒开。
    与整章译文互相独立缓存 —— 段级译文更细粒度，用户翻页时逐段拉。
    """
    segment = book_repo.get_segment(db, segment_id)
    if not segment:
        log.debug("get_segment_translation 段不存在 segment_id=%s", segment_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "segment not found")

    chapter = book_repo.get_chapter(db, int(segment.chapter_id))  # type: ignore[arg-type]
    if not chapter:
        log.debug("get_segment_translation 章节不存在 segment_id=%s", segment_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chapter not found")
    _ensure_user_access(db, user_id, int(chapter.series_id))  # type: ignore[arg-type]

    translation = await book_translator.ensure_segment_translation(db, segment_id)
    if not translation:
        log.debug("get_segment_translation LLM 失败 segment_id=%s", segment_id)
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "translation service unavailable, please retry",
        )
    return {
        "segment_id": segment_id,
        "content_id": int(segment.content_id),  # type: ignore[arg-type]
        "translation": translation,
    }


@router.post("/segment/{segment_id}/prepare-dictation")
async def prepare_segment_dictation(
    segment_id: int,
    user_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """按需给指定段准备默写素材：确保 translation + 词汇齐全。

    首次触发 LLM 生成，之后缓存命中。返回该段对应的 content_id，
    前端直接跳 /pages/dictation/index?id={content_id} 走现有默写流程。
    """
    segment = book_repo.get_segment(db, segment_id)
    if not segment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "segment not found")

    chapter = book_repo.get_chapter(db, int(segment.chapter_id))  # type: ignore[arg-type]
    if not chapter:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "chapter not found")
    _ensure_user_access(db, user_id, int(chapter.series_id))  # type: ignore[arg-type]

    seg_content = await book_translator.ensure_segment_dictation_ready(db, segment_id)
    if not seg_content:
        log.debug("prepare_segment_dictation LLM 失败 segment=%s", segment_id)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "translation service unavailable, please retry")

    return {
        "segment_id": segment_id,
        "content_id": seg_content.content_id,
        "ready": True,
    }


# =========================================================================
# Admin 接口
# =========================================================================

@router.post("/admin/import", dependencies=[Depends(require_admin)], response_model=ImportResponse)
def admin_import_book(payload: ImportRequest, db: Session = Depends(get_db)) -> ImportResponse:
    """触发抓取 + 落库。幂等：同一 source_url 再次调用只会补齐缺失章节。

    Why 同步返回：一本书 ~20 章、每章 sleep 0.5s，总耗时 20-40s，能扛住 HTTP 超时；
    未来大部头再改成后台任务。
    """
    log.debug("admin_import_book 开始 source_url=%s", payload.source_url)
    try:
        summary = book_importer.import_book(db, payload.source_url)
    except ValueError as e:
        log.debug("admin_import_book 参数错误 err=%s", e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        log.warning("admin_import_book 抓取失败 err=%s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"import failed: {e}")

    return ImportResponse(
        series_id=summary.series_id,
        series_name=summary.series_name,
        total_chapters=summary.total_chapters,
        imported_chapters=summary.imported_chapters,
        skipped_chapters=summary.skipped_chapters,
        total_segments=summary.total_segments,
        failed_chapters=summary.failed_chapters,
    )


class ResegmentRequest(BaseModel):
    series_id: int
    target_words: int = 125


@router.post("/admin/resegment", dependencies=[Depends(require_admin)])
def admin_resegment(payload: ResegmentRequest, db: Session = Depends(get_db)) -> dict:
    """对已导入的书籍按新参数重新切分。

    危险动作：删除该 series 下所有旧 segment + 对应的 learning_content 行。
    整章 content_text 不重抓、不重生成整章 learning_content。
    """
    log.debug("admin_resegment 开始 series=%s target=%s", payload.series_id, payload.target_words)
    try:
        summary = book_importer.resegment_series(db, payload.series_id, payload.target_words)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception as e:
        log.warning("admin_resegment 失败 err=%s", e)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"resegment failed: {e}")

    return {"series_id": payload.series_id, **summary}


@router.post("/admin/grant", dependencies=[Depends(require_admin)])
def admin_grant_access(payload: GrantRequest, db: Session = Depends(get_db)) -> dict:
    """给用户授权访问指定书籍。"""
    series = book_repo.get_series(db, payload.series_id)
    if not series:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "series not found")

    row = book_repo.grant_access(db, payload.user_id, payload.series_id, granted_by="admin")
    log.debug("admin_grant_access user=%s series=%s", payload.user_id, payload.series_id)
    return {
        "user_id": row.user_id,
        "series_id": row.series_id,
        "is_active": row.is_active,
        "granted_at": row.granted_at,
    }


@router.delete("/admin/grant/{user_id}/{series_id}", dependencies=[Depends(require_admin)])
def admin_revoke_access(user_id: int, series_id: int, db: Session = Depends(get_db)) -> dict:
    """撤销授权（软删除）。"""
    ok = book_repo.revoke_access(db, user_id, series_id)
    if not ok:
        log.debug("admin_revoke_access 无有效授权 user=%s series=%s", user_id, series_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no active access to revoke")
    return {"revoked": True, "user_id": user_id, "series_id": series_id}


@router.get("/admin/lookup-user", dependencies=[Depends(require_admin)])
def admin_lookup_user(username: str, db: Session = Depends(get_db)) -> dict:
    """按用户名查 user_id，方便 admin 授权前定位账号。"""
    from app.models import UserMain
    user = db.query(UserMain).filter(UserMain.username == username).first()
    if not user:
        log.debug("admin_lookup_user 未找到 username=%s", username)
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"user '{username}' not found")
    log.debug("admin_lookup_user 命中 username=%s user_id=%s", username, user.user_id)
    return {
        "user_id": user.user_id,
        "username": user.username,
        "nickname": user.nickname,
    }


@router.patch("/admin/series/{series_id}/public", dependencies=[Depends(require_admin)])
def admin_set_series_public(
    series_id: int,
    is_public: bool,
    db: Session = Depends(get_db),
) -> dict:
    """设置书籍是否公开（对所有登录用户可见，无需白名单授权）。

    为什么用 query param 而不是 body：单一布尔值用 query 更简洁，
    curl 一行搞定，不需要 -d JSON。
    """
    series = book_repo.get_series(db, series_id)
    if not series:
        log.debug("admin_set_series_public series 不存在 series_id=%s", series_id)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "series not found")
    series.is_public = is_public  # type: ignore[assignment]
    db.commit()
    log.debug("admin_set_series_public series=%s is_public=%s", series_id, is_public)
    return {"series_id": series_id, "is_public": is_public}


@router.get("/admin/series", dependencies=[Depends(require_admin)])
def admin_list_all_series(db: Session = Depends(get_db)) -> dict:
    """列出所有已导入的书籍（供 admin 查看/授权时挑）。"""
    from app.models import BookSeries
    series_list = db.query(BookSeries).order_by(BookSeries.created_at.desc()).all()
    return {
        "books": [
            {
                "series_id": s.series_id,
                "name": s.name,
                "name_cn": s.name_cn,
                "total_chapters": s.total_chapters,
                "source_url": s.source_url,
                "created_at": s.created_at,
            }
            for s in series_list
        ]
    }

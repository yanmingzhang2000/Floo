"""
书籍数据访问层。

为什么把授权（UserBookAccess）也放这里而不是单独 user_repo：
   授权是"书籍可见性"的一部分语义，和列表查询紧耦合，放一起调用链短。
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models import (
    BookChapter,
    BookChapterSegment,
    BookSeries,
    UserBookAccess,
)

log = logging.getLogger(__name__)


# =========================================================================
# 授权
# =========================================================================

def has_access(db: Session, user_id: int, series_id: int) -> bool:
    """判断用户是否有权访问指定书籍。

    只需一次 index 查询（idx_book_access_user），O(1)。
    """
    row = (
        db.query(UserBookAccess)
        .filter(
            UserBookAccess.user_id == user_id,
            UserBookAccess.series_id == series_id,
            UserBookAccess.is_active == True,
        )
        .first()
    )
    if row:
        log.debug("has_access 命中 user=%s series=%s", user_id, series_id)
        return True
    log.debug("has_access 无权限 user=%s series=%s", user_id, series_id)
    return False


def grant_access(db: Session, user_id: int, series_id: int, granted_by: str = "admin") -> UserBookAccess:
    """给用户授权访问书籍。幂等：已存在则复活并更新 granted_by。"""
    existing = (
        db.query(UserBookAccess)
        .filter(UserBookAccess.user_id == user_id, UserBookAccess.series_id == series_id)
        .first()
    )
    if existing:
        # 之前撤销过的复活；顺便更新 granted_by 便于审计
        if not existing.is_active:  # type: ignore[truthy-function]
            log.debug("grant_access 复活已撤销授权 user=%s series=%s", user_id, series_id)
            existing.is_active = True  # type: ignore[assignment]
        existing.granted_by = granted_by  # type: ignore[assignment]
        db.commit()
        return existing

    row = UserBookAccess(
        user_id=user_id,
        series_id=series_id,
        granted_by=granted_by,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log.debug("grant_access 新增授权 user=%s series=%s", user_id, series_id)
    return row


def revoke_access(db: Session, user_id: int, series_id: int) -> bool:
    """撤销授权（软删除保留审计记录）。返回是否有实际撤销动作。"""
    row = (
        db.query(UserBookAccess)
        .filter(
            UserBookAccess.user_id == user_id,
            UserBookAccess.series_id == series_id,
            UserBookAccess.is_active == True,
        )
        .first()
    )
    if not row:
        log.debug("revoke_access 无有效授权可撤销 user=%s series=%s", user_id, series_id)
        return False
    row.is_active = False  # type: ignore[assignment]
    db.commit()
    log.debug("revoke_access 撤销 user=%s series=%s", user_id, series_id)
    return True


# =========================================================================
# 查询
# =========================================================================

def list_accessible_series(db: Session, user_id: int) -> list[BookSeries]:
    """列出用户可访问的所有书籍，按授权时间倒序。"""
    rows = (
        db.query(BookSeries, UserBookAccess.granted_at)
        .join(UserBookAccess, UserBookAccess.series_id == BookSeries.series_id)
        .filter(
            UserBookAccess.user_id == user_id,
            UserBookAccess.is_active == True,
            BookSeries.is_active == True,
        )
        .order_by(UserBookAccess.granted_at.desc())
        .all()
    )
    series_list = [row[0] for row in rows]
    log.debug("list_accessible_series user=%s count=%s", user_id, len(series_list))
    return series_list


def get_series(db: Session, series_id: int) -> Optional[BookSeries]:
    """按 ID 查书籍。"""
    series = db.query(BookSeries).filter(BookSeries.series_id == series_id).first()
    if not series:
        log.debug("get_series 不存在 series_id=%s", series_id)
    return series


def list_chapters(db: Session, series_id: int) -> list[BookChapter]:
    """按 order_no 升序列出章节。"""
    chapters = (
        db.query(BookChapter)
        .filter(BookChapter.series_id == series_id)
        .order_by(BookChapter.order_no.asc())
        .all()
    )
    log.debug("list_chapters series=%s count=%s", series_id, len(chapters))
    return chapters


def get_chapter(db: Session, chapter_id: int) -> Optional[BookChapter]:
    """按 ID 查章节。"""
    return db.query(BookChapter).filter(BookChapter.chapter_id == chapter_id).first()


def list_segments(db: Session, chapter_id: int) -> list[BookChapterSegment]:
    """按 order_no 升序列出章节分段。"""
    segments = (
        db.query(BookChapterSegment)
        .filter(BookChapterSegment.chapter_id == chapter_id)
        .order_by(BookChapterSegment.order_no.asc())
        .all()
    )
    log.debug("list_segments chapter=%s count=%s", chapter_id, len(segments))
    return segments


def get_segment(db: Session, segment_id: int) -> Optional[BookChapterSegment]:
    """按 ID 查段。"""
    return (
        db.query(BookChapterSegment)
        .filter(BookChapterSegment.segment_id == segment_id)
        .first()
    )


def find_chapter_by_content_id(db: Session, content_id: int) -> Optional[BookChapter]:
    """反查：给一个 learning_content 的 content_id，如果它是某章的整章内容，返回该章。

    detail 页需要判断"当前打开的 content 是不是书籍章节"，从而决定是否走
    段落分割 + 按需译文的书籍专属交互路径。
    """
    return (
        db.query(BookChapter)
        .filter(BookChapter.content_id == content_id)
        .first()
    )

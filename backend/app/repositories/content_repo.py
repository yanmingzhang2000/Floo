"""
学习内容数据访问层。

为什么把 AI 生成和用户自定义内容放同一张表同一个 repo：
learning_contents 是所有学习行为的唯一锚点，统一查询入口比分表更简单。
creator_type 字段区分来源，上层按需过滤即可。
"""
import json
import logging
from datetime import date
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import LearningContent, UserMemoryProgress

log = logging.getLogger(__name__)


def get_content_by_id(db: Session, content_id: int) -> Optional[LearningContent]:
    """按 ID 查内容。"""
    content = db.query(LearningContent).filter(
        LearningContent.content_id == content_id,
        LearningContent.is_active == True,
    ).first()
    if not content:
        log.debug("content_id=%s 不存在或已禁用", content_id)
    return content


def get_today_ai_contents(db: Session) -> list[LearningContent]:
    """
    获取今天已生成的所有 AI 内容列表。

    用于幂等检查：今天已有内容时跳过生成，避免重复调用 LLM API。
    按 created_at 升序返回，保持与生成顺序一致。
    """
    from datetime import datetime
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    contents = (
        db.query(LearningContent)
        .filter(
            LearningContent.creator_type == 0,
            LearningContent.is_active == True,
            LearningContent.created_at >= today_start,
            LearningContent.created_at <= today_end,
        )
        .order_by(LearningContent.created_at.asc())
        .all()
    )
    log.debug("今日已有 AI 内容 count=%s", len(contents))
    return contents


def get_today_ai_contents_by_theme(db: Session, theme: str) -> list[LearningContent]:
    """
    获取今天指定 theme 已生成的 AI 内容。

    同一 theme 的用户共享同一批内容，所以按 theme + 日期做幂等检查。
    避免相同 theme 被重复生成浪费 LLM 调用。
    """
    from datetime import datetime
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    contents = (
        db.query(LearningContent)
        .filter(
            LearningContent.creator_type == 0,
            LearningContent.is_active == True,
            LearningContent.theme_type == theme,
            LearningContent.created_at >= today_start,
            LearningContent.created_at <= today_end,
        )
        .order_by(LearningContent.created_at.asc())
        .all()
    )
    log.debug("今日 theme=%s 已有内容 count=%s", theme, len(contents))
    return contents


def get_latest_ai_content_by_theme(db: Session, theme: str) -> Optional[LearningContent]:
    """
    获取指定 theme 最新一条 AI 内容。
    供 /today 接口按用户偏好返回单条预览。
    """
    content = (
        db.query(LearningContent)
        .filter(
            LearningContent.creator_type == 0,
            LearningContent.is_active == True,
            LearningContent.theme_type == theme,
        )
        .order_by(LearningContent.created_at.desc())
        .first()
    )
    if content:
        log.debug("找到 theme=%s 最新内容 content_id=%s", theme, content.content_id)
    else:
        log.debug("theme=%s 无内容", theme)
    return content


def get_today_content_list_by_theme(db: Session, theme: str) -> list[LearningContent]:
    """
    获取今日指定 theme 的完整内容列表，按生成顺序排列。
    供前端根据用户学习时长决定展示几篇。
    """
    from datetime import datetime
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    contents = (
        db.query(LearningContent)
        .filter(
            LearningContent.creator_type == 0,
            LearningContent.is_active == True,
            LearningContent.theme_type == theme,
            LearningContent.created_at >= today_start,
            LearningContent.created_at <= today_end,
        )
        .order_by(LearningContent.content_id.asc())
        .all()
    )
    log.debug("theme=%s 今日内容列表 count=%s", theme, len(contents))
    return contents


def get_latest_ai_content(db: Session) -> Optional[LearningContent]:
    """
    获取最新一条 AI 生成内容。

    为什么不按 date 精确匹配：AI 内容可能不是每天都生成，
    取最近一条保证用户始终有内容可学。
    """
    content = (
        db.query(LearningContent)
        .filter(
            LearningContent.creator_type == 0,
            LearningContent.is_active == True,
        )
        .order_by(LearningContent.created_at.desc())
        .first()
    )
    if content:
        log.debug("找到最新AI内容 content_id=%s", content.content_id)
    else:
        log.debug("无 AI 生成内容")
    return content


def list_ai_contents(db: Session, limit: int = 20) -> list[LearningContent]:
    """获取 AI 生成内容列表，按时间倒序。"""
    return (
        db.query(LearningContent)
        .filter(
            LearningContent.creator_type == 0,
            LearningContent.is_active == True,
        )
        .order_by(LearningContent.created_at.desc())
        .limit(limit)
        .all()
    )


def list_user_contents(db: Session, user_id: int) -> list[LearningContent]:
    """获取用户自定义内容列表。"""
    return (
        db.query(LearningContent)
        .filter(
            LearningContent.creator_type == 1,
            LearningContent.user_id == user_id,
            LearningContent.is_active == True,
        )
        .order_by(LearningContent.created_at.desc())
        .all()
    )


def create_ai_content(db: Session, data: dict[str, Any]) -> LearningContent:
    """
    写入 AI 生成的学习内容。

    words 列表序列化为 JSON 字符串存入 key_words 字段，
    查询时由上层 service 负责反序列化。
    """
    words = data.get("words", [])
    content = LearningContent(
        creator_type=0,
        user_id=None,
        difficulty_level=data.get("difficulty_level", "medium"),
        theme_type=data.get("theme_type", "daily_news"),
        title=data.get("title", "Daily English"),
        content_text=data.get("article", ""),
        translation=data.get("translation"),
        key_words=json.dumps(words, ensure_ascii=False),
        audio_url=data.get("audio_url"),
        content_type=data.get("content_type", "article"),
    )
    db.add(content)
    db.flush()
    log.debug("AI 内容已写入 content_id=%s title=%s", content.content_id, content.title)
    return content


def create_user_content(
    db: Session,
    user_id: int,
    title: str,
    content_text: str,
    difficulty_level: str,
    theme_type: str,
    translation: Optional[str] = None,
    key_words: Optional[list] = None,
) -> LearningContent:
    """写入用户自定义学习内容。"""
    content = LearningContent(
        creator_type=1,
        user_id=user_id,
        difficulty_level=difficulty_level,
        theme_type=theme_type,
        title=title,
        content_text=content_text,
        translation=translation,
        key_words=json.dumps(key_words or [], ensure_ascii=False),
    )
    db.add(content)
    db.flush()
    log.debug("用户自定义内容已写入 content_id=%s user_id=%s", content.content_id, user_id)
    return content


def init_memory_progress(db: Session, user_id: int, content_id: int) -> UserMemoryProgress:
    """
    为用户初始化一条记忆进度记录。

    为什么放在 content_repo 而不是单独的 memory_repo：
    内容创建和记忆进度初始化总是同时发生，放一起调用链更短。
    """
    from datetime import datetime
    # 检查是否已存在，避免重复初始化
    existing = db.query(UserMemoryProgress).filter(
        UserMemoryProgress.user_id == user_id,
        UserMemoryProgress.content_id == content_id,
    ).first()
    if existing:
        log.debug("记忆进度已存在 user_id=%s content_id=%s，跳过", user_id, content_id)
        return existing

    progress = UserMemoryProgress(
        user_id=user_id,
        content_id=content_id,
        review_stage=0,
        next_review_at=datetime.utcnow(),
        total_review_count=0,
        last_accuracy=0.00,
    )
    db.add(progress)
    db.flush()
    log.debug("记忆进度已初始化 user_id=%s content_id=%s", user_id, content_id)
    return progress


def parse_words(content: LearningContent) -> list[dict]:
    """
    将 key_words JSON 字符串解析为列表。

    为什么在 repo 层解析：调用方不应该关心存储格式是 JSON 字符串还是独立表，
    这是数据访问层的实现细节。
    """
    if not content.key_words:
        return []
    try:
        return json.loads(content.key_words)
    except (json.JSONDecodeError, TypeError) as e:
        log.debug("key_words 解析失败 content_id=%s err=%s，返回空列表", content.content_id, e)
        return []


def get_learned_contents_by_date_range(
    db: Session,
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[LearningContent], int]:
    """
    按内容创建时间区间查询用户已学内容。

    为什么按 created_at 而不是 learned_at：用户需求是筛选"某段时间导入的内容"，
    created_at 代表内容创建/导入时间，learned_at 代表学习时间，两者语义不同。
    """
    from datetime import datetime
    from app.models import UserLearnedContent

    # 构建基础查询：关联已学内容表和内容表
    query = (
        db.query(LearningContent)
        .join(
            UserLearnedContent,
            UserLearnedContent.content_id == LearningContent.content_id,
        )
        .filter(
            UserLearnedContent.user_id == user_id,
            LearningContent.is_active == True,
        )
    )

    # 按创建时间区间过滤
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            query = query.filter(LearningContent.created_at >= start_dt)
            log.debug("筛选开始日期 start_date=%s", start_date)
        except ValueError:
            log.debug("start_date 格式无效 start_date=%s", start_date)

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            query = query.filter(LearningContent.created_at <= end_dt)
            log.debug("筛选结束日期 end_date=%s", end_date)
        except ValueError:
            log.debug("end_date 格式无效 end_date=%s", end_date)

    # 获取总数（用于分页）
    total = query.count()

    # 按创建时间倒序排列，应用分页
    contents = (
        query.order_by(LearningContent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    log.debug(
        "查询已学内容 user_id=%s start_date=%s end_date=%s total=%s returned=%s",
        user_id, start_date, end_date, total, len(contents),
    )
    return contents, total
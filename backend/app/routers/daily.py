"""
接口 1：学习内容生成与查询。

为什么生成时读取用户偏好：Floo! 的核心设计是个性化推送，
difficulty_level 和 theme_type 必须作为 LLM Prompt 参数，
不读偏好就失去了个性化的意义。
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import content_repo, user_repo
from app.schemas import (
    GenerateContentRequest,
    GenerateContentResult,
    LearningContentOut,
)
from app.services.news_generator import generate_daily_news

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/daily", tags=["daily"])


def _content_to_out(content, words: list) -> LearningContentOut:
    """将 ORM 对象转为输出 schema，统一处理字段映射。"""
    return LearningContentOut(
        id=content.content_id,
        content_date=content.created_at.strftime("%Y-%m-%d"),
        title=content.title,
        article=content.content_text,
        translation=content.translation,
        audio_url=content.audio_url,
        difficulty_level=content.difficulty_level,
        theme_type=content.theme_type,
        words=words,
    )


@router.post("/generate", response_model=GenerateContentResult)
async def generate_daily(
    payload: GenerateContentRequest,
    db: Session = Depends(get_db),
):
    """AI 生成个性化学习内容，读取用户偏好决定难度和主题。"""
    log.debug("收到生成请求 user_id=%s topic_hint=%s", payload.user_id, payload.topic_hint)

    # 读取用户偏好作为 LLM Prompt 参数
    user = user_repo.get_user(db, payload.user_id)
    difficulty = payload.difficulty_override or "medium"
    theme = payload.theme_override or "daily_life"
    if user and user.preference:
        difficulty = payload.difficulty_override or user.preference.difficulty_level
        theme = payload.theme_override or user.preference.theme_type
        log.debug("使用用户偏好 difficulty=%s theme=%s", difficulty, theme)
    else:
        log.debug("用户无偏好记录，使用默认值 difficulty=%s theme=%s", difficulty, theme)

    data = await generate_daily_news(
        topic_hint=payload.topic_hint,
        difficulty=difficulty,
        theme=theme,
    )
    if not data.get("article"):
        log.debug("AI 返回 article 为空，返回 500")
        raise HTTPException(500, "AI 生成失败，请稍后重试")

    content = content_repo.create_ai_content(db, data)

    # 如果有用户 ID，同步初始化记忆进度
    if user:
        content_repo.init_memory_progress(db, user.user_id, content.content_id)
        log.debug("记忆进度已初始化 user_id=%s content_id=%s", user.user_id, content.content_id)

    db.commit()
    log.debug("生成完成 content_id=%s", content.content_id)
    return GenerateContentResult(content_id=content.content_id, message="生成成功")


@router.get("/today", response_model=LearningContentOut)
def get_today(db: Session = Depends(get_db)):
    """获取最新一条 AI 学习内容。"""
    content = content_repo.get_latest_ai_content(db)
    if not content:
        log.debug("无内容，提示前端先调用 generate")
        raise HTTPException(404, "暂无学习内容，请先点击生成")
    words = content_repo.parse_words(content)
    return _content_to_out(content, words)


@router.get("/list", response_model=list[LearningContentOut])
def list_contents(limit: int = 20, db: Session = Depends(get_db)):
    """获取 AI 生成内容列表。"""
    contents = content_repo.list_ai_contents(db, limit=limit)
    log.debug("返回内容列表 count=%s", len(contents))
    return [_content_to_out(c, content_repo.parse_words(c)) for c in contents]


@router.get("/content/{content_id}", response_model=LearningContentOut)
def get_content(content_id: int, db: Session = Depends(get_db)):
    """按 ID 获取学习内容。"""
    content = content_repo.get_content_by_id(db, content_id)
    if not content:
        log.debug("content_id=%s 不存在", content_id)
        raise HTTPException(404, "内容不存在")
    words = content_repo.parse_words(content)
    return _content_to_out(content, words)
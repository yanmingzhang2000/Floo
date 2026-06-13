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
    CustomContentRequest,
    CustomContentResponse,
    GenerateContentRequest,
    GenerateContentResult,
    LearningContentOut,
    MemoryProgressListResponse,
    MemoryProgressOut,
    ReviewListResponse,
    ReviewTaskOut,
    TodayContentListResponse,
)
from app.services.news_generator import generate_daily_news_batch

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
    """
    AI 批量生成今日学习内容（3 篇新闻）。

    按用户偏好的 theme 生成内容，同 theme 当日共享。
    all_random 主题每天随机挑选真实 theme 生成。
    幂等设计：同 theme 今日已有 >= 3 条内容时直接返回，不重复调用 LLM。
    限制：每人每天最多生成3次。
    """
    from datetime import date, timedelta
    from app.schemas import THEME_OPTIONS
    from app.models import DailyGenerationLimit
    import random

    force = payload.model_dump().get('force', False)
    log.debug("收到生成请求 user_id=%s force=%s", payload.user_id, force)

    # 检查每日生成次数限制（每天最多3次）
    today = date.today()
    limit_record = (
        db.query(DailyGenerationLimit)
        .filter(
            DailyGenerationLimit.user_id == payload.user_id,
            DailyGenerationLimit.limit_date == today
        )
        .first()
    )
    
    if limit_record and limit_record.generation_count >= 3 and not force:
        log.debug("用户 %s 今日已生成 %s 次，达到上限", payload.user_id, limit_record.generation_count)
        raise HTTPException(429, "今日生成次数已达上限（每天最多3次），请明天再来")
    
    log.debug("用户 %s 今日已生成 %s 次，继续执行", payload.user_id, limit_record.generation_count if limit_record else 0)

    # 读取用户偏好 theme
    user = user_repo.get_user(db, payload.user_id)
    theme = payload.theme_override or "daily_news"
    if user and user.preference:
        theme = payload.theme_override or user.preference.theme_type
        log.debug("使用用户偏好 theme=%s", theme)
    else:
        log.debug("用户无偏好记录，使用默认 theme=%s", theme)

    # all_random 主题：随机选一个真实 theme
    actual_theme = theme
    if theme == "all_random":
        actual_theme = random.choice([t for t in THEME_OPTIONS if t != "all_random"])
        log.info("all_random 模式，今日随机选择 theme=%s", actual_theme)

    # 幂等检查：同 theme 今日已有内容（1 总览 + 3 文章 = 4 条）且未强制重新生成则直接返回
    if not force:
        existing = content_repo.get_today_ai_contents_by_theme(db, actual_theme)
        if len(existing) >= 4:
            ids = [c.content_id for c in existing[:3]]
            log.info("theme=%s 今日内容已存在，跳过生成 content_ids=%s", actual_theme, ids)
            return GenerateContentResult(
                content_id=ids[0],
                content_ids=ids,
                count=len(ids),
                message=f"今日 {actual_theme} 内容已生成",
            )

    batch = await generate_daily_news_batch(theme=actual_theme)
    if not batch or not batch[0].get("article"):
        log.warning("AI 返回批量内容为空 theme=%s", actual_theme)
        raise HTTPException(500, "AI 生成失败，请稍后重试")

    content_ids: list[int] = []
    for data in batch:
        content = content_repo.create_ai_content(db, data)
        content_ids.append(content.content_id)
        # 如果有用户 ID，同步初始化记忆进度
        if user:
            content_repo.init_memory_progress(db, user.user_id, content.content_id)
            log.debug("记忆进度已初始化 user_id=%s content_id=%s", user.user_id, content.content_id)

    db.commit()
    
    # 更新每日生成次数限制
    if limit_record:
        limit_record.generation_count += 1
        log.debug("更新生成次数 user_id=%s count=%s", payload.user_id, limit_record.generation_count)
    else:
        new_limit = DailyGenerationLimit(
            user_id=payload.user_id,
            limit_date=today,
            generation_count=1
        )
        db.add(new_limit)
        log.debug("创建生成次数记录 user_id=%s date=%s", payload.user_id, today)
    db.commit()
    
    log.info("批量生成完成 theme=%s content_ids=%s", actual_theme, content_ids)
    return GenerateContentResult(
        content_id=content_ids[0],
        content_ids=content_ids,
        count=len(content_ids),
        message=f"成功生成 {len(content_ids)} 篇学习内容",
    )


@router.get("/today", response_model=LearningContentOut)
def get_today(user_id: int = 1, db: Session = Depends(get_db)):
    """
    获取今日学习内容（按用户偏好的 theme 返回）。

    同 theme 用户看到相同内容；all_random 用户看当天随机 theme 的内容。
    """
    from app.schemas import THEME_OPTIONS
    import random

    # 读取用户偏好 theme
    user = user_repo.get_user(db, user_id)
    theme = "daily_news"
    if user and user.preference:
        theme = user.preference.theme_type

    # all_random 用户：从今天已有的所有 theme 中随机返回一条
    if theme == "all_random":
        all_today = content_repo.get_today_ai_contents(db)
        if all_today:
            content = random.choice(all_today)
            log.debug("all_random 用户，随机返回 content_id=%s theme=%s", content.content_id, content.theme_type)
            words = content_repo.parse_words(content)
            return _content_to_out(content, words)
        # 无内容时随机选一个 theme
        theme = random.choice([t for t in THEME_OPTIONS if t != "all_random"])
        log.debug("all_random 用户且今日无内容，降级到 theme=%s", theme)

    # 按 theme 查询最新内容
    content = content_repo.get_latest_ai_content_by_theme(db, theme)
    if not content:
        log.debug("theme=%s 无内容，提示前端先调用 generate", theme)
        raise HTTPException(404, f"暂无 {theme} 内容，请先点击生成")
    words = content_repo.parse_words(content)
    return _content_to_out(content, words)


@router.get("/list", response_model=list[LearningContentOut])
def list_contents(limit: int = 20, db: Session = Depends(get_db)):
    """获取 AI 生成内容列表。"""
    contents = content_repo.list_ai_contents(db, limit=limit)
    log.debug("返回内容列表 count=%s", len(contents))
    return [_content_to_out(c, content_repo.parse_words(c)) for c in contents]


@router.get("/today-list", response_model=TodayContentListResponse)
def get_today_list(user_id: int = 1, db: Session = Depends(get_db)):
    """
    获取今日完整学习内容列表（总览 + 最多 3 篇文章）。
    前端根据用户学习时长目标决定展示几条：
      15-30 min → 只看总览（第 1 条）
      30-40 min → 总览 + 1 篇
      40-50 min → 总览 + 2 篇
      50-60 min → 全部
    """
    from app.schemas import THEME_OPTIONS
    import random

    user = user_repo.get_user(db, user_id)
    theme = "daily_news"
    if user and user.preference:
        theme = user.preference.theme_type

    # all_random 用户从今日已有内容里随机取一个 theme
    if theme == "all_random":
        all_today = content_repo.get_today_ai_contents(db)
        if all_today:
            themes_today = list({c.theme_type for c in all_today})
            theme = random.choice(themes_today)
            log.debug("all_random 用户，随机选 theme=%s", theme)
        else:
            theme = random.choice([t for t in THEME_OPTIONS if t != "all_random"])
            log.debug("all_random 用户无今日内容，降级 theme=%s", theme)

    daily_goal = 15
    if user and user.preference:
        daily_goal = user.preference.daily_goal_count  # 前端存的是分钟数

    contents = content_repo.get_today_content_list_by_theme(db, theme)
    log.debug("today-list theme=%s count=%s daily_goal=%s", theme, len(contents), daily_goal)

    # 追加用户的自定义内容
    from app.models import LearningContent as LC
    custom_contents = (
        db.query(LC)
        .filter(
            LC.user_id == user_id,
            LC.creator_type == 1,
            LC.is_active == True,
        )
        .order_by(LC.created_at.desc())
        .all()
    )
    all_contents = list(contents) + list(custom_contents)

    return TodayContentListResponse(
        theme=theme,
        daily_goal_minutes=daily_goal,
        contents=[_content_to_out(c, content_repo.parse_words(c)) for c in all_contents],
    )


@router.get("/content/{content_id}", response_model=LearningContentOut)
def get_content(content_id: int, db: Session = Depends(get_db)):
    """按 ID 获取学习内容。"""
    content = content_repo.get_content_by_id(db, content_id)
    if not content:
        log.debug("content_id=%s 不存在", content_id)
        raise HTTPException(404, "内容不存在")
    words = content_repo.parse_words(content)
    return _content_to_out(content, words)


@router.get("/review", response_model=ReviewListResponse)
def get_review_tasks(user_id: int = 1, db: Session = Depends(get_db)):
    """查询今日待复习任务列表（stage>=1 且 next_review_at <= 当前时间）。"""
    from datetime import datetime
    from sqlalchemy import and_
    from app.models import UserMemoryProgress, LearningContent as LC

    log.debug("查询复习任务 user_id=%s", user_id)
    now = datetime.utcnow()
    rows = (
        db.query(UserMemoryProgress, LC)
        .join(LC, LC.content_id == UserMemoryProgress.content_id)
        .filter(
            and_(
                UserMemoryProgress.user_id == user_id,
                UserMemoryProgress.review_stage >= 1,
                UserMemoryProgress.next_review_at <= now,
                LC.is_active == True,
            )
        )
        .order_by(UserMemoryProgress.next_review_at.asc())
        .all()
    )
    tasks = [
        ReviewTaskOut(
            content_id=p.content_id,
            title=c.title,
            review_stage=p.review_stage,
            last_accuracy=float(p.last_accuracy or 0),
            next_review_at=p.next_review_at,
        )
        for p, c in rows
    ]
    log.debug("待复习任务数 user_id=%s count=%s", user_id, len(tasks))
    return ReviewListResponse(user_id=user_id, total_count=len(tasks), tasks=tasks)


@router.get("/progress", response_model=MemoryProgressListResponse)
def get_all_progress(user_id: int = 1, db: Session = Depends(get_db)):
    """查询用户全部内容的记忆进度（用于复习页展示）。"""
    from sqlalchemy import and_
    from app.models import UserMemoryProgress, LearningContent as LC

    log.debug("查询全部记忆进度 user_id=%s", user_id)
    rows = (
        db.query(UserMemoryProgress, LC)
        .join(LC, LC.content_id == UserMemoryProgress.content_id)
        .filter(
            and_(
                UserMemoryProgress.user_id == user_id,
                LC.is_active == True,
            )
        )
        .order_by(UserMemoryProgress.next_review_at.asc())
        .all()
    )
    items = [
        MemoryProgressOut(
            content_id=c.content_id,
            title=c.title,
            review_stage=p.review_stage,
            last_accuracy=float(p.last_accuracy or 0),
            next_review_at=p.next_review_at,
            is_mastered=p.is_mastered,
            total_review_count=p.total_review_count,
        )
        for p, c in rows
    ]
    mastered = sum(1 for i in items if i.is_mastered)
    log.debug("全部记忆进度 user_id=%s total=%s mastered=%s", user_id, len(items), mastered)
    return MemoryProgressListResponse(
        user_id=user_id, total_count=len(items), mastered_count=mastered, items=items,
    )


@router.get("/generation-limit")
def get_generation_limit(user_id: int = 1, db: Session = Depends(get_db)):
    """获取用户今日剩余生成次数。"""
    from datetime import date
    from app.models import DailyGenerationLimit

    today = date.today()
    limit_record = (
        db.query(DailyGenerationLimit)
        .filter(
            DailyGenerationLimit.user_id == user_id,
            DailyGenerationLimit.limit_date == today
        )
        .first()
    )
    
    used_count = limit_record.generation_count if limit_record else 0
    remaining = max(0, 3 - used_count)
    
    log.debug("生成次数限制 user_id=%s used=%s remaining=%s", user_id, used_count, remaining)
    return {
        "user_id": user_id,
        "used_count": used_count,
        "remaining_count": remaining,
        "max_count": 3
    }


@router.post("/cleanup")
def cleanup_excess_content(db: Session = Depends(get_db)):
    """
    清理多余的学习内容：每个 (日期, 主题) 最多保留 4 条。
    为什么是 4：用户最大每日时长 45-60 分钟，对应 4 篇内容。
    """
    from datetime import date
    from sqlalchemy import func, and_
    from app.models import LearningContent

    # 按 (created_at日期, theme_type) 分组，统计每组数量
    subq = (
        db.query(
            func.date(LearningContent.created_at).label("day"),
            LearningContent.theme_type,
            func.count().label("cnt"),
        )
        .filter(LearningContent.creator_type == 0, LearningContent.is_active == True)
        .group_by(func.date(LearningContent.created_at), LearningContent.theme_type)
        .having(func.count() > 4)
        .subquery()
    )

    # 找出需要删除的内容（每组保留最早创建的 4 条，删除其余）
    rows = db.query(subq).all()
    total_deleted = 0
    for day, theme_type, cnt in rows:
        # 该组所有内容，按创建时间排序
        items = (
            db.query(LearningContent)
            .filter(
                and_(
                    func.date(LearningContent.created_at) == day,
                    LearningContent.theme_type == theme_type,
                    LearningContent.creator_type == 0,
                    LearningContent.is_active == True,
                )
            )
            .order_by(LearningContent.created_at.asc())
            .all()
        )
        # 保留前 4 条，软删除其余
        for item in items[4:]:
            item.is_active = False
            total_deleted += 1

    db.commit()
    log.debug("清理完成，软删除 %s 条多余内容", total_deleted)
    return {"deleted_count": total_deleted}


@router.post("/clear-all")
def clear_all_ai_content(db: Session = Depends(get_db)):
    """清除所有AI生成的内容（软删除），用于重新生成。"""
    from app.models import LearningContent, UserMemoryProgress, DailyGenerationLimit

    # 软删除所有AI生成内容
    contents = db.query(LearningContent).filter(LearningContent.creator_type == 0).all()
    count = 0
    for c in contents:
        if c.is_active:
            c.is_active = False
            count += 1

    # 清除所有记忆进度（因为内容被删除了）
    progress_count = db.query(UserMemoryProgress).delete()

    # 清除生成次数限制（让用户可以重新生成）
    limit_count = db.query(DailyGenerationLimit).delete()

    db.commit()
    log.info("已清除 %s 条AI内容、%s 条记忆进度、%s 条生成限制", count, progress_count, limit_count)
    return {"deleted_contents": count, "deleted_progress": progress_count, "deleted_limits": limit_count}


# ============== 已学内容标记 ==============

@router.post("/learned/toggle")
def toggle_learned(user_id: int, content_id: int, db: Session = Depends(get_db)):
    """切换内容的已学状态：未学→已学，已学→取消。"""
    from app.models import UserLearnedContent

    existing = (
        db.query(UserLearnedContent)
        .filter(UserLearnedContent.user_id == user_id, UserLearnedContent.content_id == content_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        log.debug("取消已学 user_id=%s content_id=%s", user_id, content_id)
        return {"learned": False}
    else:
        record = UserLearnedContent(user_id=user_id, content_id=content_id)
        db.add(record)
        db.commit()
        log.debug("标记已学 user_id=%s content_id=%s", user_id, content_id)
        return {"learned": True}


@router.get("/learned/check")
def check_learned(user_id: int, content_id: int, db: Session = Depends(get_db)):
    """检查内容是否已学。"""
    from app.models import UserLearnedContent

    exists = (
        db.query(UserLearnedContent)
        .filter(UserLearnedContent.user_id == user_id, UserLearnedContent.content_id == content_id)
        .first()
    ) is not None
    return {"learned": exists}


@router.get("/learned/list")
def get_learned_content_ids(user_id: int, db: Session = Depends(get_db)):
    """获取用户所有已学内容的 content_id 列表。"""
    from app.models import UserLearnedContent

    rows = (
        db.query(UserLearnedContent.content_id)
        .filter(UserLearnedContent.user_id == user_id)
        .all()
    )
    return {"content_ids": [r[0] for r in rows]}


@router.get("/review/learned")
def get_learned_review_tasks(user_id: int = 1, db: Session = Depends(get_db)):
    """查询已学内容的复习任务（仅从已学内容中筛选待复习的）。"""
    from datetime import datetime
    from sqlalchemy import and_
    from app.models import UserMemoryProgress, UserLearnedContent, LearningContent as LC

    now = datetime.utcnow()
    rows = (
        db.query(UserMemoryProgress, LC)
        .join(LC, LC.content_id == UserMemoryProgress.content_id)
        .join(UserLearnedContent, and_(
            UserLearnedContent.user_id == user_id,
            UserLearnedContent.content_id == UserMemoryProgress.content_id,
        ))
        .filter(
            and_(
                UserMemoryProgress.user_id == user_id,
                UserMemoryProgress.review_stage >= 1,
                UserMemoryProgress.next_review_at <= now,
                LC.is_active == True,
            )
        )
        .order_by(UserMemoryProgress.next_review_at.asc())
        .all()
    )
    tasks = [
        ReviewTaskOut(
            content_id=p.content_id,
            title=c.title,
            review_stage=p.review_stage,
            last_accuracy=float(p.last_accuracy or 0),
            next_review_at=p.next_review_at,
        )
        for p, c in rows
    ]
    return ReviewListResponse(user_id=user_id, total_count=len(tasks), tasks=tasks)


# ============== 自定义学习内容 ==============

async def _process_custom_content(text: str) -> dict:
    """调用 LLM 处理用户粘贴的文本，生成翻译和生词。"""
    from app.services.llm_client import chat_json

    system_prompt = """你是一位英语教学专家。用户会粘贴一段英文文本，请完成以下任务：
1. 根据内容生成一个简短的英文标题（不超过 8 个词）
2. 将全文翻译成中文
3. 从文本中提取 5-10 个对英语学习者有价值的生词或短语

严格按如下 JSON 格式输出，不要包含任何额外文字：
{
  "title": "英文标题",
  "translation": "完整中文翻译",
  "lexicon": [
    {
      "word": "单词或短语",
      "phonetic": "音标",
      "meaning": "中文释义，含词性",
      "usage": "原文中包含该词的完整句子"
    }
  ]
}

生词提取规则：
- 优先选择 CET-4/CET-6 级别的实词（名词、动词、形容词、副词）
- 避免冠词、介词、代词等虚词
- 每个 usage 必须是原文中的原句
- 如果文本较短，可以少提取，但至少提取 3 个"""

    user_prompt = f"请处理以下英文文本：\n\n{text}"

    result = await chat_json(system_prompt, user_prompt, temperature=0.3)
    if not result:
        log.debug("LLM 返回空结果，使用降级方案")
        return {
            "title": text[:50].strip() + "..." if len(text) > 50 else text.strip(),
            "translation": "（翻译生成失败，请稍后重试）",
            "lexicon": [],
        }
    return result


@router.post("/custom-content", response_model=CustomContentResponse)
async def create_custom_content(
    payload: CustomContentRequest,
    db: Session = Depends(get_db),
):
    """用户粘贴文本，AI 生成翻译和生词，创建自定义学习内容。"""
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="内容不能为空")

    # 检查每日限额（和 AI 生成共用）
    from datetime import date
    from app.models import DailyGenerationLimit

    today = date.today()
    limit_record = (
        db.query(DailyGenerationLimit)
        .filter(
            DailyGenerationLimit.user_id == payload.user_id,
            DailyGenerationLimit.limit_date == today,
        )
        .first()
    )
    used_count = limit_record.generation_count if limit_record else 0
    if used_count >= 3:
        log.debug("用户 %s 今日已生成 %s 次，自定义内容达上限", payload.user_id, used_count)
        raise HTTPException(status_code=429, detail="今日生成次数已用完（每天 3 篇）")

    # 调用 AI 处理文本
    log.debug("开始处理自定义内容 user_id=%s text_len=%s", payload.user_id, len(text))
    ai_result = await _process_custom_content(text)

    # 读取用户偏好获取 difficulty_level
    user = user_repo.get_user(db, payload.user_id)
    difficulty = "medium"
    if user and user.preference:
        difficulty = user.preference.difficulty_level

    # 写入数据库
    content = content_repo.create_user_content(
        db=db,
        user_id=payload.user_id,
        title=ai_result.get("title", "自定义内容"),
        content_text=text,
        difficulty_level=difficulty,
        theme_type="custom",
        translation=ai_result.get("translation"),
        key_words=ai_result.get("lexicon", []),
    )

    # 初始化记忆进度
    content_repo.init_memory_progress(db, payload.user_id, content.content_id)

    # 更新生成次数
    if limit_record:
        limit_record.generation_count += 1
    else:
        from app.models import DailyGenerationLimit as DGL
        db.add(DGL(
            user_id=payload.user_id,
            limit_date=today,
            generation_count=1,
        ))
    db.commit()

    log.debug("自定义内容创建成功 content_id=%s user_id=%s", content.content_id, payload.user_id)
    return CustomContentResponse(
        content_id=content.content_id,
        title=content.title,
        message="自定义内容已创建，进入复习计划",
    )


@router.get("/custom-content")
def list_custom_content(user_id: int = 1, db: Session = Depends(get_db)):
    """获取用户的自定义学习内容列表。"""
    from app.models import LearningContent as LC

    contents = (
        db.query(LC)
        .filter(
            LC.user_id == user_id,
            LC.creator_type == 1,
            LC.is_active == True,
        )
        .order_by(LC.created_at.desc())
        .all()
    )
    result = []
    for c in contents:
        words = content_repo.parse_words(c)
        result.append(_content_to_out(c, words))
    return {"contents": result, "total": len(result)}


@router.delete("/custom-content/{content_id}")
def delete_custom_content(
    content_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db),
):
    """删除用户的自定义学习内容（只能删自己的）。"""
    from app.models import LearningContent as LC

    content = (
        db.query(LC)
        .filter(
            LC.content_id == content_id,
            LC.user_id == user_id,
            LC.creator_type == 1,
        )
        .first()
    )
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在或无权删除")

    content.is_active = False
    db.commit()
    log.debug("自定义内容已删除 content_id=%s user_id=%s", content_id, user_id)
    return {"message": "已删除"}
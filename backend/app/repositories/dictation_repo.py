"""
默写历史数据访问层。

为什么默写记录只增不改：user_dictation_history 是流水表，
每次默写都是独立事件，历史不可篡改，分析高频错词也依赖完整历史。
覆盖更新只发生在 user_memory_progress 的 last_accuracy 字段。
"""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import UserDictationHistory, UserMemoryProgress

log = logging.getLogger(__name__)

# 艾宾浩斯复习间隔（天数），stage 0-7
_EBBINGHAUS_INTERVALS = [0, 1, 2, 4, 7, 15, 30, 60]


def create_dictation(
    db: Session,
    user_id: int,
    content_id: Optional[int],
    original_text: str,
    user_input: str,
    accuracy_rate: float,
    feedback: dict[str, Any],
    earned_points: int,
    time_spent_seconds: Optional[int] = None,
) -> UserDictationHistory:
    """写入一条默写流水记录。"""
    from app.services.week_helper import get_year_week
    year_week = get_year_week(datetime.utcnow())

    # 优先使用 AI 输出的 error_words，fallback 从 diffs 提取
    error_words = feedback.get("error_words", [])
    if not error_words:
        diffs = feedback.get("diffs", [])
        error_words = list({
            d.get("expected", "").lower()
            for d in diffs
            if d.get("type") in ("missing", "wrong") and d.get("expected")
        })

    record = UserDictationHistory(
        user_id=user_id,
        content_id=content_id,
        year_week=year_week,
        original_text=original_text,
        user_input=user_input,
        accuracy_rate=accuracy_rate,
        time_spent_seconds=time_spent_seconds,
        ai_feedback=json.dumps(feedback, ensure_ascii=False),
        error_words=json.dumps(error_words, ensure_ascii=False),
        earned_points=earned_points,
    )
    db.add(record)
    db.flush()
    log.debug("默写记录已写入 dictation_id=%s user_id=%s accuracy=%.1f",
              record.dictation_id, user_id, accuracy_rate)
    return record


def update_memory_progress(
    db: Session,
    user_id: int,
    content_id: int,
    accuracy_rate: float,
) -> UserMemoryProgress:
    """
    根据本次默写正确率更新记忆进度。

    为什么把记忆进度更新放在 dictation_repo：
    每次默写完成后必须同步更新进度，两者是同一个业务事件的两个写操作，
    放在一起确保不会漏写。

    艾宾浩斯规则：正确率 >= 80 则升级 stage，否则 stage 重置为 1（不归零，保留已学状态）。
    """
    progress = db.query(UserMemoryProgress).filter(
        UserMemoryProgress.user_id == user_id,
        UserMemoryProgress.content_id == content_id,
    ).first()

    if not progress:
        log.debug("记忆进度不存在，新建 user_id=%s content_id=%s", user_id, content_id)
        progress = UserMemoryProgress(
            user_id=user_id,
            content_id=content_id,
            review_stage=0,
            total_review_count=0,
            last_accuracy=0.00,
        )
        db.add(progress)
        db.flush()

    progress.last_accuracy = accuracy_rate
    progress.last_review_at = datetime.utcnow()
    progress.total_review_count += 1

    if accuracy_rate >= 80:
        # 答对：升级复习阶段，最高到 stage 7
        new_stage = min(progress.review_stage + 1, len(_EBBINGHAUS_INTERVALS) - 1)
        log.debug("正确率 %.1f >= 80，stage %s -> %s", accuracy_rate, progress.review_stage, new_stage)
        progress.review_stage = new_stage
    else:
        # 答错：退回 stage 1，保留已学状态不归零
        log.debug("正确率 %.1f < 80，stage 重置为 1", accuracy_rate)
        progress.review_stage = 1

    # 是否已完全掌握（连续达到最高阶段）
    if progress.review_stage >= len(_EBBINGHAUS_INTERVALS) - 1 and accuracy_rate >= 95:
        progress.is_mastered = True
        log.debug("content_id=%s 已标记为掌握", content_id)

    # 计算下次复习时间
    interval = _EBBINGHAUS_INTERVALS[progress.review_stage]
    from datetime import timedelta
    progress.next_review_at = datetime.utcnow() + timedelta(days=interval)
    log.debug("下次复习时间 content_id=%s interval=%d天 next=%s",
              content_id, interval, progress.next_review_at.date())

    return progress


def list_user_dictations(
    db: Session,
    user_id: int,
    limit: int = 20,
) -> list[UserDictationHistory]:
    """查询用户最近的默写记录。"""
    return (
        db.query(UserDictationHistory)
        .filter(UserDictationHistory.user_id == user_id)
        .order_by(UserDictationHistory.created_at.desc())
        .limit(limit)
        .all()
    )


def get_week_low_accuracy(
    db: Session,
    user_id: int,
    year_week: str,
    top_n: int = 5,
) -> list[int]:
    """
    捞出本周正确率最低的 content_id 列表，用于周复习推送。

    为什么用子查询取最低均值而不是直接排序：同一内容可能本周练了多次，
    取平均值比取单次最低更能反映真实掌握程度。
    """
    from sqlalchemy import func
    rows = (
        db.query(
            UserDictationHistory.content_id,
            func.avg(UserDictationHistory.accuracy_rate).label("avg_acc"),
        )
        .filter(
            UserDictationHistory.user_id == user_id,
            UserDictationHistory.year_week == year_week,
            UserDictationHistory.content_id.isnot(None),
        )
        .group_by(UserDictationHistory.content_id)
        .order_by(func.avg(UserDictationHistory.accuracy_rate).asc())
        .limit(top_n)
        .all()
    )
    content_ids = [r.content_id for r in rows]
    log.debug("周复习低正确率 content_ids=%s year_week=%s", content_ids, year_week)
    return content_ids
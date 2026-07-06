"""
打卡提醒服务。

为什么单独建一个 service：reminder 逻辑（计算距今天数、判断是否需要提醒）
属于纯计算，和打卡 repo 的 I/O 操作分开，符合规则一的单一职责原则。
"""
import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories import checkin_repo

log = logging.getLogger(__name__)


def get_days_since_last_checkin(db: Session, user_id: int) -> Optional[int]:
    """
    返回距今最近一次打卡已过多少天。

    为什么返回 None 而不是 0：从未打卡和今日已打卡是完全不同的状态，
    None 让调用方可以区分"新用户"和"今天打过卡"两种情况。
    """
    last_date = checkin_repo.get_last_checkin_date(db, user_id)
    if last_date is None:
        log.debug("user_id=%s 从未打卡，返回 None", user_id)
        return None
    days = (date.today() - last_date).days
    log.debug("user_id=%s 最近打卡=%s，距今 %d 天", user_id, last_date, days)
    return days


def should_remind(db: Session, user_id: int) -> tuple[bool, int, int]:
    """
    判断是否需要对该用户展示提醒。

    为什么返回 tuple 而不是 bool：router 需要同时把
    days_since_last 和 threshold 透传给前端，
    集中在这里计算避免 router 再查一次 DB。

    返回值：(需要提醒, 距今天数, 阈值天数)
    - 从未打卡视为需要提醒（days = -1 表示新用户）
    - 今天已打卡（days == 0）不需要提醒
    """
    threshold = settings.REMINDER_THRESHOLD_DAYS
    days = get_days_since_last_checkin(db, user_id)

    if days is None:
        # 新用户，从未打卡：提醒一次鼓励开始
        log.debug("user_id=%s 新用户，触发首次提醒", user_id)
        return True, -1, threshold

    if days > threshold:
        log.debug("user_id=%s 已 %d 天未打卡，超过阈值 %d，需要提醒", user_id, days, threshold)
        return True, days, threshold

    log.debug("user_id=%s 距今 %d 天，未超过阈值 %d，不提醒", user_id, days, threshold)
    return False, days, threshold

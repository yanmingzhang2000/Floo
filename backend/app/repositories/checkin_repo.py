"""
打卡数据访问层。

为什么打卡和周报放同一个 repo：打卡记录是周报统计的数据源，
两者耦合度高，放在一起方便统计查询复用同一个 db session。
"""
import logging
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models import UserCheckinRecord, UserWeeklySummary

log = logging.getLogger(__name__)


def find_checkin(db: Session, user_id: int, day: date) -> Optional[UserCheckinRecord]:
    """查询某天的打卡记录。"""
    record = (
        db.query(UserCheckinRecord)
        .filter(
            UserCheckinRecord.user_id == user_id,
            UserCheckinRecord.checkin_date == day,
        )
        .first()
    )
    if record:
        log.debug("user_id=%s 在 %s 已打卡 checkin_id=%s", user_id, day, record.checkin_id)
    return record


def create_checkin(
    db: Session,
    user_id: int,
    day: date,
    points: int,
    note: Optional[str],
) -> UserCheckinRecord:
    """写入打卡记录。"""
    from app.services.week_helper import get_year_week
    from datetime import datetime
    year_week = get_year_week(datetime.combine(day, datetime.min.time()))

    record = UserCheckinRecord(
        user_id=user_id,
        checkin_date=day,
        year_week=year_week,
        completed_count=1,
        earned_points=points,
        note=note,
    )
    db.add(record)
    db.flush()
    log.debug("打卡记录已创建 checkin_id=%s user_id=%s date=%s", record.checkin_id, user_id, day)
    return record


def has_checkin_yesterday(db: Session, user_id: int, today: date) -> bool:
    """判断昨天是否打卡，用于连续天数计算。"""
    yesterday = today - timedelta(days=1)
    return find_checkin(db, user_id, yesterday) is not None


def list_month_checkins(
    db: Session,
    user_id: int,
    year: int,
    month: int,
) -> list[UserCheckinRecord]:
    """
    返回某月所有打卡记录。

    为什么用半开区间 [start, end)：用 < end 比 <= last_day 少一次月末判断，
    不用考虑闰年 2 月的边界问题。
    """
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    records = (
        db.query(UserCheckinRecord)
        .filter(
            UserCheckinRecord.user_id == user_id,
            UserCheckinRecord.checkin_date >= start,
            UserCheckinRecord.checkin_date < end,
        )
        .all()
    )
    log.debug("user_id=%s %s-%s 共 %d 条打卡", user_id, year, month, len(records))
    return records


def get_or_create_weekly_summary(
    db: Session,
    user_id: int,
    year_week: str,
) -> UserWeeklySummary:
    """
    获取或创建本周汇总记录。

    为什么用 get_or_create：周报可能由打卡触发也可能由定时任务触发，
    两个入口都需要保证只有一条记录。
    """
    summary = db.query(UserWeeklySummary).filter(
        UserWeeklySummary.user_id == user_id,
        UserWeeklySummary.year_week == year_week,
    ).first()

    if not summary:
        summary = UserWeeklySummary(
            user_id=user_id,
            year_week=year_week,
            total_checkin_days=0,
            total_learned_count=0,
            weekly_review_status=0,
        )
        db.add(summary)
        db.flush()
        log.debug("创建周汇总 user_id=%s year_week=%s", user_id, year_week)
    else:
        log.debug("周汇总已存在 user_id=%s year_week=%s", user_id, year_week)

    return summary


def increment_weekly_checkin(db: Session, user_id: int, year_week: str) -> None:
    """打卡成功后累加本周打卡天数到周汇总。"""
    summary = get_or_create_weekly_summary(db, user_id, year_week)
    summary.total_checkin_days += 1
    log.debug("周打卡天数 +1 -> %s user_id=%s week=%s",
              summary.total_checkin_days, user_id, year_week)


def get_weekly_summary(
    db: Session,
    user_id: int,
    year_week: str,
) -> Optional[UserWeeklySummary]:
    """查询指定周的汇总数据。"""
    return db.query(UserWeeklySummary).filter(
        UserWeeklySummary.user_id == user_id,
        UserWeeklySummary.year_week == year_week,
    ).first()
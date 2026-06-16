"""
打卡数据访问层。

为什么打卡和周报放同一个 repo：打卡记录是周报统计的数据源，
两者耦合度高，放在一起方便统计查询复用同一个 db session。
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.models import UserCheckinRecord, UserDictationHistory, UserWeeklySummary, PointLogHistory
from app.schemas import WeeklySummaryOut

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


def _year_week_to_range(year_week: str) -> tuple[date, date]:
    """
    将 YYYYWW 格式的周次字符串转为 [周一, 下周一) 日期区间。

    为什么用 ISO week：create_checkin 和 dictation_repo 都用 ISO week number，
    周报统计的时间范围必须与它们一致，否则会漏数据。
    """
    year = int(year_week[:4])
    week = int(year_week[4:])
    # ISO 周一：从第 1 周周一开始
    jan4 = date(year, 1, 4)
    start_of_week1 = jan4 - timedelta(days=jan4.isocalendar()[2] - 1)
    monday = start_of_week1 + timedelta(weeks=week - 1)
    next_monday = monday + timedelta(weeks=1)
    return monday, next_monday


def get_weekly_summary(
    db: Session,
    user_id: int,
    year_week: str,
) -> WeeklySummaryOut:
    """
    从原始数据实时计算本周学习汇总。

    为什么不走预计算的 user_weekly_summary 表：该表目前只在打卡时更新
    total_checkin_days，其他字段从未写入（历史原因），直接查原始数据更可靠。
    未来如果性能瓶颈可加缓存，但当前用户量不需要。
    """
    monday, next_monday = _year_week_to_range(year_week)

    # 本周打卡天数
    checkin_count = (
        db.query(sql_func.count(UserCheckinRecord.checkin_id))
        .filter(
            UserCheckinRecord.user_id == user_id,
            UserCheckinRecord.checkin_date >= monday,
            UserCheckinRecord.checkin_date < next_monday,
        )
        .scalar()
        or 0
    )

    # 本周默写次数 & 平均正确率
    dict_stats = (
        db.query(
            sql_func.count(UserDictationHistory.dictation_id).label("cnt"),
            sql_func.avg(UserDictationHistory.accuracy_rate).label("avg_acc"),
        )
        .filter(
            UserDictationHistory.user_id == user_id,
            UserDictationHistory.created_at >= datetime.combine(monday, datetime.min.time()),
            UserDictationHistory.created_at < datetime.combine(next_monday, datetime.min.time()),
        )
        .first()
    )
    if dict_stats:
        learned_count = dict_stats[0] or 0
        avg_acc = float(dict_stats[1] or 0.0) if dict_stats[1] is not None else 0.0
    else:
        learned_count = 0
        avg_acc = 0.0

    # 本周获得积分（正数流水之和）
    points_result = (
        db.query(sql_func.coalesce(sql_func.sum(PointLogHistory.change_amount), 0))
        .filter(
            PointLogHistory.user_id == user_id,
            PointLogHistory.change_amount > 0,
            PointLogHistory.created_at >= datetime.combine(monday, datetime.min.time()),
            PointLogHistory.created_at < datetime.combine(next_monday, datetime.min.time()),
        )
        .scalar()
        or 0
    )

    log.debug("周报动态计算 user_id=%s week=%s checkins=%s dicts=%s avg_acc=%.1f points=%s",
              user_id, year_week, checkin_count, learned_count, avg_acc, points_result)

    # 直接返回 Pydantic 模型，避免未持久化 ORM 实例序列化异常
    return WeeklySummaryOut(
        year_week=year_week,
        total_checkin_days=checkin_count,
        total_learned_count=learned_count,
        avg_accuracy_rate=round(avg_acc, 2),
        total_earned_points=points_result,
        weekly_review_status=0,
    )

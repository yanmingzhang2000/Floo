"""
接口 3：打卡与日历看板。

为什么打卡要同步更新周汇总：周报统计依赖 user_weekly_summary，
打卡时实时更新比定时任务更简单，MVP 阶段无需引入 Celery 等异步任务。
"""
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import checkin_repo, user_repo
from app.schemas import (
    CheckinCalendarOut,
    CheckinOut,
    CheckinRequest,
    CheckinResponse,
    WeeklySummaryOut,
)
from app.services.week_helper import get_year_week

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/checkin", tags=["checkin"])

DEFAULT_POINTS = 10


@router.post("", response_model=CheckinResponse)
def do_checkin(payload: CheckinRequest, db: Session = Depends(get_db)):
    """
    今日打卡：写记录 + 加积分 + 更新连续天数 + 更新周汇总。

    幂等性：同一天重复请求直接返回已有记录，不重复加分。
    """
    user = user_repo.get_user(db, payload.user_id)
    if not user:
        log.debug("user_id=%s 不存在", payload.user_id)
        raise HTTPException(404, "用户不存在")

    account = user_repo.get_point_account(db, payload.user_id)
    if not account:
        log.debug("user_id=%s 无积分账户", payload.user_id)
        raise HTTPException(500, "积分账户异常，请联系管理员")

    today = date.today()
    existing = checkin_repo.find_checkin(db, user.user_id, today)
    if existing:
        log.debug("幂等：%s 已打卡，直接返回", today)
        return CheckinResponse(
            checkin=CheckinOut.model_validate(existing),
            available_points=account.available_points,
            current_streak_days=account.current_streak_days,
        )

    # 写打卡记录
    record = checkin_repo.create_checkin(
        db, user.user_id, today, DEFAULT_POINTS, payload.note
    )

    # 加积分
    user_repo.add_points(
        db=db,
        account=account,
        amount=DEFAULT_POINTS,
        change_type="checkin",
        reference_id=record.checkin_id,
        description=f"{today} 打卡",
    )

    # 更新连续打卡天数
    has_yesterday = checkin_repo.has_checkin_yesterday(db, user.user_id, today)
    user_repo.update_streak(db, account, has_yesterday)

    # 同步更新周汇总
    from datetime import datetime
    year_week = get_year_week(datetime.combine(today, datetime.min.time()))
    checkin_repo.increment_weekly_checkin(db, user.user_id, year_week)

    db.commit()
    db.refresh(record)
    db.refresh(account)

    return CheckinResponse(
        checkin=CheckinOut.model_validate(record),
        available_points=account.available_points,
        current_streak_days=account.current_streak_days,
    )


@router.get("/calendar", response_model=CheckinCalendarOut)
def get_calendar(
    user_id: int = 1,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_db),
):
    """返回某月打卡日历，前端用来渲染热力图。"""
    user = user_repo.get_user(db, user_id)
    if not user:
        log.debug("user_id=%s 不存在", user_id)
        raise HTTPException(404, "用户不存在")

    account = user_repo.get_point_account(db, user_id)
    today = date.today()
    year = year or today.year
    month = month or today.month

    records = checkin_repo.list_month_checkins(db, user_id, year, month)
    return CheckinCalendarOut(
        user_id=user_id,
        year=year,
        month=month,
        checked_dates=[r.checkin_date for r in records],
        available_points=account.available_points if account else 0,
        current_streak_days=account.current_streak_days if account else 0,
    )


@router.get("/weekly", response_model=WeeklySummaryOut)
def get_weekly_summary(
    user_id: int = 1,
    year_week: str | None = None,
    db: Session = Depends(get_db),
):
    """查询周报数据，默认返回本周。"""
    user = user_repo.get_user(db, user_id)
    if not user:
        log.debug("user_id=%s 不存在", user_id)
        raise HTTPException(404, "用户不存在")

    from datetime import datetime
    target_week = year_week or get_year_week(datetime.utcnow())
    summary = checkin_repo.get_weekly_summary(db, user_id, target_week)
    if not summary:
        log.debug("user_id=%s week=%s 无周报数据", user_id, target_week)
        raise HTTPException(404, "本周暂无学习数据")

    return summary
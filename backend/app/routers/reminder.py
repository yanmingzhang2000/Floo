"""
接口：打卡提醒状态查询。

为什么用拉取（pull）而不是服务端推送：
前端在打开 App 时主动查询一次，既能控制提醒频率（前端缓存当日已提醒标记），
又不需要引入 WebSocket 或推送服务，MVP 阶段复杂度最低。
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import user_repo
from app.services import reminder_service

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reminder", tags=["reminder"])


@router.get("/status")
def get_reminder_status(user_id: int, db: Session = Depends(get_db)):
    """
    查询当前用户是否需要收到"未背单词"提醒。

    前端每次打开 App 时调用；前端负责记录"今日已展示"标记，
    避免同一天多次弹窗。
    """
    user = user_repo.get_user(db, user_id)
    if not user:
        log.debug("user_id=%s 不存在，返回 404", user_id)
        raise HTTPException(status_code=404, detail="用户不存在")

    need_remind, days_since_last, threshold = reminder_service.should_remind(db, user_id)

    log.debug(
        "user_id=%s should_remind=%s days_since_last=%s threshold=%s",
        user_id, need_remind, days_since_last, threshold,
    )

    return {
        "should_remind": need_remind,
        "days_since_last": days_since_last,
        "threshold": threshold,
    }

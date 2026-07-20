"""
接口 0：用户注册、登录、偏好设置。

为什么 MVP 阶段不加 JWT：减少依赖复杂度，前端先用 user_id=1 的测试用户跑通，
鉴权机制在产品验证后再引入。
"""
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import user_repo
from app.schemas import (
    UserLoginRequest,
    UserOut,
    UserPreferenceOut,
    UserPreferenceUpdate,
    UserRegisterRequest,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/user", tags=["user"])


def _hash_password(password: str) -> str:
    """简单 SHA256 哈希，MVP 阶段够用，生产环境应换 bcrypt。"""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register", response_model=UserOut)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """用户注册，同步创建偏好表和积分账户。"""
    existing = user_repo.get_user_by_username(db, payload.username)
    if existing:
        log.debug("用户名已存在 username=%s", payload.username)
        raise HTTPException(400, "用户名已被注册")

    user = user_repo.create_user(
        db=db,
        username=payload.username,
        password_hash=_hash_password(payload.password),
        nickname=payload.nickname,
        email=payload.email,
    )
    db.commit()
    db.refresh(user)
    log.debug("注册成功 user_id=%s username=%s", user.user_id, user.username)
    return user


@router.post("/login", response_model=UserOut)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """用户登录，返回用户基本信息。"""
    user = user_repo.get_user_by_username(db, payload.username)
    if not user or user.password_hash != _hash_password(payload.password):
        log.debug("登录失败 username=%s", payload.username)
        raise HTTPException(401, "用户名或密码错误")
    if not user.is_active:
        log.debug("账户已禁用 username=%s", payload.username)
        raise HTTPException(403, "账户已被禁用")
    log.debug("登录成功 user_id=%s", user.user_id)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取用户基本信息。"""
    user = user_repo.get_user(db, user_id)
    if not user:
        log.debug("user_id=%s 不存在", user_id)
        raise HTTPException(404, "用户不存在")
    return user


@router.get("/{user_id}/preference")
def get_preference(user_id: int, db: Session = Depends(get_db)):
    """获取用户学习偏好。"""
    user = user_repo.get_user(db, user_id)
    if not user or not user.preference:
        log.debug("user_id=%s 偏好不存在", user_id)
        raise HTTPException(404, "用户偏好不存在")
    pref = user.preference
    return {
        "theme_type": pref.theme_type,
        "daily_goal_minutes": pref.daily_goal_count,
    }
def update_preference(
    user_id: int,
    payload: UserPreferenceUpdate,
    db: Session = Depends(get_db),
):
    """更新用户学习偏好（主题、每日目标）。"""
    pref = user_repo.update_preference(
        db=db,
        user_id=user_id,
        theme_type=payload.theme_type,
        daily_goal_count=payload.daily_goal_count,
    )
    if not pref:
        log.debug("user_id=%s 偏好不存在，无法更新", user_id)
        raise HTTPException(404, "用户偏好不存在")
    db.commit()
    return {
        "theme_type": pref.theme_type,
        "daily_goal_minutes": pref.daily_goal_count,
    }
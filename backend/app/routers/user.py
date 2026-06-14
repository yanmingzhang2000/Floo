"""
接口 0：用户注册、登录、偏好设置。

为什么 MVP 阶段不加 JWT：减少依赖复杂度，前端先用 user_id=1 的测试用户跑通，
鉴权机制在产品验证后再引入。
"""
import hashlib
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.repositories import user_repo
from app.schemas import (
    UserLoginRequest,
    UserOut,
    UserPreferenceOut,
    UserPreferenceUpdate,
    UserRegisterRequest,
    WechatLoginRequest,
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
        "difficulty_level": pref.difficulty_level,
        "theme_type": pref.theme_type,
        "daily_goal_minutes": pref.daily_goal_count,
    }


@router.put("/{user_id}/preference")
def update_preference(
    user_id: int,
    payload: UserPreferenceUpdate,
    db: Session = Depends(get_db),
):
    """更新用户学习偏好（难度、主题、每日目标）。"""
    pref = user_repo.update_preference(
        db=db,
        user_id=user_id,
        difficulty_level=payload.difficulty_level,
        theme_type=payload.theme_type,
        daily_goal_count=payload.daily_goal_count,
    )
    if not pref:
        log.debug("user_id=%s 偏好不存在，无法更新", user_id)
        raise HTTPException(404, "用户偏好不存在")
    db.commit()
    return {
        "difficulty_level": pref.difficulty_level,
        "theme_type": pref.theme_type,
        "daily_goal_minutes": pref.daily_goal_count,
    }


@router.post("/wechat-login", response_model=UserOut)
def wechat_login(payload: WechatLoginRequest, db: Session = Depends(get_db)):
    """微信小程序登录，通过 code 换取 openid 完成登录/自动注册。"""
    # 检查配置
    if not settings.WX_APPID or not settings.WX_SECRET:
        log.debug("微信登录未配置 WX_APPID/WX_SECRET")
        raise HTTPException(500, "微信登录未配置")

    # 调用微信接口换取 openid
    try:
        resp = httpx.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": settings.WX_APPID,
                "secret": settings.WX_SECRET,
                "js_code": payload.code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        data = resp.json()
        log.debug("微信 code2session 响应: %s", data)
    except Exception as e:
        log.debug("调用微信接口失败: %s", e)
        raise HTTPException(500, "微信登录服务异常")

    openid = data.get("openid")
    if not openid:
        error_msg = data.get("errmsg", "未知错误")
        log.debug("获取 openid 失败: %s", error_msg)
        raise HTTPException(400, f"微信登录失败: {error_msg}")

    # 查找或创建用户
    user = user_repo.get_user_by_openid(db, openid)
    if not user:
        log.debug("openid=%s 不存在，自动注册", openid)
        user = user_repo.create_wechat_user(
            db=db,
            openid=openid,
            nickname="微信用户",
            avatar_url=None,
        )
        db.commit()
        db.refresh(user)

    # 更新登录时间
    user.last_login_time = datetime.utcnow()
    db.commit()

    log.debug("微信登录成功 user_id=%s openid=%s", user.user_id, openid)
    return user


@router.post("/bind-wechat")
def bind_wechat(user_id: int, payload: WechatLoginRequest, db: Session = Depends(get_db)):
    """绑定微信到已有账号，用户在设置页点击绑定时调用。"""
    # 检查配置
    if not settings.WX_APPID or not settings.WX_SECRET:
        log.debug("微信绑定未配置 WX_APPID/WX_SECRET")
        raise HTTPException(500, "微信登录未配置")

    # 检查用户是否存在
    user = user_repo.get_user(db, user_id)
    if not user:
        log.debug("user_id=%s 不存在", user_id)
        raise HTTPException(404, "用户不存在")

    # 检查是否已绑定其他账号
    if user.openid:
        log.debug("user_id=%s 已绑定微信", user_id)
        raise HTTPException(400, "该账号已绑定微信")

    # 调用微信接口换取 openid
    try:
        resp = httpx.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": settings.WX_APPID,
                "secret": settings.WX_SECRET,
                "js_code": payload.code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        data = resp.json()
        log.debug("微信 code2session 响应: %s", data)
    except Exception as e:
        log.debug("调用微信接口失败: %s", e)
        raise HTTPException(500, "微信登录服务异常")

    openid = data.get("openid")
    if not openid:
        error_msg = data.get("errmsg", "未知错误")
        log.debug("获取 openid 失败: %s", error_msg)
        raise HTTPException(400, f"微信登录失败: {error_msg}")

    # 检查该 openid 是否已被其他账号绑定
    existing_user = user_repo.get_user_by_openid(db, openid)
    if existing_user:
        log.debug("openid=%s 已被 user_id=%s 绑定", openid, existing_user.user_id)
        raise HTTPException(400, "该微信已绑定其他账号")

    # 绑定
    user.openid = openid
    db.commit()

    log.debug("微信绑定成功 user_id=%s openid=%s", user_id, openid)
    return {"message": "绑定成功"}
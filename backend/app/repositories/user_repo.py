"""
用户数据访问层。

为什么把偏好和积分账户的读写也放这里：
用户注册时三张表必须同步创建（user_main / preference / point_account），
事务边界放在 repo 层，router 只需一次调用。
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models import PointLogHistory, UserLearningPreference, UserMain, UserPointAccount

log = logging.getLogger(__name__)


def get_user(db: Session, user_id: int) -> Optional[UserMain]:
    """按 ID 查用户。"""
    user = db.query(UserMain).filter(UserMain.user_id == user_id).first()
    if not user:
        log.debug("user_id=%s 不存在", user_id)
    return user


def get_user_by_username(db: Session, username: str) -> Optional[UserMain]:
    """按用户名查用户，用于登录校验。"""
    return db.query(UserMain).filter(UserMain.username == username).first()


def create_user(
    db: Session,
    username: str,
    password_hash: str,
    nickname: str,
    email: Optional[str] = None,
) -> UserMain:
    """
    创建用户并同步初始化偏好表和积分账户。

    为什么三表同步创建：注册是原子操作，任何一张表缺失都会导致后续功能异常。
    """
    user = UserMain(
        username=username,
        password_hash=password_hash,
        nickname=nickname,
        email=email,
    )
    db.add(user)
    db.flush()  # 获取 user_id

    # 初始化学习偏好
    preference = UserLearningPreference(
        user_id=user.user_id,
        difficulty_level="medium",
        theme_type="daily_life",
        daily_goal_count=5,
    )
    db.add(preference)

    # 初始化积分账户
    account = UserPointAccount(
        user_id=user.user_id,
        total_earned_points=0,
        available_points=0,
        total_consumed_points=0,
    )
    db.add(account)

    db.flush()
    log.debug("创建用户 user_id=%s username=%s，偏好和积分账户已初始化", user.user_id, username)
    return user


def get_point_account(db: Session, user_id: int) -> Optional[UserPointAccount]:
    """获取用户积分账户。"""
    return db.query(UserPointAccount).filter(UserPointAccount.user_id == user_id).first()


def add_points(
    db: Session,
    account: UserPointAccount,
    amount: int,
    change_type: str,
    reference_id: Optional[int] = None,
    description: Optional[str] = None,
) -> None:
    """
    为用户增加积分并写入流水。

    为什么流水和余额绑在一起写：任何余额变更必须有流水溯源，
    拆开写容易造成余额和流水对不上账。
    """
    if amount == 0:
        log.debug("amount=0，跳过积分变更 user_id=%s", account.user_id)
        return

    account.available_points += amount
    if amount > 0:
        account.total_earned_points += amount
    else:
        account.total_consumed_points += abs(amount)

    db.add(PointLogHistory(
        account_id=account.account_id,
        user_id=account.user_id,
        change_amount=amount,
        change_type=change_type,
        reference_id=reference_id,
        description=description,
        balance_after=account.available_points,
    ))
    log.debug("积分变更 user_id=%s amount=%+d type=%s balance=%s",
              account.user_id, amount, change_type, account.available_points)


def update_streak(db: Session, account: UserPointAccount, has_yesterday: bool) -> None:
    """
    更新连续打卡天数。

    为什么在积分账户表存 streak：streak 属于激励体系的一部分，
    和积分账户同属集群四，放一起更新事务更简单。
    """
    if has_yesterday:
        account.current_streak_days += 1
        log.debug("连续打卡 +1 -> %s user_id=%s", account.current_streak_days, account.user_id)
    else:
        account.current_streak_days = 1
        log.debug("连续打卡重置为 1 user_id=%s", account.user_id)

    if account.current_streak_days > account.max_streak_days:
        account.max_streak_days = account.current_streak_days


def update_preference(
    db: Session,
    user_id: int,
    theme_type: Optional[str] = None,
    daily_goal_count: Optional[int] = None,
) -> Optional[UserLearningPreference]:
    """更新用户学习偏好。"""
    pref = db.query(UserLearningPreference).filter(
        UserLearningPreference.user_id == user_id
    ).first()
    if not pref:
        log.debug("user_id=%s 偏好记录不存在", user_id)
        return None
    if theme_type is not None:
        pref.theme_type = theme_type
    if daily_goal_count is not None:
        pref.daily_goal_count = daily_goal_count
    log.debug("user_id=%s 偏好已更新", user_id)
    return pref
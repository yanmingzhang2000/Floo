"""
积分商城路由 - 盲盒抽奖、角色收藏、积分消费。

抽卡逻辑：按权重随机抽取角色，重复角色累加 count。
"""
import logging
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Character, UserCollection, UserMain, UserPointAccount, PointLogHistory
from app.repositories.user_repo import add_points

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/shop", tags=["shop"])

# 盲盒价格
BOX_PRICE = 50
TEN_BOX_PRICE = 450
HUNDRED_BOX_PRICE = 4000


@router.get("/characters")
def get_characters(user_id: int, db: Session = Depends(get_db)):
    """获取所有角色列表 + 用户已收集情况。"""
    characters = db.query(Character).filter(Character.is_active == True).all()
    user_collections = {}
    if user_id:
        collections = db.query(UserCollection).filter(UserCollection.user_id == user_id).all()
        for c in collections:
            user_collections[c.character_id] = c.count

    result = []
    for char in characters:
        result.append({
            "character_id": char.character_id,
            "name": char.name,
            "meaning": char.meaning,
            "image_url": char.image_url,
            "rarity": char.rarity,
            "description": char.description,
            "count": user_collections.get(char.character_id, 0),
        })

    return {"characters": result}


@router.get("/balance")
def get_balance(user_id: int, db: Session = Depends(get_db)):
    """获取用户积分余额。"""
    account = db.query(UserPointAccount).filter(UserPointAccount.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="积分账户不存在")
    return {"available_points": account.available_points}


@router.post("/open-box")
def open_box(user_id: int, count: int = 1, db: Session = Depends(get_db)):
    """
    开盲盒。
    count: 抽取次数（1/10/100）
    """
    if count not in [1, 10, 100]:
        raise HTTPException(status_code=400, detail="抽取次数只能是1/10/100")

    # 计算价格
    if count == 1:
        price = BOX_PRICE
    elif count == 10:
        price = TEN_BOX_PRICE
    else:
        price = HUNDRED_BOX_PRICE

    # 检查积分
    account = db.query(UserPointAccount).filter(UserPointAccount.user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="积分账户不存在")
    if account.available_points < price:
        raise HTTPException(status_code=400, detail=f"积分不足，需要{price}积分，当前{account.available_points}积分")

    # 扣积分
    account.available_points -= price
    account.total_consumed_points += price
    db.add(PointLogHistory(
        account_id=account.account_id,
        user_id=user_id,
        change_amount=-price,
        change_type="redeem",
        description=f"盲盒抽奖x{count}",
        balance_after=account.available_points,
    ))

    # 获取所有激活角色及其权重
    characters = db.query(Character).filter(Character.is_active == True).all()
    if not characters:
        raise HTTPException(status_code=500, detail="暂无角色数据")

    names = [c.name for c in characters]
    weights = [c.weight for c in characters]

    # 抽卡
    results = []
    for _ in range(count):
        chosen_name = random.choices(names, weights=weights, k=1)[0]
        chosen_char = next(c for c in characters if c.name == chosen_name)

        # 检查是否已有
        existing = db.query(UserCollection).filter(
            UserCollection.user_id == user_id,
            UserCollection.character_id == chosen_char.character_id,
        ).first()

        if existing:
            existing.count += 1
            existing.last_obtained_at = datetime.utcnow()
            is_new = False
        else:
            existing = UserCollection(
                user_id=user_id,
                character_id=chosen_char.character_id,
                count=1,
            )
            db.add(existing)
            is_new = True

        results.append({
            "character_id": chosen_char.character_id,
            "name": chosen_char.name,
            "meaning": chosen_char.meaning,
            "image_url": chosen_char.image_url,
            "rarity": chosen_char.rarity,
            "description": chosen_char.description,
            "is_new": is_new,
        })

    db.commit()

    return {
        "results": results,
        "remaining_points": account.available_points,
    }


@router.get("/collection")
def get_collection(user_id: int, db: Session = Depends(get_db)):
    """获取用户收藏的角色列表。"""
    collections = (
        db.query(UserCollection)
        .filter(UserCollection.user_id == user_id)
        .order_by(UserCollection.obtained_at.desc())
        .all()
    )

    result = []
    for c in collections:
        char = c.character
        result.append({
            "collection_id": c.collection_id,
            "character_id": char.character_id,
            "name": char.name,
            "meaning": char.meaning,
            "image_url": char.image_url,
            "rarity": char.rarity,
            "description": char.description,
            "count": c.count,
            "obtained_at": c.obtained_at.isoformat() if c.obtained_at else None,
        })

    return {"collection": result}


@router.post("/admin/give-points")
def give_points_to_all_users(amount: int = 50, db: Session = Depends(get_db)):
    """管理员：给所有用户赠送积分。"""
    accounts = db.query(UserPointAccount).all()
    count = 0
    for account in accounts:
        add_points(
            db=db,
            account=account,
            amount=amount,
            change_type="reward",
            description="新手赠送积分",
        )
        count += 1
    db.commit()
    log.debug("给 %d 个用户赠送了 %d 积分", count, amount)
    return {"message": f"已给 {count} 个用户赠送 {amount} 积分"}

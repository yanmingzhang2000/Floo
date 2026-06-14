"""给所有用户赠送50积分"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.database import SessionLocal
from app.models import UserPointAccount, PointLogHistory

POINTS_TO_ADD = 50
DESCRIPTION = "新手赠送积分"

def main():
    db = SessionLocal()
    try:
        accounts = db.query(UserPointAccount).all()
        count = 0
        for account in accounts:
            # 增加积分
            account.available_points += POINTS_TO_ADD
            account.total_earned_points += POINTS_TO_ADD
            
            # 记录流水
            log = PointLogHistory(
                account_id=account.account_id,
                user_id=account.user_id,
                change_amount=POINTS_TO_ADD,
                change_type="reward",
                description=DESCRIPTION,
                balance_after=account.available_points,
            )
            db.add(log)
            count += 1
            print(f"用户 {account.user_id} 赠送 {POINTS_TO_ADD} 积分，余额: {account.available_points}")
        
        db.commit()
        print(f"\n完成！共给 {count} 个用户赠送了 {POINTS_TO_ADD} 积分")
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

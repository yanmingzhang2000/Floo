from app.database import SessionLocal
from app.models import UserMain, UserLearningPreference

db = SessionLocal()
users = db.query(UserMain).all()
print(f'用户总数: {len(users)}')
for u in users:
    print(f'  user_id={u.user_id} username={u.username}')
    pref = db.query(UserLearningPreference).filter(UserLearningPreference.user_id == u.user_id).first()
    if pref:
        print(f'    偏好: difficulty={pref.difficulty_level} theme={pref.theme_type}')
    else:
        print(f'    偏好: 无记录（使用默认值 medium / daily_life）')
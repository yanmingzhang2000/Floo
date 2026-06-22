from sqlalchemy import text
from app.database import SessionLocal
from app.models import LearningContent

db = SessionLocal()

# 检查列是否已存在（MySQL）
result = db.execute(text("SHOW COLUMNS FROM learning_contents LIKE 'content_type'"))
if result.fetchone():
    print('content_type 列已存在，跳过')
else:
    db.execute(text("ALTER TABLE learning_contents ADD COLUMN content_type VARCHAR(16) NOT NULL DEFAULT 'article'"))
    db.commit()
    print('已添加 content_type 列')

# 为 daily_generation_limit 表添加 limit_type 列
result = db.execute(text("SHOW COLUMNS FROM daily_generation_limit LIKE 'limit_type'"))
if result.fetchone():
    print('limit_type 列已存在，跳过')
else:
    db.execute(text("ALTER TABLE daily_generation_limit ADD COLUMN limit_type VARCHAR(16) NOT NULL DEFAULT 'ai'"))
    db.commit()
    print('已添加 limit_type 列')

# 清理旧的唯一约束（如果存在），添加新的组合唯一约束
try:
    db.execute(text("ALTER TABLE daily_generation_limit DROP INDEX uq_user_date_limit"))
    db.execute(text("CREATE UNIQUE INDEX uq_user_date_limit_type ON daily_generation_limit (user_id, limit_date, limit_type)"))
    db.commit()
    print('已更新唯一约束')
except Exception as e:
    print(f'唯一约束更新跳过：{e}（可能已存在新索引）')

# 清除旧的 AI 生成内容
deleted = db.query(LearningContent).filter(LearningContent.creator_type == 0).delete()
db.commit()
print(f'已清除 {deleted} 条旧 AI 测试内容')

db.close()
print('迁移完成')

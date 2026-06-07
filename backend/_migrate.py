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

# 清除旧的 AI 生成内容
deleted = db.query(LearningContent).filter(LearningContent.creator_type == 0).delete()
db.commit()
print(f'已清除 {deleted} 条旧 AI 测试内容')

db.close()
print('迁移完成')
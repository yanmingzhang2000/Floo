"""一键初始化 Floo! 数据库：建表 + 创建测试用户 + 初始化关联数据。

使用方式：python init_db.py

初始化内容：
1. 创建所有 9 张表
2. 创建测试用户（user_id=1）及其关联的偏好表、积分账户
3. 生成 2 条示例学习内容（AI 或 mock）
4. 为测试用户初始化记忆进度记录
"""
import asyncio
import logging
from datetime import datetime

from app.core.logging import setup_logging
from app.database import Base, SessionLocal, engine
from app.models import (
    LearningContent,
    UserLearningPreference,
    UserMain,
    UserMemoryProgress,
    UserPointAccount,
)
from app.services.news_generator import generate_daily_news

setup_logging()
log = logging.getLogger(__name__)


def init():
    print("==> 创建数据表...")
    Base.metadata.create_all(bind=engine)
    print("    [OK] 9 张表创建完成")

    db = SessionLocal()
    try:
        # 1. 创建测试用户
        user = db.query(UserMain).filter(UserMain.user_id == 1).first()
        if not user:
            user = UserMain(
                user_id=1,
                username="test_user",
                password_hash="mock_hash_12345",  # 实际应用需要真实哈希
                nickname="Floo测试者",
                email="test@floo.app",
            )
            db.add(user)
            db.flush()
            log.debug("测试用户已创建 user_id=1")

            # 2. 创建用户偏好
            preference = UserLearningPreference(
                user_id=user.user_id,
                difficulty_level="medium",
                theme_type="daily_life",
                daily_goal_count=5,
            )
            db.add(preference)
            log.debug("用户偏好已创建")

            # 3. 创建积分账户
            account = UserPointAccount(
                user_id=user.user_id,
                total_earned_points=0,
                available_points=0,
            )
            db.add(account)
            log.debug("积分账户已创建")

            db.commit()
            print("==> 测试用户创建完成 (user_id=1, username=test_user)")
        else:
            log.debug("测试用户已存在，跳过创建")
            print("==> 测试用户已存在")

        # 4. 生成示例学习内容（AI 或 mock）
        existing_count = db.query(LearningContent).count()
        if existing_count == 0:
            print("==> 生成示例学习内容...")
            for i in range(2):
                data = asyncio.run(generate_daily_news())
                content = LearningContent(
                    creator_type=0,  # AI 生成
                    user_id=None,
                    difficulty_level=data.get("difficulty_level", "medium"),
                    theme_type=data.get("theme_type", "daily_life"),
                    title=data.get("title", f"Sample Content {i+1}"),
                    content_text=data.get("article", "Sample text"),
                    translation=data.get("translation"),
                    key_words=str(data.get("words", [])),  # 临时存 JSON 字符串
                )
                db.add(content)
                db.flush()

                # 5. 为测试用户初始化记忆进度
                progress = UserMemoryProgress(
                    user_id=1,
                    content_id=content.content_id,
                    review_stage=0,
                    next_review_at=datetime.utcnow(),  # 立即可复习
                )
                db.add(progress)
                log.debug("示例内容 %s 已生成，content_id=%s", i+1, content.content_id)

            db.commit()
            print("    [OK] 已生成 2 条示例内容并初始化记忆进度")
        else:
            log.debug("已有 %s 条学习内容，跳过生成", existing_count)
            print(f"==> 已有 {existing_count} 条学习内容")

        print("\n==> 初始化完成 [OK]")
        print("\n下一步：")
        print("  1. 启动后端：uvicorn app.main:app --reload")
        print("  2. 访问 API 文档：http://localhost:8000/docs")
        print("  3. 测试用户凭证：username=test_user, user_id=1")
    except Exception as e:
        log.error("初始化失败：%s", e, exc_info=True)
        print(f"\n==> 初始化失败：{e}")
        print("请检查：")
        print("  1. MySQL 服务是否启动")
        print("  2. .env 文件中的 DATABASE_URL 是否正确")
        print("  3. 数据库 floo_core_db 是否已创建")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init()
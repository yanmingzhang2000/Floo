"""FastAPI 应用入口。

为什么在这里建表而不是用 Alembic：MVP 阶段追求零配置启动，
后续表结构稳定后再引入迁移工具。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logging import setup_logging
from app.database import Base, engine, SessionLocal
from app.models import Character
from app.routers import checkin, daily, dictation, dictionary, favorites, shop, speech, tts, word_review
from app.routers import user
from app.routers import ai_coach
from app.routers import reminder
from app.routers import book

setup_logging()
log = logging.getLogger(__name__)

# 启动时自动建表
Base.metadata.create_all(bind=engine)
log.debug("数据库表已同步")

# 兼容性补丁：检查并补齐缺失列（避免 schema 不匹配导致 500）
def _patch_missing_columns():
    """检查并补齐缺失列，避免 schema 不匹配导致 500。
    为什么不用 Alembic：MVP 阶段求快速迭代，后续再规范。"""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        # 检查 openid 列是否存在
        result = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'user_main' AND COLUMN_NAME = 'openid'"
        )).scalar()
        if result == 0:
            log.info("检测到 user_main 缺少 openid 列，开始补列")
            db.execute(text(
                "ALTER TABLE user_main ADD COLUMN openid VARCHAR(128) NULL UNIQUE, "
                "ADD INDEX ix_user_main_openid (openid)"
            ))
            db.commit()
            log.info("openid 列已补齐")
        else:
            log.debug("user_main.openid 列已存在，跳过补列")

        # 检查 user_favorite_words.is_mastered 列是否存在
        result2 = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'user_favorite_words' AND COLUMN_NAME = 'is_mastered'"
        )).scalar()
        if result2 == 0:
            log.info("检测到 user_favorite_words 缺少 is_mastered 列，开始补列")
            db.execute(text(
                "ALTER TABLE user_favorite_words ADD COLUMN is_mastered BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            db.commit()
            log.info("is_mastered 列已补齐")
        else:
            log.debug("user_favorite_words.is_mastered 列已存在，跳过补列")

        # 检查 daily_generation_limit.limit_type 列是否存在
        result3 = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'daily_generation_limit' AND COLUMN_NAME = 'limit_type'"
        )).scalar()
        if result3 == 0:
            log.info("检测到 daily_generation_limit 缺少 limit_type 列，开始补列")
            db.execute(text(
                "ALTER TABLE daily_generation_limit "
                "ADD COLUMN limit_type VARCHAR(16) NOT NULL DEFAULT 'ai'"
            ))
            # 尝试删除旧唯一索引并创建新索引
            try:
                db.execute(text("ALTER TABLE daily_generation_limit DROP INDEX uq_user_date_limit"))
            except Exception:
                log.debug("旧索引 uq_user_date_limit 不存在，跳过删除")
            db.execute(text(
                "CREATE UNIQUE INDEX uq_user_date_limit_type "
                "ON daily_generation_limit (user_id, limit_date, limit_type)"
            ))
            db.commit()
            log.info("limit_type 列已补齐")
        else:
            log.debug("daily_generation_limit.limit_type 列已存在，跳过补列")
    except Exception as e:
        db.rollback()
        log.warning("补列检查失败（如果数据库已正常可忽略）: %s", e)
    finally:
        db.close()

_patch_missing_columns()

# 初始化盲盒角色数据（仅首次）
CHARACTERS_INIT = [
    {"name": "Wisdom", "meaning": "智慧", "rarity": "common", "weight": 7000, "description": "洞察世事的智慧"},
    {"name": "Courage", "meaning": "勇气", "rarity": "common", "weight": 7000, "description": "无畏前行的勇气"},
    {"name": "Hope", "meaning": "希望", "rarity": "common", "weight": 7000, "description": "照亮前路的希望"},
    {"name": "Faith", "meaning": "信念", "rarity": "common", "weight": 7000, "description": "坚定不移的信念"},
    {"name": "Grace", "meaning": "优雅", "rarity": "common", "weight": 7000, "description": "从容优雅的姿态"},
    {"name": "Peace", "meaning": "和平", "rarity": "common", "weight": 7000, "description": "内心宁静的平和"},
    {"name": "Love", "meaning": "爱", "rarity": "common", "weight": 7000, "description": "温暖万物的爱"},
    {"name": "Serenity", "meaning": "宁静", "rarity": "rare", "weight": 2500, "description": "深邃如海的宁静"},
    {"name": "Brilliance", "meaning": "才华", "rarity": "rare", "weight": 2500, "description": "璀璨夺目的才华"},
    {"name": "Infinity", "meaning": "无限", "rarity": "legendary", "weight": 500, "description": "无限可能的传说"},
]

def _seed_characters():
    """character 表为空时自动插入初始数据。"""
    db = SessionLocal()
    try:
        if db.query(Character).count() == 0:
            for item in CHARACTERS_INIT:
                db.add(Character(**item))
            db.commit()
            log.info("已初始化 %d 个盲盒角色", len(CHARACTERS_INIT))
    except Exception as e:
        db.rollback()
        log.error("角色初始化失败: %s", e)
    finally:
        db.close()

_seed_characters()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时开启定时任务调度器，关闭时清理。"""
    from app.services.scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()
    log.info("应用启动完成，定时任务已注册")
    yield
    shutdown_scheduler()


app = FastAPI(title="English Learning App API", version="0.1.0", lifespan=lifespan)


class _CorsFallbackMiddleware(BaseHTTPMiddleware):
    """兜底 CORS 中间件：确保所有响应（含 500）都带上 CORS 头。

    如果 upstream 的 CORSMiddleware 因异常路径漏加头，这里补上。
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin")
        if origin and "access-control-allow-origin" not in {k.lower() for k in response.headers}:
            log.debug("CORS 头缺失，兜底补上 origin=%s", origin)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response


app.add_middleware(_CorsFallbackMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yanmingzhang2000.github.io",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(daily.router)
app.include_router(dictation.router)
app.include_router(dictionary.router)
app.include_router(checkin.router)
app.include_router(favorites.router)
app.include_router(shop.router)
app.include_router(speech.router)
app.include_router(tts.router)
app.include_router(word_review.router)
app.include_router(ai_coach.router)
app.include_router(reminder.router)
app.include_router(book.router)


@app.get("/")
def root():
    return {"app": "english-app", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
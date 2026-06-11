"""FastAPI 应用入口。

为什么在这里建表而不是用 Alembic：MVP 阶段追求零配置启动，
后续表结构稳定后再引入迁移工具。
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.database import Base, engine, SessionLocal
from app.models import Character
from app.routers import checkin, daily, dictation, dictionary, favorites, shop, speech
from app.routers import user

setup_logging()
log = logging.getLogger(__name__)

# 启动时自动建表
Base.metadata.create_all(bind=engine)
log.debug("数据库表已同步")

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

app = FastAPI(title="English Learning App API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/")
def root():
    return {"app": "english-app", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
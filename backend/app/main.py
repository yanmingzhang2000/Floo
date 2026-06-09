"""FastAPI 应用入口。

为什么在这里建表而不是用 Alembic：MVP 阶段追求零配置启动，
后续表结构稳定后再引入迁移工具。
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging
from app.database import Base, engine
from app.routers import checkin, daily, dictation, dictionary, favorites, shop
from app.routers import user

setup_logging()
log = logging.getLogger(__name__)

# 启动时自动建表
Base.metadata.create_all(bind=engine)
log.debug("数据库表已同步")

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


@app.get("/")
def root():
    return {"app": "english-app", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
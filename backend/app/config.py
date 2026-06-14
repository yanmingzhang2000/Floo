"""应用配置。

集中管理环境变量，避免散落在各模块里硬编码。
用 pydantic-settings 自动从 .env 加载，本地开发零配置即可跑通（LLM_API_KEY 为空时走 mock）。

支持的 LLM 后端（均兼容 OpenAI 协议）：
  - Google Gemini:  LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
                    LLM_MODEL=gemini-2.0-flash
  - DeepSeek:       LLM_BASE_URL=https://api.deepseek.com/v1
                    LLM_MODEL=deepseek-chat
  - 通义千问:        LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
                    LLM_MODEL=qwen-plus
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # 大模型配置（兼容 OpenAI 协议）
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    # 有道智云语音评测
    YOUDAO_APP_ID: str = os.getenv("YOUDAO_APP_ID", "")
    YOUDAO_APP_KEY: str = os.getenv("YOUDAO_APP_KEY", "")
    YOUDAO_APP_SECRET: str = os.getenv("YOUDAO_APP_SECRET", "")

    # 微信小程序登录
    WX_APPID: str = os.getenv("WX_APPID", "")
    WX_SECRET: str = os.getenv("WX_SECRET", "")

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL 环境变量未设置，当前值为空。请检查 Railway Variables。"
    )
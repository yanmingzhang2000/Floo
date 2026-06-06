"""应用配置。

集中管理环境变量，避免散落在各模块里硬编码。
用 pydantic-settings 自动从 .env 加载，本地开发零配置即可跑通（LLM_API_KEY 为空时走 mock）。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/floo_core_db"

    # 大模型配置（兼容 OpenAI 协议：DeepSeek / 通义千问 / OpenAI 均可）
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-chat"

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000


settings = Settings()
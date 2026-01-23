from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Maya AI News Anchor"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    database_url: str = ""

    # LangChain/LangGraph
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "maya-weekly-news"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # HeyGen
    heygen_api_key: str = ""
    maya_avatar_id: str = ""
    maya_voice_id: str = ""

    # Blotato
    blotato_api_key: str = ""
    blotato_base_url: str = "https://api.blotato.com/v1"

    # Telegram
    telegram_api_id: str = ""
    telegram_api_hash: str = ""
    telegram_session_name: str = "maya_session"

    # Slack Notifications
    slack_webhook_url: Optional[str] = None
    slack_channel: str = "#maya-content"

    # Telegram Notifications (alternative)
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # App URLs
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

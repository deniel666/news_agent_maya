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
    maya_voice_locale: str = "en-SG"

    # Language & Localization
    default_language: str = "en-SG"
    malay_reviewer_webhook: Optional[str] = None  # Slack/Telegram for Malay content review

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

    # Admin Authentication
    admin_api_key: Optional[str] = None

    # App URLs
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # MCP Configuration
    mcp_enabled: bool = True
    mcp_default_timeout: int = 30

    # Composio Configuration (MCP Gateway)
    composio_api_key: Optional[str] = None
    composio_user_id: str = "maya_agent"
    composio_base_url: str = "https://backend.composio.dev"

    # Legacy MCP Server API Keys (kept for fallback)
    rapidapi_key: Optional[str] = None  # For TikTok trends (~$10/mo)

    # MCP Stock Images (FREE)
    pexels_api_key: Optional[str] = None
    unsplash_access_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None

    # MCP Analytics (subscription-based)
    metricool_user_token: Optional[str] = None
    metricool_user_id: Optional[str] = None
    sociavault_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

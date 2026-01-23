"""API endpoints for settings and configuration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from app.core.config import settings
from app.integrations.heygen import get_heygen_client
from app.integrations.blotato import get_blotato_client

router = APIRouter()


class SettingsResponse(BaseModel):
    heygen_configured: bool
    blotato_configured: bool
    telegram_configured: bool
    slack_configured: bool
    openai_configured: bool
    supabase_configured: bool


class AvatarInfo(BaseModel):
    avatar_id: str
    name: str
    preview_url: Optional[str] = None


class VoiceInfo(BaseModel):
    voice_id: str
    name: str
    language: Optional[str] = None


@router.get("/status", response_model=SettingsResponse)
async def get_settings_status():
    """Get configuration status."""
    return SettingsResponse(
        heygen_configured=bool(settings.heygen_api_key),
        blotato_configured=bool(settings.blotato_api_key),
        telegram_configured=bool(settings.telegram_api_id and settings.telegram_api_hash),
        slack_configured=bool(settings.slack_webhook_url),
        openai_configured=bool(settings.openai_api_key),
        supabase_configured=bool(settings.supabase_url and settings.supabase_key),
    )


@router.get("/avatars", response_model=List[AvatarInfo])
async def list_avatars():
    """List available HeyGen avatars."""
    if not settings.heygen_api_key:
        raise HTTPException(status_code=400, detail="HeyGen not configured")

    try:
        heygen = get_heygen_client()
        avatars = await heygen.list_avatars()

        return [
            AvatarInfo(
                avatar_id=a.get("avatar_id", ""),
                name=a.get("avatar_name", "Unknown"),
                preview_url=a.get("preview_image_url"),
            )
            for a in avatars
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices():
    """List available HeyGen voices."""
    if not settings.heygen_api_key:
        raise HTTPException(status_code=400, detail="HeyGen not configured")

    try:
        heygen = get_heygen_client()
        voices = await heygen.list_voices()

        return [
            VoiceInfo(
                voice_id=v.get("voice_id", ""),
                name=v.get("name", "Unknown"),
                language=v.get("language"),
            )
            for v in voices
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social-accounts")
async def list_social_accounts():
    """List connected social media accounts via Blotato."""
    if not settings.blotato_api_key:
        raise HTTPException(status_code=400, detail="Blotato not configured")

    try:
        blotato = get_blotato_client()
        accounts = await blotato.list_connected_accounts()
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news-sources")
async def get_news_sources():
    """Get configured news sources."""
    from app.services.news_aggregator import (
        SEA_RSS_FEEDS,
        TWITTER_ACCOUNTS,
        SEA_TELEGRAM_CHANNELS,
    )

    return {
        "rss_feeds": [
            {"name": name, "url": url}
            for name, url in SEA_RSS_FEEDS.items()
        ],
        "twitter_accounts": TWITTER_ACCOUNTS,
        "telegram_channels": SEA_TELEGRAM_CHANNELS,
    }


@router.get("/current-config")
async def get_current_config():
    """Get current Maya configuration (non-sensitive)."""
    return {
        "avatar_id": settings.maya_avatar_id or "Not configured",
        "voice_id": settings.maya_voice_id or "Not configured",
        "openai_model": settings.openai_model,
        "langchain_project": settings.langchain_project,
        "frontend_url": settings.frontend_url,
        "backend_url": settings.backend_url,
    }


class TestConnectionRequest(BaseModel):
    service: str  # heygen, blotato, openai, supabase


@router.post("/test-connection")
async def test_connection(request: TestConnectionRequest):
    """Test connection to external services."""
    service = request.service.lower()

    if service == "heygen":
        if not settings.heygen_api_key:
            return {"status": "error", "message": "HeyGen API key not configured"}
        try:
            heygen = get_heygen_client()
            await heygen.list_avatars()
            return {"status": "success", "message": "HeyGen connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif service == "blotato":
        if not settings.blotato_api_key:
            return {"status": "error", "message": "Blotato API key not configured"}
        try:
            blotato = get_blotato_client()
            await blotato.list_connected_accounts()
            return {"status": "success", "message": "Blotato connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif service == "openai":
        if not settings.openai_api_key:
            return {"status": "error", "message": "OpenAI API key not configured"}
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
            )
            from langchain_core.messages import HumanMessage
            await llm.ainvoke([HumanMessage(content="Hello")])
            return {"status": "success", "message": "OpenAI connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif service == "supabase":
        if not settings.supabase_url:
            return {"status": "error", "message": "Supabase not configured"}
        try:
            from app.services.database import get_db_service
            db = get_db_service()
            await db.get_dashboard_stats()
            return {"status": "success", "message": "Supabase connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": f"Unknown service: {service}"}

"""API endpoints for news source management."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from uuid import UUID

from app.models.sources import (
    NewsSource,
    NewsSourceCreate,
    NewsSourceUpdate,
    SourceType,
)
from app.services.database import get_db_service

router = APIRouter()


@router.get("/", response_model=List[NewsSource])
async def list_sources(
    source_type: Optional[SourceType] = None,
    enabled: Optional[bool] = None,
):
    """List all configured news sources."""
    db = get_db_service()
    sources = await db.list_sources(source_type=source_type, enabled=enabled)
    return sources


@router.post("/", response_model=NewsSource)
async def create_source(source: NewsSourceCreate):
    """Add a new news source."""
    db = get_db_service()

    # Validate URL format based on type
    if source.source_type == SourceType.RSS:
        if not source.url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="RSS URL must start with http:// or https://")
    elif source.source_type == SourceType.TELEGRAM:
        if not source.url.startswith("@"):
            source.url = f"@{source.url}"
    elif source.source_type == SourceType.TWITTER:
        source.url = source.url.lstrip("@")  # Store without @

    result = await db.create_source(source)
    return result


@router.get("/{source_id}", response_model=NewsSource)
async def get_source(source_id: UUID):
    """Get a specific source by ID."""
    db = get_db_service()
    source = await db.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=NewsSource)
async def update_source(source_id: UUID, update: NewsSourceUpdate):
    """Update a news source."""
    db = get_db_service()

    existing = await db.get_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")

    result = await db.update_source(source_id, update)
    return result


@router.delete("/{source_id}")
async def delete_source(source_id: UUID):
    """Delete a news source."""
    db = get_db_service()

    existing = await db.get_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete_source(source_id)
    return {"status": "deleted", "id": str(source_id)}


@router.post("/{source_id}/toggle")
async def toggle_source(source_id: UUID):
    """Toggle source enabled/disabled."""
    db = get_db_service()

    existing = await db.get_source(source_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")

    update = NewsSourceUpdate(enabled=not existing.enabled)
    result = await db.update_source(source_id, update)

    return {
        "id": str(source_id),
        "enabled": result.enabled,
    }


@router.post("/test/{source_id}")
async def test_source(source_id: UUID):
    """Test fetching from a source."""
    db = get_db_service()

    source = await db.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    from app.services.news_aggregator import get_news_aggregator
    aggregator = get_news_aggregator()

    try:
        if source.source_type == SourceType.RSS:
            articles = await aggregator.fetch_single_rss(source.url, source.name, days=1)
        elif source.source_type == SourceType.TWITTER:
            articles = await aggregator.fetch_single_nitter(source.url, days=1)
        elif source.source_type == SourceType.TELEGRAM:
            articles = await aggregator.fetch_single_telegram(source.url, days=1)
        else:
            articles = []

        return {
            "status": "success",
            "articles_found": len(articles),
            "sample": articles[0] if articles else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


@router.post("/import/defaults")
async def import_default_sources():
    """Import default SEA news sources."""
    db = get_db_service()

    default_sources = [
        # RSS Feeds
        {"name": "CNA", "source_type": "rss", "url": "https://www.channelnewsasia.com/rssfeeds/8395986", "category": "local"},
        {"name": "Straits Times", "source_type": "rss", "url": "https://www.straitstimes.com/news/asia/rss.xml", "category": "local"},
        {"name": "Malay Mail", "source_type": "rss", "url": "https://www.malaymail.com/feed/rss/malaysia", "category": "local"},
        {"name": "The Star", "source_type": "rss", "url": "https://www.thestar.com.my/rss/News/Nation", "category": "local"},
        {"name": "SCMP SEA", "source_type": "rss", "url": "https://www.scmp.com/rss/91/feed", "category": "local"},
        {"name": "Nikkei Asia", "source_type": "rss", "url": "https://asia.nikkei.com/rss/feed/nar", "category": "business"},
        {"name": "TechInAsia", "source_type": "rss", "url": "https://www.techinasia.com/feed", "category": "ai_tech"},
        {"name": "e27", "source_type": "rss", "url": "https://e27.co/feed/", "category": "ai_tech"},
        {"name": "VentureBeat AI", "source_type": "rss", "url": "https://venturebeat.com/category/ai/feed/", "category": "ai_tech"},

        # Twitter/Nitter accounts
        {"name": "TechInAsia Twitter", "source_type": "twitter", "url": "TechInAsia", "category": "ai_tech"},
        {"name": "e27 Twitter", "source_type": "twitter", "url": "e27co", "category": "ai_tech"},
        {"name": "CNA Business", "source_type": "twitter", "url": "CNABusiness", "category": "business"},

        # Telegram channels
        {"name": "CNA Telegram", "source_type": "telegram", "url": "@channelnewsasia", "category": "local"},
    ]

    imported = []
    for source_data in default_sources:
        try:
            source = NewsSourceCreate(**source_data)
            result = await db.create_source(source)
            imported.append(result.name)
        except Exception as e:
            pass  # Skip duplicates

    return {
        "status": "success",
        "imported": len(imported),
        "sources": imported,
    }

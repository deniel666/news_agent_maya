"""Database models for source management and cron jobs."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


class SourceType(str, Enum):
    RSS = "rss"
    TELEGRAM = "telegram"
    TWITTER = "twitter"  # via Nitter


class NewsSourceCreate(BaseModel):
    name: str
    source_type: SourceType
    url: str  # RSS URL, Telegram channel, or Twitter username
    category: Optional[str] = None  # local, business, ai_tech
    enabled: bool = True


class NewsSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    category: Optional[str] = None
    enabled: Optional[bool] = None


class NewsSource(BaseModel):
    id: UUID
    name: str
    source_type: SourceType
    url: str
    category: Optional[str] = None
    enabled: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CronSchedule(BaseModel):
    id: UUID
    name: str
    cron_expression: str  # e.g., "0 6 * * 0" for Sunday 6 AM
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CronScheduleCreate(BaseModel):
    name: str
    cron_expression: str
    enabled: bool = True


class CronScheduleUpdate(BaseModel):
    name: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None


class Language(str, Enum):
    ENGLISH = "en"
    MALAY = "ms"


class OnDemandRequest(BaseModel):
    """Request to generate video from a specific article."""
    article_url: str
    title: Optional[str] = None  # Override title
    languages: List[Language] = [Language.ENGLISH]  # Generate in these languages
    platforms: List[str] = ["instagram", "facebook", "tiktok", "youtube"]


class OnDemandJob(BaseModel):
    id: UUID
    article_url: str
    title: Optional[str] = None
    original_content: Optional[str] = None

    # Scripts per language
    script_en: Optional[str] = None
    script_ms: Optional[str] = None

    # Videos per language
    video_url_en: Optional[str] = None
    video_url_ms: Optional[str] = None

    # Captions per language
    caption_en: Optional[str] = None
    caption_ms: Optional[str] = None

    languages: List[Language]
    platforms: List[str]

    status: str = "pending"  # pending, scraping, generating_script, awaiting_approval, generating_video, publishing, completed, failed
    error: Optional[str] = None

    created_at: datetime
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TelegramApprovalMessage(BaseModel):
    """Message sent to Telegram for approval."""
    job_id: str
    job_type: str  # "weekly" or "on_demand"
    preview_text: str
    scripts: dict  # {language: script}
    video_urls: Optional[dict] = None  # {language: url}
    callback_url: str

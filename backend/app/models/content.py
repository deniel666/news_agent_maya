"""Models for content/story management."""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


class StoryType(str, Enum):
    WEEKLY_BRIEFING = "weekly_briefing"
    ON_DEMAND = "on_demand"
    MANUAL = "manual"


class StoryStatus(str, Enum):
    DRAFT = "draft"
    SCRIPT_READY = "script_ready"
    VIDEO_READY = "video_ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PublishPlatform(str, Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class StoryCreate(BaseModel):
    title: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    story_type: StoryType = StoryType.MANUAL
    tags: List[str] = Field(default_factory=list)


class StoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    status: Optional[StoryStatus] = None
    tags: Optional[List[str]] = None
    featured: Optional[bool] = None


class Story(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    story_type: StoryType
    status: StoryStatus = StoryStatus.DRAFT
    tags: List[str] = Field(default_factory=list)
    featured: bool = False

    # Content
    script_en: Optional[str] = None
    script_ms: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Related IDs
    briefing_id: Optional[UUID] = None  # If from weekly briefing
    ondemand_job_id: Optional[UUID] = None  # If from on-demand

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoAsset(BaseModel):
    id: UUID
    story_id: UUID
    language: str  # 'en' or 'ms'
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    heygen_video_id: Optional[str] = None

    # Quality/format info
    resolution: Optional[str] = None  # e.g., "1080x1920"
    format: Optional[str] = None  # e.g., "mp4"

    created_at: datetime

    class Config:
        from_attributes = True


class VideoAssetCreate(BaseModel):
    story_id: UUID
    language: str
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    heygen_video_id: Optional[str] = None


class PublishRecord(BaseModel):
    id: UUID
    story_id: UUID
    video_id: UUID
    platform: PublishPlatform
    language: str

    # Post details
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    caption: Optional[str] = None

    # Status
    status: str = "pending"  # pending, published, failed
    error: Optional[str] = None

    # Timestamps
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PublishRecordCreate(BaseModel):
    story_id: UUID
    video_id: UUID
    platform: PublishPlatform
    language: str
    caption: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class ContentStats(BaseModel):
    total_stories: int
    stories_by_status: dict  # {status: count}
    stories_by_type: dict  # {type: count}
    total_videos: int
    videos_by_language: dict  # {language: count}
    total_published: int
    published_by_platform: dict  # {platform: count}
    this_week: int
    this_month: int


class StoryWithAssets(Story):
    """Story with all related assets."""
    videos: List[VideoAsset] = Field(default_factory=list)
    publish_records: List[PublishRecord] = Field(default_factory=list)

    @property
    def video_count(self) -> int:
        return len(self.videos)

    @property
    def is_published(self) -> bool:
        return any(r.status == "published" for r in self.publish_records)

    @property
    def published_platforms(self) -> List[str]:
        return list(set(
            r.platform.value for r in self.publish_records
            if r.status == "published"
        ))

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


class PipelineStatus(str, Enum):
    AGGREGATING = "aggregating"
    CATEGORIZING = "categorizing"
    SYNTHESIZING = "synthesizing"
    AWAITING_SCRIPT_APPROVAL = "awaiting_script_approval"
    GENERATING_VIDEO = "generating_video"
    AWAITING_VIDEO_APPROVAL = "awaiting_video_approval"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"


class NewsArticle(BaseModel):
    id: Optional[str] = None
    source_type: Literal["telegram", "rss", "nitter"]
    source_name: str
    title: Optional[str] = None
    content: str
    url: Optional[str] = None
    published_at: datetime
    category: Optional[Literal["local", "business", "ai_tech"]] = None
    relevance_score: Optional[float] = None

    class Config:
        from_attributes = True


class WeeklyBriefingCreate(BaseModel):
    year: int
    week_number: int
    language_code: str = "en-SG"


class WeeklyBriefingUpdate(BaseModel):
    local_script: Optional[str] = None
    business_script: Optional[str] = None
    ai_script: Optional[str] = None
    full_script: Optional[str] = None
    status: Optional[PipelineStatus] = None
    script_approved_at: Optional[datetime] = None
    video_approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    language_code: Optional[str] = None
    requires_external_review: Optional[bool] = None


class WeeklyBriefing(BaseModel):
    id: UUID
    thread_id: str
    year: int
    week_number: int
    local_script: Optional[str] = None
    business_script: Optional[str] = None
    ai_script: Optional[str] = None
    full_script: Optional[str] = None
    status: PipelineStatus = PipelineStatus.AGGREGATING
    created_at: datetime
    script_approved_at: Optional[datetime] = None
    video_approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    language_code: str = "en-SG"
    requires_external_review: bool = False

    class Config:
        from_attributes = True


class WeeklyVideoCreate(BaseModel):
    briefing_id: UUID
    heygen_video_id: Optional[str] = None


class WeeklyVideo(BaseModel):
    id: UUID
    briefing_id: UUID
    heygen_video_id: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    status: str = "queued"
    created_at: datetime

    class Config:
        from_attributes = True


class SocialPostCreate(BaseModel):
    video_id: UUID
    platform: str
    caption: str


class SocialPost(BaseModel):
    id: UUID
    video_id: UUID
    platform: str
    caption: str
    published_at: Optional[datetime] = None
    post_url: Optional[str] = None
    status: str = "draft"

    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None


class ApprovalResponse(BaseModel):
    status: str
    message: str
    next_step: Optional[str] = None


class BriefingState(BaseModel):
    """State for the LangGraph pipeline"""
    raw_articles: List[NewsArticle] = Field(default_factory=list)
    local_news: List[NewsArticle] = Field(default_factory=list)
    business_news: List[NewsArticle] = Field(default_factory=list)
    ai_news: List[NewsArticle] = Field(default_factory=list)
    local_script: Optional[str] = None
    business_script: Optional[str] = None
    ai_script: Optional[str] = None
    full_script: Optional[str] = None
    video_url: Optional[str] = None
    caption: Optional[str] = None
    week_number: int = 0
    year: int = 0
    thread_id: Optional[str] = None
    status: PipelineStatus = PipelineStatus.AGGREGATING
    error: Optional[str] = None
    # Language support
    language_code: str = "en-SG"
    requires_external_review: bool = False


class DashboardStats(BaseModel):
    total_briefings: int
    completed_briefings: int
    pending_approvals: int
    total_videos: int
    total_posts: int


class NewsSource(BaseModel):
    name: str
    source_type: Literal["telegram", "rss", "nitter"]
    url_or_channel: str
    enabled: bool = True
    category: Optional[str] = None


class VideoLocalizationCreate(BaseModel):
    """Create a video localization for a briefing."""
    briefing_id: UUID
    language_code: str
    script: Optional[str] = None


class VideoLocalization(BaseModel):
    """Video localization for multi-language support."""
    id: UUID
    briefing_id: UUID
    language_code: str
    script: Optional[str] = None
    video_url: Optional[str] = None
    status: str = "draft"
    requires_review: bool = False
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LanguageInfo(BaseModel):
    """Language information for API responses."""
    code: str
    name: str
    locale: str
    requires_external_review: bool = False

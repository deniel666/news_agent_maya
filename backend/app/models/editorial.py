"""Editorial models for story ranking and curation."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StoryRank(str, Enum):
    """Story ranking tiers."""
    TOP_PRIORITY = "top_priority"      # Must cover - highly relevant
    HIGH = "high"                       # Strong candidate
    MEDIUM = "medium"                   # Consider if space allows
    LOW = "low"                         # Archive for later
    REJECTED = "rejected"               # Not aligned with brand


class RawStoryStatus(str, Enum):
    """Status of raw pulled stories."""
    PENDING = "pending"                 # Just pulled, not reviewed
    REVIEWING = "reviewing"             # Being reviewed by editorial agent
    RANKED = "ranked"                   # Has been scored/ranked
    PROMOTED = "promoted"               # Promoted to main story
    ARCHIVED = "archived"               # Stored for future reference


# ===================
# Raw Stories
# ===================

class RawStoryBase(BaseModel):
    """Base model for raw pulled stories."""
    title: str
    content_markdown: str               # Full content in markdown
    summary: Optional[str] = None       # AI-generated summary
    source_name: str
    source_type: str                    # rss, telegram, twitter
    source_url: Optional[str] = None
    original_url: Optional[str] = None  # Link to original article

    # Media attachments
    media_urls: List[str] = Field(default_factory=list)  # Images, videos

    # Metadata
    category: Optional[str] = None      # local, business, ai_tech
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RawStoryCreate(RawStoryBase):
    """Model for creating raw stories."""
    pass


class RawStory(RawStoryBase):
    """Full raw story model with database fields."""
    id: UUID
    status: RawStoryStatus = RawStoryStatus.PENDING

    # Ranking (filled after editorial review)
    rank: Optional[StoryRank] = None
    score: Optional[float] = None       # 0-100 relevance score
    rank_reason: Optional[str] = None   # Why this rank was assigned

    # Relationships
    promoted_story_id: Optional[UUID] = None  # If promoted to main story
    editorial_review_id: Optional[UUID] = None

    # Timestamps
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================
# Editorial Guidelines
# ===================

class GuidelineCategory(str, Enum):
    """Categories of editorial guidelines."""
    BRAND_VOICE = "brand_voice"         # Tone, style, personality
    TOPIC_PRIORITY = "topic_priority"   # What topics to prioritize
    TOPIC_AVOID = "topic_avoid"         # Topics to avoid
    AUDIENCE = "audience"               # Target audience criteria
    QUALITY = "quality"                 # Quality standards
    TIMELINESS = "timeliness"           # How fresh news should be
    REGIONAL = "regional"               # Regional relevance criteria


class EditorialGuidelineBase(BaseModel):
    """Base model for editorial guidelines."""
    name: str
    category: GuidelineCategory
    description: str
    criteria: str                       # Detailed criteria for AI to evaluate
    weight: float = 1.0                 # Weight in scoring (0.1 - 2.0)
    enabled: bool = True


class EditorialGuidelineCreate(EditorialGuidelineBase):
    """Model for creating guidelines."""
    pass


class EditorialGuidelineUpdate(BaseModel):
    """Model for updating guidelines."""
    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[str] = None
    weight: Optional[float] = None
    enabled: Optional[bool] = None


class EditorialGuideline(EditorialGuidelineBase):
    """Full guideline model."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================
# Editorial Reviews
# ===================

class EditorialReviewStatus(str, Enum):
    """Status of editorial review."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class StoryRecommendation(BaseModel):
    """Individual story recommendation from editorial review."""
    raw_story_id: UUID
    title: str
    rank: StoryRank
    score: float
    reason: str                         # Why recommended/not recommended
    suggested_angle: Optional[str] = None  # Suggested way to cover this
    key_points: List[str] = Field(default_factory=list)


class EditorialReviewBase(BaseModel):
    """Base model for editorial review."""
    week_number: int
    year: int
    review_period_start: datetime
    review_period_end: datetime


class EditorialReview(EditorialReviewBase):
    """Full editorial review model."""
    id: UUID
    status: EditorialReviewStatus = EditorialReviewStatus.IN_PROGRESS

    # Review results
    total_stories_reviewed: int = 0
    top_priority_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    rejected_count: int = 0

    # AI-generated content
    executive_summary: Optional[str] = None   # Overview of the week's news
    key_themes: List[str] = Field(default_factory=list)  # Major themes identified
    recommendations: List[StoryRecommendation] = Field(default_factory=list)
    editorial_notes: Optional[str] = None     # Additional notes for editors

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================
# Brand Profile
# ===================

class BrandProfile(BaseModel):
    """Brand profile for editorial alignment."""
    id: UUID
    name: str                           # e.g., "Erzy Media"
    tagline: Optional[str] = None

    # Brand identity
    mission: str                        # Company mission
    vision: str                         # Long-term vision
    values: List[str]                   # Core values

    # Content strategy
    target_audience: str                # Who we're creating for
    tone_of_voice: str                  # How we communicate
    content_pillars: List[str]          # Main content themes

    # Positioning
    differentiators: List[str]          # What makes us unique
    competitors: List[str]              # Who we're competing with

    # Guidelines summary for AI
    ai_prompt_context: str              # Context to include in AI prompts

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrandProfileCreate(BaseModel):
    """Model for creating/updating brand profile."""
    name: str
    tagline: Optional[str] = None
    mission: str
    vision: str
    values: List[str]
    target_audience: str
    tone_of_voice: str
    content_pillars: List[str]
    differentiators: List[str] = Field(default_factory=list)
    competitors: List[str] = Field(default_factory=list)
    ai_prompt_context: Optional[str] = None


# ===================
# Editorial Stats
# ===================

class EditorialStats(BaseModel):
    """Statistics for editorial dashboard."""
    total_raw_stories: int
    pending_review: int
    reviewed_this_week: int
    promoted_this_week: int

    # By rank
    top_priority_stories: int
    high_stories: int
    medium_stories: int
    low_stories: int
    rejected_stories: int

    # Average scores
    average_score: float

    # Reviews
    total_reviews: int
    latest_review_date: Optional[datetime] = None

"""FPF-Compliant State definitions for the Maya LangGraph pipeline.

Implements:
- Pattern A.10 & B.3: Evidence Graph Referring (Symbol Carriers with provenance)
- Pattern A.15: Work vs Method Description (draft vs approved scripts)
- Pattern E.9: Structured HITL (Design Rationale Records)
- Pattern F.9: Brand Bridge (promotional opportunity detection)
"""

from typing import TypedDict, List, Optional, Annotated, Literal
from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field

from app.models.schemas import PipelineStatus


# =============================================================================
# PATTERN A.10 & B.3: Evidence Graph Referring - Symbol Carriers
# =============================================================================

class SourceReliability(str, Enum):
    """Source reliability tiers for confidence scoring."""
    TIER_1 = "tier_1"  # Major outlets: Reuters, AP, CNA, Bloomberg
    TIER_2 = "tier_2"  # Regional: Straits Times, Malay Mail, TechInAsia
    TIER_3 = "tier_3"  # Social/Aggregators: Telegram, Twitter/X
    UNKNOWN = "unknown"


class NewsItem(BaseModel):
    """Symbol Carrier: A news item with full provenance chain.

    Every claim in the final script must trace back to a NewsItem ID,
    maintaining Chain of Custody for fact verification.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))

    # Provenance (where did this come from?)
    source_url: str
    source_name: str
    source_type: str  # rss, telegram, twitter
    source_reliability: SourceReliability = SourceReliability.UNKNOWN

    # Content (what is the fact?)
    title: str
    raw_content: str
    published_at: Optional[datetime] = None

    # Reliability metrics
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)

    # Processing metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    category: Optional[str] = None  # local, business, ai_tech

    class Config:
        frozen = False


class ExtractedFact(BaseModel):
    """A verified fact extracted from a NewsItem.

    Pattern A.1.1: Bounded Context - Journalism
    Facts are extracted WITHOUT persona, slang, or editorial tone.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))

    # Chain of custody - links back to source
    source_news_item_id: str

    # The factual claim (neutral, journalistic tone)
    claim: str

    # Supporting evidence
    evidence_quote: Optional[str] = None  # Direct quote from source

    # Verification
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    requires_verification: bool = False
    verification_notes: Optional[str] = None


class ScriptSegment(BaseModel):
    """A segment of the final script with fact traceability.

    Pattern A.15: Method Description
    The script is a recipe for video generation, not the final work.
    """
    segment_type: Literal["intro", "local", "business", "ai_tech", "outro", "bridge"]

    # The actual script text (with Maya's persona applied)
    content: str

    # Traceability: which facts support this segment?
    fact_ids: List[str] = Field(default_factory=list)

    # Timing metadata for video generation
    estimated_duration_seconds: int = 0

    # Bridge opportunity reference (if applicable)
    bridge_opportunity_id: Optional[str] = None


# =============================================================================
# PATTERN F.9: Brand Bridge - Promotional Opportunity Detection
# =============================================================================

class CongruenceLevel(str, Enum):
    """How well does the news align with our value proposition?"""
    HIGH = "high"      # Direct match (e.g., news about AI tools, we sell AI)
    MEDIUM = "medium"  # Tangential (e.g., news about productivity, we sell tools)
    LOW = "low"        # Weak connection
    NONE = "none"      # No natural bridge


class BridgeOpportunity(BaseModel):
    """A detected opportunity to naturally mention our brand/product.

    Pattern F.9: The Bridge must feel organic, not forced.
    Only HIGH/MEDIUM congruence should trigger a bridge.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))

    # Which news item triggered this opportunity?
    triggering_news_item_id: str
    triggering_fact_id: Optional[str] = None

    # Congruence analysis
    congruence_level: CongruenceLevel
    congruence_reasoning: str  # Why is this a good bridge?

    # The suggested bridge content
    suggested_hook: str  # How to naturally transition
    product_mention: str  # What to mention

    # Guardrails
    is_approved: bool = False
    rejection_reason: Optional[str] = None


# =============================================================================
# PATTERN E.9: Structured Human-in-the-Loop - Design Rationale Records
# =============================================================================

class RejectionCategory(str, Enum):
    """Structured rejection reasons for fine-tuning data."""
    TONE_TOO_AGGRESSIVE = "tone_too_aggressive"
    TONE_TOO_CASUAL = "tone_too_casual"
    FACT_CHECK_FAILED = "fact_check_failed"
    CULTURAL_INSENSITIVITY = "cultural_insensitivity"
    TIMING_TOO_LONG = "timing_too_long"
    TIMING_TOO_SHORT = "timing_too_short"
    BRIDGE_FEELS_FORCED = "bridge_feels_forced"
    MISSING_CONTEXT = "missing_context"
    OUTDATED_INFO = "outdated_info"
    QUALITY_ISSUES = "quality_issues"
    OTHER = "other"


class DesignRationaleRecord(BaseModel):
    """Structured feedback for human approval decisions.

    Pattern E.9: Capture WHY something was approved/rejected
    for future model fine-tuning.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))

    # What was being reviewed?
    review_type: Literal["script", "video", "bridge"]
    thread_id: str

    # Decision
    approved: bool

    # Structured rejection (if applicable)
    rejection_categories: List[RejectionCategory] = Field(default_factory=list)

    # Detailed feedback
    feedback_text: Optional[str] = None

    # Specific issues (for targeted fixes)
    problematic_segment_ids: List[str] = Field(default_factory=list)
    suggested_revisions: Optional[str] = None

    # Metadata
    reviewer_id: Optional[str] = None  # For multi-reviewer scenarios
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)

    # For fine-tuning: the before/after if revisions were made
    original_content: Optional[str] = None
    revised_content: Optional[str] = None


class ScriptVersion(BaseModel):
    """Versioned script with full traceability.

    Pattern A.15: Distinguishes draft from approved versions.
    """
    version: int = 1
    status: Literal["draft", "pending_review", "approved", "rejected", "revised"]

    # The script segments
    segments: List[ScriptSegment] = Field(default_factory=list)

    # Full compiled script
    full_script: str = ""

    # Caption for social media
    caption: str = ""

    # Timing
    estimated_total_duration: int = 0

    # Approval tracking
    drr: Optional[DesignRationaleRecord] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None


# =============================================================================
# STATE MERGE FUNCTIONS
# =============================================================================

def merge_news_items(left: List[dict], right: List[dict]) -> List[dict]:
    """Merge NewsItem lists, avoiding duplicates by URL."""
    seen_urls = {item.get("source_url") for item in left if item.get("source_url")}
    result = list(left)
    for item in right:
        if item.get("source_url") not in seen_urls:
            result.append(item)
            if item.get("source_url"):
                seen_urls.add(item["source_url"])
    return result


def merge_facts(left: List[dict], right: List[dict]) -> List[dict]:
    """Merge ExtractedFact lists, avoiding duplicates by ID."""
    seen_ids = {f.get("id") for f in left if f.get("id")}
    result = list(left)
    for fact in right:
        if fact.get("id") not in seen_ids:
            result.append(fact)
            if fact.get("id"):
                seen_ids.add(fact["id"])
    return result


# =============================================================================
# FPF-COMPLIANT MAYA STATE
# =============================================================================

class MayaState(TypedDict):
    """FPF-Compliant State for the Maya news briefing pipeline.

    Architectural patterns implemented:
    - A.10 & B.3: Evidence Graph (news_items with provenance)
    - A.1.1: Bounded Contexts (facts separate from persona scripts)
    - A.15: Work vs Method (draft_script vs approved_script)
    - E.9: Structured HITL (design_rationale_records)
    - F.9: Brand Bridge (bridge_opportunities)
    """

    # === Input Context ===
    week_number: int
    year: int
    thread_id: str
    language_code: str  # e.g., "en-SG", "ms-MY"

    # === Evidence Layer (Pattern A.10) ===
    # Raw news items with full provenance
    news_items: Annotated[List[dict], merge_news_items]

    # Categorized references (IDs only, not copies)
    local_news_ids: List[str]
    business_news_ids: List[str]
    ai_news_ids: List[str]

    # === Fact Extraction Layer (Pattern A.1.1 - Journalism Context) ===
    # Verified facts extracted from news items
    extracted_facts: Annotated[List[dict], merge_facts]

    # Facts organized by category
    local_facts: List[dict]
    business_facts: List[dict]
    ai_facts: List[dict]

    # === Brand Bridge Layer (Pattern F.9) ===
    bridge_opportunities: List[dict]
    selected_bridge: Optional[dict]  # The chosen bridge (if any)

    # === Script Layer (Pattern A.15) ===
    # Draft script (Method Description)
    draft_script: Optional[dict]  # ScriptVersion as dict

    # Approved script (after HITL)
    approved_script: Optional[dict]  # ScriptVersion as dict

    # === Video Layer ===
    heygen_video_id: Optional[str]
    video_url: Optional[str]
    video_duration: Optional[int]

    # === Publishing Layer ===
    post_results: Optional[dict]

    # === HITL Layer (Pattern E.9) ===
    # All review decisions with structured rationale
    design_rationale_records: List[dict]

    # Current review state
    pending_review_type: Optional[str]  # "script" or "video"

    # === Control Flow ===
    status: PipelineStatus
    error: Optional[str]

    # Revision tracking
    revision_count: int
    max_revisions: int


def create_initial_state(
    week_number: int,
    year: int,
    language_code: str = "en-SG",
) -> MayaState:
    """Create initial FPF-compliant state for a new pipeline run."""
    thread_id = f"{year}-W{week_number:02d}-{language_code}"

    return MayaState(
        # Input
        week_number=week_number,
        year=year,
        thread_id=thread_id,
        language_code=language_code,

        # Evidence Layer
        news_items=[],
        local_news_ids=[],
        business_news_ids=[],
        ai_news_ids=[],

        # Fact Extraction Layer
        extracted_facts=[],
        local_facts=[],
        business_facts=[],
        ai_facts=[],

        # Brand Bridge Layer
        bridge_opportunities=[],
        selected_bridge=None,

        # Script Layer
        draft_script=None,
        approved_script=None,

        # Video Layer
        heygen_video_id=None,
        video_url=None,
        video_duration=None,

        # Publishing
        post_results=None,

        # HITL Layer
        design_rationale_records=[],
        pending_review_type=None,

        # Control
        status=PipelineStatus.AGGREGATING,
        error=None,
        revision_count=0,
        max_revisions=3,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_news_item_by_id(state: MayaState, item_id: str) -> Optional[dict]:
    """Retrieve a NewsItem by its ID for chain-of-custody lookup."""
    for item in state.get("news_items", []):
        if item.get("id") == item_id:
            return item
    return None


def get_fact_by_id(state: MayaState, fact_id: str) -> Optional[dict]:
    """Retrieve an ExtractedFact by its ID."""
    for fact in state.get("extracted_facts", []):
        if fact.get("id") == fact_id:
            return fact
    return None


def trace_fact_to_source(state: MayaState, fact_id: str) -> Optional[dict]:
    """Full chain-of-custody: Fact -> NewsItem -> Source URL."""
    fact = get_fact_by_id(state, fact_id)
    if not fact:
        return None

    news_item = get_news_item_by_id(state, fact.get("source_news_item_id"))
    if not news_item:
        return None

    return {
        "fact": fact,
        "news_item": news_item,
        "source_url": news_item.get("source_url"),
        "source_name": news_item.get("source_name"),
        "confidence": fact.get("confidence", 0) * news_item.get("confidence_score", 0.5),
    }

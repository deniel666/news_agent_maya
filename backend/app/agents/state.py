"""State definitions for the Maya LangGraph pipeline."""

from typing import TypedDict, List, Optional, Annotated, Dict, Any
from datetime import datetime
import operator

from app.models.schemas import NewsArticle, PipelineStatus
from app.core.languages import get_language_config, DEFAULT_LANGUAGE


def merge_articles(left: List[dict], right: List[dict]) -> List[dict]:
    """Merge article lists, avoiding duplicates by URL."""
    seen_urls = {a.get("url") for a in left if a.get("url")}
    result = list(left)
    for article in right:
        if article.get("url") not in seen_urls:
            result.append(article)
            if article.get("url"):
                seen_urls.add(article["url"])
    return result


def merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dictionaries, right values override left."""
    result = dict(left)
    result.update(right)
    return result


class MayaState(TypedDict):
    """State for the Maya Media Machine pipeline.

    This state supports the 8 professional media roles:
    - Research Agent (The Scout)
    - Editor Agent (The Curator)
    - Writer Agent (The Voice)
    - Fact-Checker Agent (The Verifier)
    - Localization Agent (The Adapter)
    - Producer Agent (The Director)
    - Social Media Agent (The Promoter)
    - Analytics Agent (The Analyst)
    """

    # =========================================================================
    # INPUT PARAMETERS
    # =========================================================================
    week_number: int
    year: int
    thread_id: str

    # =========================================================================
    # LANGUAGE SUPPORT
    # =========================================================================
    language_code: str
    language_config: Dict[str, Any]
    requires_external_review: bool

    # =========================================================================
    # RESEARCH AGENT OUTPUT
    # =========================================================================
    raw_articles: Annotated[List[dict], merge_articles]
    trending_topics: List[str]  # MCP: Trending topics from Google Trends
    research_metadata: Optional[Dict[str, Any]]

    # =========================================================================
    # EDITOR AGENT OUTPUT
    # =========================================================================
    local_news: List[dict]
    business_news: List[dict]
    ai_news: List[dict]
    editorial_angles: Dict[str, str]  # article_id -> angle
    editor_metadata: Optional[Dict[str, Any]]

    # =========================================================================
    # WRITER AGENT OUTPUT
    # =========================================================================
    local_script: Optional[str]
    local_metadata: Optional[Dict[str, Any]]
    business_script: Optional[str]
    business_metadata: Optional[Dict[str, Any]]
    ai_script: Optional[str]
    ai_metadata: Optional[Dict[str, Any]]

    # =========================================================================
    # FACT-CHECKER AGENT OUTPUT
    # =========================================================================
    verification_report: Optional[Dict[str, Any]]
    flagged_claims: List[Dict[str, Any]]

    # =========================================================================
    # SCRIPT ASSEMBLER OUTPUT
    # =========================================================================
    full_script: Optional[str]
    caption: Optional[str]
    script_metadata: Optional[Dict[str, Any]]

    # =========================================================================
    # LOCALIZATION AGENT OUTPUT
    # =========================================================================
    localized_scripts: Dict[str, str]  # language_code -> script
    primary_language: Optional[str]
    localization_metadata: Optional[Dict[str, Any]]

    # =========================================================================
    # PRODUCER AGENT OUTPUT
    # =========================================================================
    heygen_video_id: Optional[str]
    video_url: Optional[str]
    video_duration: Optional[int]
    producer_metadata: Optional[Dict[str, Any]]

    # =========================================================================
    # SOCIAL MEDIA AGENT OUTPUT
    # =========================================================================
    post_results: Optional[Dict[str, Any]]
    platform_captions: Dict[str, str]  # platform -> caption
    social_metadata: Optional[Dict[str, Any]]

    # =========================================================================
    # ANALYTICS AGENT OUTPUT
    # =========================================================================
    analytics_report: Optional[Dict[str, Any]]

    # =========================================================================
    # PIPELINE CONTROL
    # =========================================================================
    status: PipelineStatus
    error: Optional[str]

    # =========================================================================
    # HUMAN APPROVAL FLAGS
    # =========================================================================
    script_approved: Optional[bool]
    script_feedback: Optional[str]
    video_approved: Optional[bool]
    video_feedback: Optional[str]


def create_initial_state(
    week_number: int,
    year: int,
    language_code: str = DEFAULT_LANGUAGE
) -> MayaState:
    """Create initial state for a new pipeline run.

    Args:
        week_number: Week number of the year
        year: Year
        language_code: Language code (e.g., 'en-SG', 'ms-MY')

    Returns:
        Initial MayaState with language configuration
    """
    thread_id = f"{year}-W{week_number:02d}-{language_code}"

    # Get language configuration
    lang_config = get_language_config(language_code)

    return MayaState(
        # Input
        week_number=week_number,
        year=year,
        thread_id=thread_id,

        # Language
        language_code=language_code,
        language_config=lang_config,
        requires_external_review=lang_config.get("requires_external_review", False),

        # Research
        raw_articles=[],
        trending_topics=[],
        research_metadata=None,

        # Editor
        local_news=[],
        business_news=[],
        ai_news=[],
        editorial_angles={},
        editor_metadata=None,

        # Writers
        local_script=None,
        local_metadata=None,
        business_script=None,
        business_metadata=None,
        ai_script=None,
        ai_metadata=None,

        # Fact-checker
        verification_report=None,
        flagged_claims=[],

        # Script assembly
        full_script=None,
        caption=None,
        script_metadata=None,

        # Localization
        localized_scripts={},
        primary_language=None,
        localization_metadata=None,

        # Producer
        heygen_video_id=None,
        video_url=None,
        video_duration=None,
        producer_metadata=None,

        # Social media
        post_results=None,
        platform_captions={},
        social_metadata=None,

        # Analytics
        analytics_report=None,

        # Control
        status=PipelineStatus.AGGREGATING,
        error=None,

        # Approvals
        script_approved=None,
        script_feedback=None,
        video_approved=None,
        video_feedback=None,
    )

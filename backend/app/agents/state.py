"""State definitions for the Maya LangGraph pipeline."""

from typing import TypedDict, List, Optional, Annotated
from datetime import datetime
import operator

from app.models.schemas import NewsArticle, PipelineStatus


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


class MayaState(TypedDict):
    """State for the Maya news briefing pipeline."""

    # Input
    week_number: int
    year: int
    thread_id: str

    # Aggregation
    raw_articles: Annotated[List[dict], merge_articles]

    # Categorized articles
    local_news: List[dict]
    business_news: List[dict]
    ai_news: List[dict]

    # Scripts
    local_script: Optional[str]
    business_script: Optional[str]
    ai_script: Optional[str]
    full_script: Optional[str]

    # Video
    heygen_video_id: Optional[str]
    video_url: Optional[str]
    video_duration: Optional[int]

    # Publishing
    caption: Optional[str]
    post_results: Optional[dict]

    # Control
    status: PipelineStatus
    error: Optional[str]

    # Human approval flags
    script_approved: Optional[bool]
    script_feedback: Optional[str]
    video_approved: Optional[bool]


def create_initial_state(week_number: int, year: int) -> MayaState:
    """Create initial state for a new pipeline run."""
    thread_id = f"{year}-W{week_number:02d}"

    return MayaState(
        week_number=week_number,
        year=year,
        thread_id=thread_id,
        raw_articles=[],
        local_news=[],
        business_news=[],
        ai_news=[],
        local_script=None,
        business_script=None,
        ai_script=None,
        full_script=None,
        heygen_video_id=None,
        video_url=None,
        video_duration=None,
        caption=None,
        post_results=None,
        status=PipelineStatus.AGGREGATING,
        error=None,
        script_approved=None,
        script_feedback=None,
        video_approved=None,
    )

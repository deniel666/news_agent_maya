"""Node functions for the Maya LangGraph pipeline.

These nodes are registered with the AgentRegistry for dynamic configuration.
Each node follows the pattern:
    async def node_name(state: MayaState, config: AgentConfig) -> Dict[str, Any]
"""

import asyncio
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.models.schemas import PipelineStatus, NewsArticle
from app.services.news_aggregator import get_news_aggregator
from app.services.notification import get_notification_service
from app.integrations.heygen import get_heygen_client
from app.integrations.blotato import get_blotato_client, MAYA_HASHTAGS
from .prompts import (
    get_maya_persona,
    get_local_news_prompt,
    get_business_news_prompt,
    get_ai_tech_news_prompt,
    get_caption_prompt,
    CATEGORIZATION_PROMPT,
    RELEVANCE_PROMPT,
)
from .state import MayaState
from .config import AgentConfig, get_config_manager
from .registry import agent, get_registry


def get_llm(config: Optional[AgentConfig] = None) -> ChatOpenAI:
    """Get LLM instance, optionally using agent config."""
    if config and config.llm_config:
        registry = get_registry()
        return registry.get_llm(config.llm_config, cache_key=config.id)

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
    )


@agent("aggregate")
async def aggregate_news(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Aggregate news from all sources.

    Config params:
        - lookback_days: Number of days to look back (default: 7)
        - sources: List of source types to use (default: all)
    """
    aggregator = get_news_aggregator()

    # Get config params
    lookback_days = 7
    if config and config.params:
        lookback_days = config.params.get("lookback_days", 7)

    try:
        articles = await aggregator.aggregate_all(days=lookback_days)

        # Convert to dict format for state
        raw_articles = [
            {
                "source_type": a.source_type,
                "source_name": a.source_name,
                "title": a.title,
                "content": a.content,
                "url": a.url,
                "published_at": a.published_at.isoformat() if a.published_at else None,
            }
            for a in articles
        ]

        return {
            "raw_articles": raw_articles,
            "status": PipelineStatus.CATEGORIZING,
        }
    except Exception as e:
        return {
            "error": f"Aggregation failed: {str(e)}",
            "status": PipelineStatus.FAILED,
        }


@agent("deduplicate")
async def deduplicate_articles(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Remove duplicate articles using title similarity.

    Config params:
        - similarity_threshold: Minimum similarity to consider duplicate (default: 0.85)
        - use_embeddings: Use semantic embeddings for dedup (default: False)
    """
    articles = state["raw_articles"]

    # Get config params
    use_embeddings = False
    if config and config.params:
        use_embeddings = config.params.get("use_embeddings", False)

    # Simple deduplication by title similarity
    seen_titles = set()
    unique_articles = []

    for article in articles:
        title = (article.get("title") or article.get("content", "")[:100]).lower()
        # Simple check - could use embeddings for better dedup
        title_key = title[:50]

        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)

    return {"raw_articles": unique_articles}


@agent("categorize")
async def categorize_articles(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Categorize articles into local, business, and AI news.

    Config params:
        - categories: List of categories to use
        - also_score_relevance: Score articles for relevance (default: True)
    """
    articles = state["raw_articles"]
    llm = get_llm(config)

    # Get limits from config
    max_items = 50
    max_per_category = 15
    if config:
        max_items = config.max_items or 50

    # Get segments config for per-category limits
    config_manager = get_config_manager()
    segments = config_manager.list_enabled_segments()

    local_news = []
    business_news = []
    ai_news = []

    for article in articles[:max_items]:
        try:
            prompt = CATEGORIZATION_PROMPT.replace(
                "${title}", article.get("title") or ""
            ).replace(
                "${content}", (article.get("content") or "")[:500]
            ).replace(
                "${source}", article.get("source_name", "")
            )

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            category = response.content.strip().lower()

            if category == "local":
                local_news.append(article)
            elif category == "business":
                business_news.append(article)
            elif category in ["ai_tech", "ai", "tech"]:
                ai_news.append(article)
        except Exception as e:
            # Default to local if categorization fails
            local_news.append(article)

    # Get per-segment limits
    local_limit = next((s.max_articles for s in segments if s.id == "local"), 15)
    business_limit = next((s.max_articles for s in segments if s.id == "business"), 15)
    ai_limit = next((s.max_articles for s in segments if s.id == "ai_tech"), 15)

    return {
        "local_news": local_news[:local_limit],
        "business_news": business_news[:business_limit],
        "ai_news": ai_news[:ai_limit],
        "status": PipelineStatus.SYNTHESIZING,
    }


@agent("synthesize_local")
async def synthesize_local(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Synthesize local and international news script.

    Uses language_config from state for localized prompts.
    """
    articles = state["local_news"]
    llm = get_llm(config)
    language_config = state.get("language_config")

    # Get max items from config
    max_items = 10
    if config:
        max_items = config.max_items or 10

    # Format articles for prompt
    articles_text = "\n\n".join([
        f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n{a.get('content', '')[:400]}"
        for a in articles[:max_items]
    ])

    # Use language-aware prompt
    prompt = get_local_news_prompt(language_config).replace(
        "${articles}", articles_text
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"local_script": response.content}


@agent("synthesize_business")
async def synthesize_business(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Synthesize business news script.

    Uses language_config from state for localized prompts.
    """
    articles = state["business_news"]
    llm = get_llm(config)
    language_config = state.get("language_config")

    max_items = 10
    if config:
        max_items = config.max_items or 10

    articles_text = "\n\n".join([
        f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n{a.get('content', '')[:400]}"
        for a in articles[:max_items]
    ])

    prompt = get_business_news_prompt(language_config).replace(
        "${articles}", articles_text
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"business_script": response.content}


@agent("synthesize_ai")
async def synthesize_ai(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Synthesize AI and tech news script.

    Uses language_config from state for localized prompts.
    """
    articles = state["ai_news"]
    llm = get_llm(config)
    language_config = state.get("language_config")

    max_items = 10
    if config:
        max_items = config.max_items or 10

    articles_text = "\n\n".join([
        f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n{a.get('content', '')[:400]}"
        for a in articles[:max_items]
    ])

    prompt = get_ai_tech_news_prompt(language_config).replace(
        "${articles}", articles_text
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"ai_script": response.content}


@agent("generate_scripts")
async def generate_scripts(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Combine individual scripts into full script with intro/outro."""
    local = state.get("local_script", "")
    business = state.get("business_script", "")
    ai = state.get("ai_script", "")
    language_config = state.get("language_config")

    # Get enabled segments in order
    config_manager = get_config_manager()
    segments = config_manager.list_enabled_segments()

    # Build script sections based on enabled segments
    sections = []
    for segment in segments:
        if segment.id == "local" and local:
            sections.append(f"[LOCAL & INTERNATIONAL NEWS]\n{local}")
        elif segment.id == "business" and business:
            sections.append(f"[BUSINESS NEWS]\n{business}")
        elif segment.id == "ai_tech" and ai:
            sections.append(f"[AI & TECH NEWS]\n{ai}")

    # Construct full script
    script_body = "\n\n".join(sections)

    full_script = f"""[INTRO]
Good evening, everyone! I'm Maya, and welcome to your weekly news roundup. Let's dive into what matters for your business this week.

{script_body}

[OUTRO]
And that's your weekly roundup! Thanks for watching. I'm Maya, and I'll see you next week. Stay informed, stay ahead!
"""

    # Generate caption using language-aware prompt
    llm = get_llm(config)
    caption_prompt = get_caption_prompt(language_config).replace(
        "${local_summary}", local[:200] if local else "Local news"
    ).replace(
        "${business_summary}", business[:200] if business else "Business updates"
    ).replace(
        "${ai_summary}", ai[:200] if ai else "Tech news"
    ).replace(
        "${week_number}", str(state["week_number"])
    ).replace(
        "${year}", str(state["year"])
    )

    caption_response = await llm.ainvoke([HumanMessage(content=caption_prompt)])

    return {
        "full_script": full_script,
        "caption": caption_response.content,
        "status": PipelineStatus.AWAITING_SCRIPT_APPROVAL,
    }


@agent("script_approval")
async def script_approval_gate(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Human approval gate for scripts.

    Config params:
        - notification_channels: List of channels to notify (slack, telegram)
        - auto_approve_after_hours: Auto-approve after N hours (None = never)
    """
    notification = get_notification_service()

    # Get notification channels from config
    channels = ["slack", "telegram"]
    if config and config.params:
        channels = config.params.get("notification_channels", channels)

    # Send notification
    await notification.send_script_approval_request(
        thread_id=state["thread_id"],
        scripts={
            "local": state.get("local_script", ""),
            "business": state.get("business_script", ""),
            "ai": state.get("ai_script", ""),
        },
        week_number=state["week_number"],
        year=state["year"],
    )

    # This node will be interrupted here for human approval
    # The pipeline will resume when approval is received via API
    return {"status": PipelineStatus.AWAITING_SCRIPT_APPROVAL}


@agent("generate_video")
async def generate_video(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Generate video using HeyGen.

    Config params:
        - aspect_ratio: Video aspect ratio (default: "9:16")
        - background_color: Background color (default: "#1a1a2e")
        - max_wait_seconds: Max wait for generation (default: 600)
    """
    heygen = get_heygen_client()

    # Get video params from config
    aspect_ratio = "9:16"
    background_color = "#1a1a2e"
    max_wait_seconds = 600

    if config and config.params:
        aspect_ratio = config.params.get("aspect_ratio", aspect_ratio)
        background_color = config.params.get("background_color", background_color)
        max_wait_seconds = config.params.get("max_wait_seconds", max_wait_seconds)

    # Get language-specific locale for voice
    language_config = state.get("language_config", {})
    locale = language_config.get("heygen_locale", "en-SG")
    speed = language_config.get("speech_speed", 1.0)

    try:
        # Generate video with locale
        result = await heygen.generate_video(
            script=state["full_script"],
            aspect_ratio=aspect_ratio,
            background_color=background_color,
            locale=locale,
            speed=speed,
        )

        video_id = result["video_id"]

        # Wait for video completion
        status = await heygen.wait_for_video(video_id, timeout_seconds=max_wait_seconds)

        return {
            "heygen_video_id": video_id,
            "video_url": status["video_url"],
            "video_duration": status.get("duration"),
            "status": PipelineStatus.AWAITING_VIDEO_APPROVAL,
        }
    except Exception as e:
        return {
            "error": f"Video generation failed: {str(e)}",
            "status": PipelineStatus.FAILED,
        }


@agent("video_approval")
async def video_approval_gate(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Human approval gate for video.

    Config params:
        - notification_channels: List of channels to notify
    """
    notification = get_notification_service()

    # Send notification
    await notification.send_video_approval_request(
        thread_id=state["thread_id"],
        video_url=state.get("video_url", ""),
        caption=state.get("caption", ""),
    )

    return {"status": PipelineStatus.AWAITING_VIDEO_APPROVAL}


@agent("publish")
async def publish_to_social(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """Publish video to social media platforms via Blotato.

    Config params:
        - platforms: List of platforms to publish to
        - schedule_delay_minutes: Delay before publishing (0 = immediate)
    """
    blotato = get_blotato_client()

    # Get platforms from config
    platforms = ["instagram", "tiktok", "youtube", "linkedin"]
    if config and config.params:
        platforms = config.params.get("platforms", platforms)

    try:
        results = await blotato.schedule_multi_platform(
            video_url=state["video_url"],
            caption=state["caption"],
            platforms=platforms,
            hashtags=MAYA_HASHTAGS,
        )

        return {
            "post_results": results,
            "status": PipelineStatus.COMPLETED,
        }
    except Exception as e:
        return {
            "error": f"Publishing failed: {str(e)}",
            "status": PipelineStatus.FAILED,
        }


# Conditional routing functions
def should_continue_after_aggregation(state: MayaState) -> str:
    if state.get("error"):
        return "end"
    return "deduplicate"


def should_continue_after_scripts(state: MayaState) -> str:
    if state.get("error"):
        return "end"
    return "script_approval"


def route_after_script_approval(state: MayaState) -> str:
    if state.get("script_approved"):
        return "generate_video"
    elif state.get("script_feedback"):
        return "revise_scripts"
    return "wait_approval"


def route_after_video_approval(state: MayaState) -> str:
    if state.get("video_approved"):
        return "publish"
    return "wait_approval"

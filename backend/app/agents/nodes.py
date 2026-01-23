"""Node functions for the Maya LangGraph pipeline."""

import asyncio
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.models.schemas import PipelineStatus, NewsArticle
from app.services.news_aggregator import get_news_aggregator
from app.services.notification import get_notification_service
from app.integrations.heygen import get_heygen_client
from app.integrations.blotato import get_blotato_client, MAYA_HASHTAGS
from .prompts import (
    MAYA_PERSONA,
    LOCAL_NEWS_PROMPT,
    BUSINESS_NEWS_PROMPT,
    AI_TECH_NEWS_PROMPT,
    CATEGORIZATION_PROMPT,
    RELEVANCE_PROMPT,
    CAPTION_PROMPT,
)
from .state import MayaState


def get_llm():
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
    )


async def aggregate_news(state: MayaState) -> Dict[str, Any]:
    """Aggregate news from all sources."""
    aggregator = get_news_aggregator()

    try:
        articles = await aggregator.aggregate_all(days=7)

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


async def deduplicate_articles(state: MayaState) -> Dict[str, Any]:
    """Remove duplicate articles using semantic similarity."""
    articles = state["raw_articles"]

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


async def categorize_articles(state: MayaState) -> Dict[str, Any]:
    """Categorize articles into local, business, and AI news."""
    articles = state["raw_articles"]
    llm = get_llm()

    local_news = []
    business_news = []
    ai_news = []

    for article in articles[:50]:  # Limit to top 50 for cost
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

    return {
        "local_news": local_news[:15],
        "business_news": business_news[:15],
        "ai_news": ai_news[:15],
        "status": PipelineStatus.SYNTHESIZING,
    }


async def synthesize_local(state: MayaState) -> Dict[str, Any]:
    """Synthesize local and international news script."""
    articles = state["local_news"]
    llm = get_llm()

    # Format articles for prompt
    articles_text = "\n\n".join([
        f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n{a.get('content', '')[:400]}"
        for a in articles[:10]
    ])

    prompt = LOCAL_NEWS_PROMPT.replace(
        "${MAYA_PERSONA}", MAYA_PERSONA
    ).replace(
        "${articles}", articles_text
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"local_script": response.content}


async def synthesize_business(state: MayaState) -> Dict[str, Any]:
    """Synthesize business news script."""
    articles = state["business_news"]
    llm = get_llm()

    articles_text = "\n\n".join([
        f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n{a.get('content', '')[:400]}"
        for a in articles[:10]
    ])

    prompt = BUSINESS_NEWS_PROMPT.replace(
        "${MAYA_PERSONA}", MAYA_PERSONA
    ).replace(
        "${articles}", articles_text
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"business_script": response.content}


async def synthesize_ai(state: MayaState) -> Dict[str, Any]:
    """Synthesize AI and tech news script."""
    articles = state["ai_news"]
    llm = get_llm()

    articles_text = "\n\n".join([
        f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n{a.get('content', '')[:400]}"
        for a in articles[:10]
    ])

    prompt = AI_TECH_NEWS_PROMPT.replace(
        "${MAYA_PERSONA}", MAYA_PERSONA
    ).replace(
        "${articles}", articles_text
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {"ai_script": response.content}


async def generate_scripts(state: MayaState) -> Dict[str, Any]:
    """Combine individual scripts into full script."""
    local = state.get("local_script", "")
    business = state.get("business_script", "")
    ai = state.get("ai_script", "")

    full_script = f"""[INTRO]
Good evening, everyone! I'm Maya, and welcome to your weekly news roundup. Let's dive into what happened this week across Southeast Asia and beyond.

[LOCAL & INTERNATIONAL NEWS]
{local}

[BUSINESS NEWS]
{business}

[AI & TECH NEWS]
{ai}

[OUTRO]
And that's your weekly roundup! Thanks for watching. I'm Maya, and I'll see you next week. Stay informed, stay curious!
"""

    # Generate caption
    llm = get_llm()
    caption_prompt = CAPTION_PROMPT.replace(
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


async def script_approval_gate(state: MayaState) -> Dict[str, Any]:
    """Human approval gate for scripts."""
    notification = get_notification_service()

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


async def generate_video(state: MayaState) -> Dict[str, Any]:
    """Generate video using HeyGen."""
    heygen = get_heygen_client()

    try:
        # Generate video
        result = await heygen.generate_video(
            script=state["full_script"],
            aspect_ratio="9:16",  # Vertical for social
        )

        video_id = result["video_id"]

        # Wait for video completion
        status = await heygen.wait_for_video(video_id, timeout_seconds=600)

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


async def video_approval_gate(state: MayaState) -> Dict[str, Any]:
    """Human approval gate for video."""
    notification = get_notification_service()

    # Send notification
    await notification.send_video_approval_request(
        thread_id=state["thread_id"],
        video_url=state.get("video_url", ""),
        caption=state.get("caption", ""),
    )

    return {"status": PipelineStatus.AWAITING_VIDEO_APPROVAL}


async def publish_to_social(state: MayaState) -> Dict[str, Any]:
    """Publish video to social media platforms via Blotato."""
    blotato = get_blotato_client()

    try:
        results = await blotato.schedule_multi_platform(
            video_url=state["video_url"],
            caption=state["caption"],
            platforms=["instagram", "tiktok", "youtube", "linkedin"],
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

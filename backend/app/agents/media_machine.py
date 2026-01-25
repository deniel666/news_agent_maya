"""Media Machine Agent Implementations.

This module implements the 8 professional media roles as LangGraph nodes.
Each agent is a specialized processor in the content creation pipeline.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.languages import get_language_config, TARGET_AUDIENCE
from app.models.schemas import PipelineStatus
from app.services.news_aggregator import get_news_aggregator
from app.services.notification import get_notification_service
from app.integrations.heygen import get_heygen_client
from app.integrations.blotato import get_blotato_client, MAYA_HASHTAGS

from .config import AgentConfig, get_config_manager
from .registry import agent, get_registry, with_mcp_tools
from .state import MayaState
from .prompts import (
    get_maya_persona,
    get_local_news_prompt,
    get_business_news_prompt,
    get_ai_tech_news_prompt,
    get_caption_prompt,
    CATEGORIZATION_PROMPT,
    RELEVANCE_PROMPT,
)


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


# =============================================================================
# 1. RESEARCH AGENT - "The Scout"
# =============================================================================

RESEARCH_SYSTEM_PROMPT = """You are a news research specialist focused on Malaysian business content.
Your job is to identify and score articles for relevance to Malaysian SME owners.

Target Audience: {target_audience}

For each article, consider:
- Direct relevance to Malaysian SMEs
- Practical applicability (can they act on this?)
- Timeliness and significance
- Regional business impact

Output a relevance score from 0.0 to 1.0."""


@agent("research")
@with_mcp_tools
async def research_agent(
    state: MayaState,
    config: AgentConfig = None,
    mcp_tools: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    The Scout - Aggregates news from all configured sources.

    Responsibilities:
    - Monitor RSS, Telegram, and Twitter sources
    - Extract and normalize article data
    - Initial relevance scoring for Malaysian SME audience
    - Detect duplicates across sources

    MCP Tools Used (when configured):
    - get_trending_keywords: Get Malaysia trending topics (Google Trends MCP)
    - get_news_by_location: Get news by location (Google Trends MCP)
    - get_news_by_topic: Get news by topic (Google Trends MCP)
    """
    raw_articles = []
    trending_topics = []
    mcp_used = False

    # Get config params
    lookback_days = 7
    max_articles = 200
    if config and config.params:
        lookback_days = config.params.get("lookback_days", 7)
        max_articles = config.params.get("max_articles", 200)

    # 1. Try MCP tools first (Google News Trends)
    if mcp_tools and config and config.prefers_mcp():
        try:
            # Get Malaysia trending topics
            if "get_trending_keywords" in mcp_tools:
                trending_result = await mcp_tools["get_trending_keywords"](geo="MY")
                if trending_result.get("success"):
                    mcp_used = True
                    for item in trending_result.get("content", []):
                        if isinstance(item, dict) and item.get("text"):
                            trending_topics.append(item["text"])
                        elif isinstance(item, str):
                            trending_topics.append(item)

            # Get news by location (Malaysia)
            if "get_news_by_location" in mcp_tools:
                location_news = await mcp_tools["get_news_by_location"](
                    location="Malaysia",
                    summarize=False
                )
                if location_news.get("success"):
                    mcp_used = True
                    for item in location_news.get("content", []):
                        if isinstance(item, dict):
                            raw_articles.append({
                                "id": f"article_{len(raw_articles)}",
                                "source_type": "google_trends_mcp",
                                "source_name": "Google News",
                                "title": item.get("title", ""),
                                "content": item.get("summary", item.get("description", "")),
                                "url": item.get("link", item.get("url", "")),
                                "published_at": item.get("published", None),
                                "fetched_at": datetime.utcnow().isoformat(),
                            })

            # Get business news
            if "get_news_by_topic" in mcp_tools:
                business_news = await mcp_tools["get_news_by_topic"](
                    topic="BUSINESS"
                )
                if business_news.get("success"):
                    mcp_used = True
                    for item in business_news.get("content", []):
                        if isinstance(item, dict):
                            # Avoid duplicates
                            url = item.get("link", item.get("url", ""))
                            if not any(a.get("url") == url for a in raw_articles):
                                raw_articles.append({
                                    "id": f"article_{len(raw_articles)}",
                                    "source_type": "google_trends_mcp",
                                    "source_name": "Google News Business",
                                    "title": item.get("title", ""),
                                    "content": item.get("summary", item.get("description", "")),
                                    "url": url,
                                    "published_at": item.get("published", None),
                                    "fetched_at": datetime.utcnow().isoformat(),
                                })

                # Get technology news
                tech_news = await mcp_tools["get_news_by_topic"](
                    topic="TECHNOLOGY"
                )
                if tech_news.get("success"):
                    for item in tech_news.get("content", []):
                        if isinstance(item, dict):
                            url = item.get("link", item.get("url", ""))
                            if not any(a.get("url") == url for a in raw_articles):
                                raw_articles.append({
                                    "id": f"article_{len(raw_articles)}",
                                    "source_type": "google_trends_mcp",
                                    "source_name": "Google News Technology",
                                    "title": item.get("title", ""),
                                    "content": item.get("summary", item.get("description", "")),
                                    "url": url,
                                    "published_at": item.get("published", None),
                                    "fetched_at": datetime.utcnow().isoformat(),
                                })

        except Exception as e:
            # Log error but continue to fallback
            import logging
            logging.getLogger(__name__).warning(f"MCP research failed: {e}")

    # 2. Fallback to built-in aggregator if MCP didn't provide enough articles
    if config is None or config.should_fallback_to_builtin() or len(raw_articles) < 10:
        try:
            aggregator = get_news_aggregator()
            articles = await aggregator.aggregate_all(days=lookback_days)

            # Add articles from aggregator, avoiding duplicates
            for i, a in enumerate(articles):
                if len(raw_articles) >= max_articles:
                    break
                # Check for duplicate URLs
                if not any(r.get("url") == a.url for r in raw_articles):
                    raw_articles.append({
                        "id": f"article_{len(raw_articles)}",
                        "source_type": a.source_type,
                        "source_name": a.source_name,
                        "title": a.title,
                        "content": a.content,
                        "url": a.url,
                        "published_at": a.published_at.isoformat() if a.published_at else None,
                        "fetched_at": datetime.utcnow().isoformat(),
                    })
        except Exception as e:
            if not raw_articles:
                return {
                    "error": f"Research failed: {str(e)}",
                    "status": PipelineStatus.FAILED,
                }

    # Limit to max_articles
    raw_articles = raw_articles[:max_articles]

    return {
        "raw_articles": raw_articles,
        "trending_topics": trending_topics,
        "research_metadata": {
            "total_fetched": len(raw_articles),
            "mcp_used": mcp_used,
            "trending_topics_count": len(trending_topics),
            "sources_checked": list(set(a.get("source_name", "") for a in raw_articles)),
            "lookback_days": lookback_days,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "status": PipelineStatus.CATEGORIZING,
    }


# =============================================================================
# 2. EDITOR AGENT - "The Curator"
# =============================================================================

EDITOR_SYSTEM_PROMPT = """You are the Editorial Director for Maya, an AI news anchor serving Malaysian SME owners.

Your job is to:
1. Evaluate each article's newsworthiness for Malaysian SMEs
2. Identify the "so what" angle - why should a kedai owner care?
3. Categorize into: local (regional news), business (economics, policy), ai_tech (tools, digital)
4. Rank stories by priority

Target Audience: {target_audience}

PRIORITIZE stories about:
- Government policies affecting small businesses
- New tools or platforms SMEs can use
- Cost changes (fuel, supplies, labor)
- Success stories of Malaysian entrepreneurs
- Practical AI applications for non-technical users

DEPRIORITIZE:
- Enterprise-only news
- Highly technical content
- Pure entertainment
- Non-actionable information"""


EDITORIAL_ANGLE_PROMPT = """For this article, identify the "so what" angle for Malaysian SME owners.

Article:
Title: {title}
Content: {content}

Output a single sentence explaining why a kedai owner, restaurant owner, or small service provider should care about this story. Focus on practical impact.

Angle:"""


@agent("editor")
async def editor_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Curator - Decides what's newsworthy and structures the briefing.

    Responsibilities:
    - Deduplicate semantically similar articles
    - Score newsworthiness for Malaysian SME audience
    - Categorize into segments
    - Identify editorial angles
    - Flag stories for fact-checking
    """
    articles = state["raw_articles"]
    llm = get_llm(config)
    language_config = state.get("language_config", {})

    # Get config params
    max_items = 100
    dedup_threshold = 0.85
    max_per_segment = 15

    if config:
        max_items = config.max_items or 100
        if config.params:
            dedup_threshold = config.params.get("deduplication_threshold", 0.85)
            max_per_segment = config.params.get("max_stories_per_segment", 15)

    # Step 1: Deduplicate by title similarity
    seen_titles = set()
    unique_articles = []
    for article in articles:
        title = (article.get("title") or article.get("content", "")[:100]).lower()
        title_key = title[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)

    # Step 2: Categorize and score
    local_news = []
    business_news = []
    ai_news = []
    editorial_angles = {}

    for article in unique_articles[:max_items]:
        try:
            # Categorize
            cat_prompt = CATEGORIZATION_PROMPT.replace(
                "${title}", article.get("title") or ""
            ).replace(
                "${content}", (article.get("content") or "")[:500]
            ).replace(
                "${source}", article.get("source_name", "")
            )

            cat_response = await llm.ainvoke([HumanMessage(content=cat_prompt)])
            category = cat_response.content.strip().lower()

            # Score relevance
            rel_prompt = RELEVANCE_PROMPT.replace(
                "${title}", article.get("title") or ""
            ).replace(
                "${content}", (article.get("content") or "")[:500]
            ).replace(
                "${source}", article.get("source_name", "")
            )

            rel_response = await llm.ainvoke([HumanMessage(content=rel_prompt)])
            try:
                relevance_score = float(rel_response.content.strip())
            except ValueError:
                relevance_score = 0.5

            article["relevance_score"] = relevance_score
            article["category"] = category

            # Generate editorial angle for high-relevance stories
            if relevance_score >= 0.6:
                angle_prompt = EDITORIAL_ANGLE_PROMPT.format(
                    title=article.get("title", ""),
                    content=(article.get("content") or "")[:400],
                )
                angle_response = await llm.ainvoke([HumanMessage(content=angle_prompt)])
                editorial_angles[article["id"]] = angle_response.content.strip()

            # Assign to segment
            if category == "local":
                local_news.append(article)
            elif category == "business":
                business_news.append(article)
            elif category in ["ai_tech", "ai", "tech"]:
                ai_news.append(article)

        except Exception as e:
            # Default to local if categorization fails
            article["category"] = "local"
            article["relevance_score"] = 0.4
            local_news.append(article)

    # Sort each segment by relevance and limit
    local_news = sorted(local_news, key=lambda x: x.get("relevance_score", 0), reverse=True)[:max_per_segment]
    business_news = sorted(business_news, key=lambda x: x.get("relevance_score", 0), reverse=True)[:max_per_segment]
    ai_news = sorted(ai_news, key=lambda x: x.get("relevance_score", 0), reverse=True)[:max_per_segment]

    return {
        "local_news": local_news,
        "business_news": business_news,
        "ai_news": ai_news,
        "editorial_angles": editorial_angles,
        "editor_metadata": {
            "total_processed": len(unique_articles),
            "local_count": len(local_news),
            "business_count": len(business_news),
            "ai_count": len(ai_news),
            "angles_generated": len(editorial_angles),
        },
        "status": PipelineStatus.SYNTHESIZING,
    }


# =============================================================================
# 3. WRITER AGENTS - "The Voice"
# =============================================================================

@agent("writer_local")
async def writer_local_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Voice - Writes local & international news in Maya's style.
    """
    articles = state.get("local_news", [])
    editorial_angles = state.get("editorial_angles", {})
    language_config = state.get("language_config")
    llm = get_llm(config)

    max_items = 10
    if config:
        max_items = config.max_items or 10

    # Build articles text with editorial angles
    articles_parts = []
    for a in articles[:max_items]:
        angle = editorial_angles.get(a.get("id"), "")
        angle_note = f"\n[SME ANGLE: {angle}]" if angle else ""
        articles_parts.append(
            f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n"
            f"{a.get('content', '')[:400]}{angle_note}"
        )

    articles_text = "\n\n".join(articles_parts)

    prompt = get_local_news_prompt(language_config).replace("${articles}", articles_text)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    # Estimate duration (avg 150 words per minute)
    word_count = len(response.content.split())
    estimated_duration = (word_count / 150) * 60

    return {
        "local_script": response.content,
        "local_metadata": {
            "word_count": word_count,
            "estimated_duration_seconds": estimated_duration,
            "articles_used": len(articles[:max_items]),
        },
    }


@agent("writer_business")
async def writer_business_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Voice - Writes business news in Maya's style.
    """
    articles = state.get("business_news", [])
    editorial_angles = state.get("editorial_angles", {})
    language_config = state.get("language_config")
    llm = get_llm(config)

    max_items = 10
    if config:
        max_items = config.max_items or 10

    articles_parts = []
    for a in articles[:max_items]:
        angle = editorial_angles.get(a.get("id"), "")
        angle_note = f"\n[SME ANGLE: {angle}]" if angle else ""
        articles_parts.append(
            f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n"
            f"{a.get('content', '')[:400]}{angle_note}"
        )

    articles_text = "\n\n".join(articles_parts)

    prompt = get_business_news_prompt(language_config).replace("${articles}", articles_text)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    word_count = len(response.content.split())
    estimated_duration = (word_count / 150) * 60

    return {
        "business_script": response.content,
        "business_metadata": {
            "word_count": word_count,
            "estimated_duration_seconds": estimated_duration,
            "articles_used": len(articles[:max_items]),
        },
    }


@agent("writer_ai")
async def writer_ai_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Voice - Writes AI & tech news in Maya's style.
    """
    articles = state.get("ai_news", [])
    editorial_angles = state.get("editorial_angles", {})
    language_config = state.get("language_config")
    llm = get_llm(config)

    max_items = 10
    if config:
        max_items = config.max_items or 10

    articles_parts = []
    for a in articles[:max_items]:
        angle = editorial_angles.get(a.get("id"), "")
        angle_note = f"\n[SME ANGLE: {angle}]" if angle else ""
        articles_parts.append(
            f"**{a.get('title', 'Untitled')}** ({a.get('source_name', 'Unknown')})\n"
            f"{a.get('content', '')[:400]}{angle_note}"
        )

    articles_text = "\n\n".join(articles_parts)

    prompt = get_ai_tech_news_prompt(language_config).replace("${articles}", articles_text)
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    word_count = len(response.content.split())
    estimated_duration = (word_count / 150) * 60

    return {
        "ai_script": response.content,
        "ai_metadata": {
            "word_count": word_count,
            "estimated_duration_seconds": estimated_duration,
            "articles_used": len(articles[:max_items]),
        },
    }


# =============================================================================
# 4. FACT-CHECKER AGENT - "The Verifier"
# =============================================================================

FACT_CHECK_PROMPT = """You are a fact-checker for a news program targeting Malaysian SME owners.

Review this script segment and identify any claims that need verification:

SCRIPT:
{script}

For each claim found, output:
1. The claim text
2. Verification status: VERIFIED, UNVERIFIED, or NEEDS_SOFTENING
3. Confidence (0.0-1.0)
4. Suggested correction if needed

Focus on:
- Statistics and numbers
- Company names and titles
- Policy or regulatory information
- Dates and timelines

Output as JSON list. If no issues found, output empty list []."""


@agent("fact_checker")
async def fact_checker_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Verifier - Checks facts, statistics, and attributions.

    Responsibilities:
    - Verify statistics and numbers
    - Check attributions
    - Flag unverifiable claims
    - Suggest corrections
    """
    local_script = state.get("local_script", "")
    business_script = state.get("business_script", "")
    ai_script = state.get("ai_script", "")

    llm = get_llm(config)
    all_flagged_claims = []
    verification_reports = {}

    # Check each segment
    for segment_name, script in [
        ("local", local_script),
        ("business", business_script),
        ("ai_tech", ai_script),
    ]:
        if not script:
            continue

        try:
            prompt = FACT_CHECK_PROMPT.format(script=script)
            response = await llm.ainvoke([HumanMessage(content=prompt)])

            # Try to parse as JSON
            content = response.content.strip()
            if content.startswith("["):
                import json
                try:
                    claims = json.loads(content)
                    verification_reports[segment_name] = {
                        "claims_found": len(claims),
                        "claims": claims,
                        "confidence": 1.0 if not claims else 0.8,
                    }
                    all_flagged_claims.extend(claims)
                except json.JSONDecodeError:
                    verification_reports[segment_name] = {
                        "claims_found": 0,
                        "raw_response": content,
                        "confidence": 0.9,
                    }
            else:
                verification_reports[segment_name] = {
                    "claims_found": 0,
                    "note": "No issues found",
                    "confidence": 0.95,
                }

        except Exception as e:
            verification_reports[segment_name] = {
                "error": str(e),
                "confidence": 0.5,
            }

    # Calculate overall confidence
    confidences = [r.get("confidence", 0.5) for r in verification_reports.values()]
    overall_confidence = sum(confidences) / len(confidences) if confidences else 0.5

    return {
        "verification_report": {
            "segments": verification_reports,
            "total_claims_flagged": len(all_flagged_claims),
            "overall_confidence": overall_confidence,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "flagged_claims": all_flagged_claims,
    }


# =============================================================================
# 5. SCRIPT ASSEMBLER
# =============================================================================

@agent("script_assembler")
async def script_assembler_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    Combines segment scripts into a full briefing with intro/outro.
    Also generates social media caption.
    """
    local_script = state.get("local_script", "")
    business_script = state.get("business_script", "")
    ai_script = state.get("ai_script", "")
    language_config = state.get("language_config")

    llm = get_llm(config)

    # Get enabled segments in order
    config_manager = get_config_manager()
    segments = config_manager.list_enabled_segments()

    # Build script sections
    sections = []
    for segment in segments:
        if segment.id == "local" and local_script:
            sections.append(f"[LOCAL & INTERNATIONAL NEWS]\n{local_script}")
        elif segment.id == "business" and business_script:
            sections.append(f"[BUSINESS NEWS]\n{business_script}")
        elif segment.id == "ai_tech" and ai_script:
            sections.append(f"[AI & TECH NEWS]\n{ai_script}")

    script_body = "\n\n".join(sections)

    full_script = f"""[INTRO]
Good evening, everyone! I'm Maya, and welcome to your weekly news roundup. Let's dive into what matters for your business this week.

{script_body}

[OUTRO]
And that's your weekly roundup! Thanks for watching. I'm Maya, and I'll see you next week. Stay informed, stay ahead!
"""

    # Generate caption
    caption_prompt = get_caption_prompt(language_config).replace(
        "${local_summary}", local_script[:200] if local_script else "Local news"
    ).replace(
        "${business_summary}", business_script[:200] if business_script else "Business updates"
    ).replace(
        "${ai_summary}", ai_script[:200] if ai_script else "Tech news"
    ).replace(
        "${week_number}", str(state["week_number"])
    ).replace(
        "${year}", str(state["year"])
    )

    caption_response = await llm.ainvoke([HumanMessage(content=caption_prompt)])

    # Calculate total duration
    total_words = len(full_script.split())
    total_duration = (total_words / 150) * 60

    return {
        "full_script": full_script,
        "caption": caption_response.content,
        "script_metadata": {
            "total_word_count": total_words,
            "estimated_duration_seconds": total_duration,
            "segments_included": [s.id for s in segments],
        },
        "status": PipelineStatus.AWAITING_SCRIPT_APPROVAL,
    }


# =============================================================================
# 6. LOCALIZATION AGENT - "The Adapter"
# =============================================================================

LOCALIZATION_PROMPT = """You are a localization specialist for Maya, an AI news anchor.

Source Language: {source_lang}
Target Language: {target_lang}

LOCALIZATION RULES for {target_lang}:
{language_instructions}

SOURCE SCRIPT:
{script}

INSTRUCTIONS:
1. Translate the content while maintaining Maya's warm, professional voice
2. Keep technical terms and brand names in English if that's natural
3. Use natural code-switching where appropriate
4. Adapt monetary examples to RM context
5. Localize cultural references

OUTPUT the localized script:"""


@agent("localization")
async def localization_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Adapter - Handles translation and cultural adaptation.

    Only runs if target language differs from source or if multi-language output is needed.
    """
    full_script = state.get("full_script", "")
    source_language = state.get("language_code", "en-SG")
    language_config = state.get("language_config", {})

    # For now, if the script is already in the target language, just pass through
    # Future: Generate additional language versions

    localized_scripts = {
        source_language: full_script,
    }

    # Check if we need additional localizations
    # This could be configured to generate ms-MY version automatically
    requires_native_review = language_config.get("requires_external_review", False)

    return {
        "localized_scripts": localized_scripts,
        "primary_language": source_language,
        "localization_metadata": {
            "source_language": source_language,
            "languages_generated": list(localized_scripts.keys()),
            "requires_native_review": requires_native_review,
        },
    }


# =============================================================================
# 7. QUALITY CONTROL GATE
# =============================================================================

@agent("quality_control")
async def quality_control_gate(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    Human approval checkpoint for scripts.
    Sends notification and waits for approval via API.
    """
    notification = get_notification_service()

    # Get notification channels from config
    channels = ["slack", "telegram"]
    if config and config.params:
        channels = config.params.get("notification_channels", channels)

    # Send notification with all relevant info
    await notification.send_script_approval_request(
        thread_id=state["thread_id"],
        scripts={
            "local": state.get("local_script", ""),
            "business": state.get("business_script", ""),
            "ai": state.get("ai_script", ""),
            "full": state.get("full_script", ""),
        },
        week_number=state["week_number"],
        year=state["year"],
        metadata={
            "verification_report": state.get("verification_report"),
            "flagged_claims": state.get("flagged_claims", []),
            "estimated_duration": state.get("script_metadata", {}).get("estimated_duration_seconds"),
        },
    )

    return {"status": PipelineStatus.AWAITING_SCRIPT_APPROVAL}


# =============================================================================
# 8. PRODUCER AGENT - "The Director"
# =============================================================================

@agent("producer")
async def producer_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Director - Orchestrates video production with HeyGen.
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
            "producer_metadata": {
                "aspect_ratio": aspect_ratio,
                "locale": locale,
                "generation_time": datetime.utcnow().isoformat(),
            },
            "status": PipelineStatus.AWAITING_VIDEO_APPROVAL,
        }
    except Exception as e:
        return {
            "error": f"Video production failed: {str(e)}",
            "status": PipelineStatus.FAILED,
        }


# =============================================================================
# 9. VIDEO APPROVAL GATE
# =============================================================================

@agent("video_approval")
async def video_approval_gate(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    Human approval checkpoint for video.
    """
    notification = get_notification_service()

    await notification.send_video_approval_request(
        thread_id=state["thread_id"],
        video_url=state.get("video_url", ""),
        caption=state.get("caption", ""),
        metadata={
            "duration": state.get("video_duration"),
            "locale": state.get("language_config", {}).get("heygen_locale"),
        },
    )

    return {"status": PipelineStatus.AWAITING_VIDEO_APPROVAL}


# =============================================================================
# 10. SOCIAL MEDIA AGENT - "The Promoter"
# =============================================================================

PLATFORM_CAPTION_PROMPT = """Generate a {platform}-optimized caption for this video.

Video Summary:
{summary}

Original Caption:
{caption}

PLATFORM-SPECIFIC RULES for {platform}:
{platform_rules}

Output ONLY the caption text (no labels or formatting):"""

PLATFORM_RULES = {
    "instagram": """
- Max 2,200 characters but keep under 300 for visibility
- Include relevant emojis
- Use 5-15 hashtags at the end
- Include call-to-action
- Use line breaks for readability""",

    "tiktok": """
- Max 150 characters
- Catchy, hook-driven first line
- 3-5 hashtags only
- Informal, trendy tone
- Include trending hashtags if relevant""",

    "youtube": """
- This is for the video description
- Include timestamps if multiple topics
- Include links to mentioned resources
- Use keywords naturally for SEO
- Keep first 2 lines compelling (shown in preview)""",

    "linkedin": """
- Professional but approachable tone
- Start with a hook or question
- Include business insights
- Minimal hashtags (3-5 max)
- Include call-to-action for engagement""",
}


@agent("social_media")
async def social_media_agent(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    The Promoter - Handles platform-specific distribution.
    """
    blotato = get_blotato_client()
    llm = get_llm(config)

    video_url = state.get("video_url", "")
    base_caption = state.get("caption", "")
    language_config = state.get("language_config", {})

    # Get platforms from config
    platforms = ["instagram", "tiktok", "youtube", "linkedin"]
    generate_custom_captions = True

    if config and config.params:
        platforms = config.params.get("platforms", platforms)
        generate_custom_captions = config.params.get("generate_platform_captions", True)

    # Generate platform-specific captions
    platform_captions = {}
    for platform in platforms:
        if generate_custom_captions and platform in PLATFORM_RULES:
            try:
                prompt = PLATFORM_CAPTION_PROMPT.format(
                    platform=platform,
                    summary=state.get("full_script", "")[:500],
                    caption=base_caption,
                    platform_rules=PLATFORM_RULES[platform],
                )
                response = await llm.ainvoke([HumanMessage(content=prompt)])
                platform_captions[platform] = response.content.strip()
            except Exception:
                platform_captions[platform] = base_caption
        else:
            platform_captions[platform] = base_caption

    # Schedule posts
    try:
        results = await blotato.schedule_multi_platform(
            video_url=video_url,
            caption=base_caption,  # Blotato may override with platform-specific
            platforms=platforms,
            hashtags=MAYA_HASHTAGS,
        )

        return {
            "post_results": results,
            "platform_captions": platform_captions,
            "social_metadata": {
                "platforms_posted": platforms,
                "captions_generated": list(platform_captions.keys()),
                "timestamp": datetime.utcnow().isoformat(),
            },
            "status": PipelineStatus.COMPLETED,
        }
    except Exception as e:
        return {
            "error": f"Social publishing failed: {str(e)}",
            "status": PipelineStatus.FAILED,
        }


# =============================================================================
# 11. ANALYTICS AGENT - "The Analyst"
# =============================================================================

@agent("analytics")
@with_mcp_tools
async def analytics_agent(
    state: MayaState,
    config: AgentConfig = None,
    mcp_tools: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    The Analyst - Tracks performance and provides feedback.

    MCP Tools Used (when configured):
    - get_analytics: Get platform performance metrics (Metricool MCP)
    - get_best_time_to_post: Get optimal posting times (Metricool MCP)
    - get-tiktok-profile: Get TikTok profile stats (viral.app MCP)
    - list-profile-videos: Get recent video performance (viral.app MCP)
    """
    post_results = state.get("post_results", {})
    thread_id = state.get("thread_id", "")
    mcp_used = False

    # Initialize platform performance data
    platform_performance = {}
    optimal_posting_times = {}
    recommendations = []

    # 1. Try MCP tools for analytics
    if mcp_tools and config and config.prefers_mcp():
        try:
            # Get platform analytics from Metricool
            if "get_analytics" in mcp_tools:
                analytics_result = await mcp_tools["get_analytics"](days=7)
                if analytics_result.get("success"):
                    mcp_used = True
                    platform_performance = analytics_result.get("content", {})

            # Get best posting times
            if "get_best_time_to_post" in mcp_tools:
                times_result = await mcp_tools["get_best_time_to_post"]()
                if times_result.get("success"):
                    mcp_used = True
                    optimal_posting_times = times_result.get("content", {})

            # Get TikTok-specific analytics from viral.app
            if "get-tiktok-profile" in mcp_tools:
                tiktok_result = await mcp_tools["get-tiktok-profile"]()
                if tiktok_result.get("success"):
                    mcp_used = True
                    platform_performance["tiktok_profile"] = tiktok_result.get("content", {})

            # Get recent video performance
            if "list-profile-videos" in mcp_tools:
                videos_result = await mcp_tools["list-profile-videos"](limit=10)
                if videos_result.get("success"):
                    mcp_used = True
                    platform_performance["recent_videos"] = videos_result.get("content", [])

                    # Generate recommendations based on video performance
                    videos = videos_result.get("content", [])
                    if videos:
                        avg_views = sum(v.get("views", 0) for v in videos) / len(videos)
                        avg_engagement = sum(v.get("engagement_rate", 0) for v in videos) / len(videos)
                        recommendations.append({
                            "type": "performance_benchmark",
                            "message": f"Average views: {avg_views:.0f}, Average engagement: {avg_engagement:.2%}",
                        })

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"MCP analytics failed: {e}")

    # Build analytics report
    analytics_report = {
        "thread_id": thread_id,
        "week_number": state.get("week_number"),
        "year": state.get("year"),
        "language": state.get("language_code", "en-SG"),
        "content_metrics": {
            "local_articles_used": len(state.get("local_news", [])),
            "business_articles_used": len(state.get("business_news", [])),
            "ai_articles_used": len(state.get("ai_news", [])),
            "script_word_count": state.get("script_metadata", {}).get("total_word_count"),
            "video_duration": state.get("video_duration"),
            "trending_topics_used": len(state.get("trending_topics", [])),
        },
        "quality_metrics": {
            "verification_confidence": state.get("verification_report", {}).get("overall_confidence"),
            "claims_flagged": len(state.get("flagged_claims", [])),
        },
        "distribution": {
            "platforms": list(state.get("platform_captions", {}).keys()),
            "post_count": len(post_results) if isinstance(post_results, dict) else 0,
        },
        # MCP-enhanced metrics
        "platform_performance": platform_performance,
        "optimal_posting_times": optimal_posting_times,
        "recommendations": recommendations,
        "mcp_used": mcp_used,
        "generated_at": datetime.utcnow().isoformat(),
    }

    return {
        "analytics_report": analytics_report,
    }


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def route_after_quality_control(state: MayaState) -> str:
    """Route after script approval gate."""
    if state.get("script_approved"):
        return "producer"
    elif state.get("script_feedback"):
        return "writer_local"  # Loop back to rewrite
    return "end"


def route_after_video_approval(state: MayaState) -> str:
    """Route after video approval gate."""
    if state.get("video_approved"):
        return "social_media"
    elif state.get("video_feedback"):
        return "producer"  # Regenerate
    return "end"

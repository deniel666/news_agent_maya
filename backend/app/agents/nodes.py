"""FPF-Compliant Node Functions for the Maya LangGraph Pipeline.

Implements:
- Pattern A.1.1: Bounded Contexts (Fact Extraction vs Persona Projection)
- Pattern A.10: Evidence Graph (NewsItem with provenance)
- Pattern F.9: Brand Bridge (promotional opportunity detection)
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.models.schemas import PipelineStatus
from app.services.news_aggregator import get_news_aggregator
from app.services.notification import get_notification_service
from app.integrations.heygen import get_heygen_client
from app.integrations.blotato import get_blotato_client, MAYA_HASHTAGS
from .state import (
    MayaState,
    NewsItem,
    ExtractedFact,
    ScriptSegment,
    ScriptVersion,
    BridgeOpportunity,
    CongruenceLevel,
    SourceReliability,
)
from .prompts import (
    MAYA_PERSONA,
    FACT_EXTRACTION_PROMPT,
    PERSONA_PROJECTION_PROMPT,
    BRIDGE_DETECTION_PROMPT,
    CAPTION_PROMPT,
    CATEGORIZATION_PROMPT,
)


def get_llm(temperature: float = 0.7):
    """Get LLM instance with configurable temperature."""
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=temperature,
    )


def _determine_source_reliability(source_name: str, source_type: str) -> SourceReliability:
    """Determine source reliability tier based on source metadata."""
    tier_1_sources = {
        "reuters", "ap", "afp", "bloomberg", "cna", "channel news asia",
        "bbc", "financial times", "wall street journal", "nikkei"
    }
    tier_2_sources = {
        "straits times", "malay mail", "the star", "bernama", "techinasia",
        "tech in asia", "venturebeat", "techcrunch", "wired", "ars technica"
    }

    source_lower = source_name.lower()

    for t1 in tier_1_sources:
        if t1 in source_lower:
            return SourceReliability.TIER_1

    for t2 in tier_2_sources:
        if t2 in source_lower:
            return SourceReliability.TIER_2

    if source_type in ["telegram", "twitter", "nitter"]:
        return SourceReliability.TIER_3

    return SourceReliability.UNKNOWN


# =============================================================================
# EVIDENCE LAYER NODES (Pattern A.10)
# =============================================================================

async def aggregate_news(state: MayaState) -> Dict[str, Any]:
    """Aggregate news from all sources with full provenance tracking."""
    aggregator = get_news_aggregator()

    try:
        articles = await aggregator.aggregate_all(days=7)

        # Convert to NewsItem format with provenance
        news_items = []
        for a in articles:
            reliability = _determine_source_reliability(
                a.source_name or "",
                a.source_type or ""
            )

            # Calculate initial confidence based on source reliability
            confidence_map = {
                SourceReliability.TIER_1: 0.9,
                SourceReliability.TIER_2: 0.7,
                SourceReliability.TIER_3: 0.5,
                SourceReliability.UNKNOWN: 0.4,
            }

            news_item = NewsItem(
                id=str(uuid4()),
                source_url=a.url or "",
                source_name=a.source_name or "Unknown",
                source_type=a.source_type or "unknown",
                source_reliability=reliability,
                title=a.title or "",
                raw_content=a.content or "",
                published_at=a.published_at,
                confidence_score=confidence_map.get(reliability, 0.5),
                relevance_score=0.5,  # Will be updated during categorization
            )
            news_items.append(news_item.model_dump())

        return {
            "news_items": news_items,
            "status": PipelineStatus.CATEGORIZING,
        }
    except Exception as e:
        return {
            "error": f"Aggregation failed: {str(e)}",
            "status": PipelineStatus.FAILED,
        }


async def deduplicate_articles(state: MayaState) -> Dict[str, Any]:
    """Remove duplicate news items using semantic similarity."""
    news_items = state.get("news_items", [])

    # Simple deduplication by title similarity
    seen_titles = set()
    unique_items = []

    for item in news_items:
        title = (item.get("title") or item.get("raw_content", "")[:100]).lower()
        title_key = title[:50]

        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_items.append(item)

    return {"news_items": unique_items}


async def categorize_articles(state: MayaState) -> Dict[str, Any]:
    """Categorize news items and update their relevance scores."""
    news_items = state.get("news_items", [])
    llm = get_llm(temperature=0.3)  # Lower temperature for classification

    local_ids = []
    business_ids = []
    ai_ids = []

    for item in news_items[:50]:  # Limit for cost
        try:
            prompt = CATEGORIZATION_PROMPT.format(
                title=item.get("title", ""),
                content=(item.get("raw_content") or "")[:500],
                source=item.get("source_name", ""),
            )

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            category = response.content.strip().lower()

            # Update item category
            item["category"] = category

            # Add to appropriate list
            item_id = item.get("id")
            if category == "local":
                local_ids.append(item_id)
            elif category == "business":
                business_ids.append(item_id)
            elif category in ["ai_tech", "ai", "tech"]:
                ai_ids.append(item_id)
                item["category"] = "ai_tech"

        except Exception:
            # Default to local if categorization fails
            local_ids.append(item.get("id"))
            item["category"] = "local"

    return {
        "news_items": news_items,
        "local_news_ids": local_ids[:15],
        "business_news_ids": business_ids[:15],
        "ai_news_ids": ai_ids[:15],
        "status": PipelineStatus.SYNTHESIZING,
    }


# =============================================================================
# BRIDGE LAYER NODES (Pattern F.9)
# =============================================================================

async def detect_bridge_opportunities(state: MayaState) -> Dict[str, Any]:
    """Detect potential brand bridge opportunities in news items."""
    news_items = state.get("news_items", [])
    llm = get_llm(temperature=0.5)

    bridge_opportunities = []

    # Only check top news items from each category
    all_ids = (
        state.get("local_news_ids", [])[:3] +
        state.get("business_news_ids", [])[:3] +
        state.get("ai_news_ids", [])[:3]
    )

    for item in news_items:
        if item.get("id") not in all_ids:
            continue

        try:
            prompt = BRIDGE_DETECTION_PROMPT.format(
                title=item.get("title", ""),
                content=(item.get("raw_content") or "")[:400],
            )

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            result = response.content.strip()

            # Parse response (expected: JSON with congruence_level, hook, mention)
            try:
                bridge_data = json.loads(result)
                if bridge_data.get("congruence_level") in ["high", "medium"]:
                    opportunity = BridgeOpportunity(
                        triggering_news_item_id=item.get("id"),
                        congruence_level=CongruenceLevel(bridge_data["congruence_level"]),
                        congruence_reasoning=bridge_data.get("reasoning", ""),
                        suggested_hook=bridge_data.get("hook", ""),
                        product_mention=bridge_data.get("mention", ""),
                    )
                    bridge_opportunities.append(opportunity.model_dump())
            except (json.JSONDecodeError, KeyError):
                pass

        except Exception:
            continue

    return {"bridge_opportunities": bridge_opportunities}


async def select_best_bridge(state: MayaState) -> Dict[str, Any]:
    """Select the best bridge opportunity if any exist."""
    opportunities = state.get("bridge_opportunities", [])

    if not opportunities:
        return {"selected_bridge": None}

    # Prefer HIGH congruence, then MEDIUM
    high_congruence = [o for o in opportunities if o.get("congruence_level") == "high"]
    if high_congruence:
        return {"selected_bridge": high_congruence[0]}

    medium_congruence = [o for o in opportunities if o.get("congruence_level") == "medium"]
    if medium_congruence:
        return {"selected_bridge": medium_congruence[0]}

    return {"selected_bridge": None}


# =============================================================================
# FACT EXTRACTION LAYER (Pattern A.1.1 - Journalism Context)
# =============================================================================

async def _extract_facts_for_category(
    state: MayaState,
    category: str,
    news_ids: List[str],
) -> List[Dict[str, Any]]:
    """Extract facts from news items in a specific category.

    This is the JOURNALISM CONTEXT - no persona, no slang, just facts.
    """
    news_items = state.get("news_items", [])
    llm = get_llm(temperature=0.3)  # Low temperature for factual extraction

    # Get items for this category
    category_items = [
        item for item in news_items
        if item.get("id") in news_ids
    ][:10]

    if not category_items:
        return []

    extracted_facts = []

    for item in category_items:
        try:
            prompt = FACT_EXTRACTION_PROMPT.format(
                title=item.get("title", ""),
                content=item.get("raw_content", "")[:600],
                source_name=item.get("source_name", ""),
                source_url=item.get("source_url", ""),
            )

            response = await llm.ainvoke([HumanMessage(content=prompt)])

            # Parse facts from response (expected: JSON array of facts)
            try:
                facts_data = json.loads(response.content)
                for fact_data in facts_data[:3]:  # Max 3 facts per item
                    fact = ExtractedFact(
                        source_news_item_id=item.get("id"),
                        claim=fact_data.get("claim", ""),
                        evidence_quote=fact_data.get("evidence"),
                        confidence=fact_data.get("confidence", 0.7),
                        requires_verification=fact_data.get("needs_verification", False),
                    )
                    extracted_facts.append(fact.model_dump())
            except (json.JSONDecodeError, TypeError):
                # Fallback: treat entire response as a single fact
                fact = ExtractedFact(
                    source_news_item_id=item.get("id"),
                    claim=response.content[:500],
                    confidence=0.6,
                )
                extracted_facts.append(fact.model_dump())

        except Exception:
            continue

    return extracted_facts


async def extract_local_facts(state: MayaState) -> Dict[str, Any]:
    """Extract facts from local news items (Journalism Context)."""
    facts = await _extract_facts_for_category(
        state, "local", state.get("local_news_ids", [])
    )
    return {
        "local_facts": facts,
        "extracted_facts": facts,  # Also add to global facts list
    }


async def extract_business_facts(state: MayaState) -> Dict[str, Any]:
    """Extract facts from business news items (Journalism Context)."""
    facts = await _extract_facts_for_category(
        state, "business", state.get("business_news_ids", [])
    )
    return {
        "business_facts": facts,
        "extracted_facts": facts,
    }


async def extract_ai_facts(state: MayaState) -> Dict[str, Any]:
    """Extract facts from AI/tech news items (Journalism Context)."""
    facts = await _extract_facts_for_category(
        state, "ai_tech", state.get("ai_news_ids", [])
    )
    return {
        "ai_facts": facts,
        "extracted_facts": facts,
    }


# =============================================================================
# PERSONA PROJECTION LAYER (Pattern A.1.1 - Maya Context)
# =============================================================================

async def _project_persona_for_segment(
    state: MayaState,
    segment_type: str,
    facts: List[Dict[str, Any]],
) -> ScriptSegment:
    """Apply Maya's persona to facts for a segment.

    This is the MAYA CONTEXT - warm, SEA-friendly, with local expressions.
    """
    llm = get_llm(temperature=0.7)  # Higher temperature for creative writing
    language_code = state.get("language_code", "en-SG")

    # Format facts for the prompt
    facts_text = "\n".join([
        f"- {fact.get('claim', '')}"
        for fact in facts[:5]
    ])

    if not facts_text:
        facts_text = "No significant news this week."

    prompt = PERSONA_PROJECTION_PROMPT.format(
        segment_type=segment_type.upper().replace("_", " "),
        facts=facts_text,
        language_code=language_code,
        maya_persona=MAYA_PERSONA,
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    # Extract fact IDs for traceability
    fact_ids = [f.get("id") for f in facts if f.get("id")]

    # Estimate duration (roughly 150 words per minute)
    word_count = len(response.content.split())
    duration = int((word_count / 150) * 60)

    return ScriptSegment(
        segment_type=segment_type,
        content=response.content,
        fact_ids=fact_ids,
        estimated_duration_seconds=duration,
    )


async def project_local_persona(state: MayaState) -> Dict[str, Any]:
    """Apply Maya's persona to local news facts."""
    facts = state.get("local_facts", [])
    segment = await _project_persona_for_segment(state, "local", facts)

    return {"_local_segment": segment.model_dump()}


async def project_business_persona(state: MayaState) -> Dict[str, Any]:
    """Apply Maya's persona to business news facts."""
    facts = state.get("business_facts", [])
    segment = await _project_persona_for_segment(state, "business", facts)

    return {"_business_segment": segment.model_dump()}


async def project_ai_persona(state: MayaState) -> Dict[str, Any]:
    """Apply Maya's persona to AI/tech news facts."""
    facts = state.get("ai_facts", [])
    segment = await _project_persona_for_segment(state, "ai_tech", facts)

    return {"_ai_segment": segment.model_dump()}


# =============================================================================
# SCRIPT COMPILATION (Pattern A.15)
# =============================================================================

async def compile_full_script(state: MayaState) -> Dict[str, Any]:
    """Compile all segments into a full script (Method Description)."""
    llm = get_llm(temperature=0.6)

    # Gather segments
    local_segment = state.get("_local_segment", {})
    business_segment = state.get("_business_segment", {})
    ai_segment = state.get("_ai_segment", {})
    bridge = state.get("selected_bridge")

    # Build intro segment
    intro = ScriptSegment(
        segment_type="intro",
        content=(
            "Good evening, everyone! I'm Maya, and welcome to your weekly news "
            "roundup. Let's dive into what happened this week across Southeast "
            "Asia and beyond."
        ),
        estimated_duration_seconds=10,
    )

    # Build outro segment
    outro = ScriptSegment(
        segment_type="outro",
        content=(
            "And that's your weekly roundup! Thanks for watching. I'm Maya, and "
            "I'll see you next week. Stay informed, stay curious!"
        ),
        estimated_duration_seconds=10,
    )

    # Collect all segments
    segments = [intro.model_dump()]

    if local_segment:
        segments.append(local_segment)

    if business_segment:
        segments.append(business_segment)

    # Insert bridge if available
    if bridge and bridge.get("is_approved", False):
        bridge_segment = ScriptSegment(
            segment_type="bridge",
            content=bridge.get("suggested_hook", "") + " " + bridge.get("product_mention", ""),
            bridge_opportunity_id=bridge.get("id"),
            estimated_duration_seconds=15,
        )
        segments.append(bridge_segment.model_dump())

    if ai_segment:
        segments.append(ai_segment)

    segments.append(outro.model_dump())

    # Compile full script text
    full_script_parts = []
    total_duration = 0
    all_fact_ids = []

    for seg in segments:
        seg_type = seg.get("segment_type", "").upper().replace("_", " ")
        full_script_parts.append(f"[{seg_type}]")
        full_script_parts.append(seg.get("content", ""))
        full_script_parts.append("")
        total_duration += seg.get("estimated_duration_seconds", 0)
        all_fact_ids.extend(seg.get("fact_ids", []))

    full_script = "\n".join(full_script_parts)

    # Generate caption
    caption_prompt = CAPTION_PROMPT.format(
        local_summary=(local_segment.get("content", "")[:150] if local_segment else "Local news"),
        business_summary=(business_segment.get("content", "")[:150] if business_segment else "Business updates"),
        ai_summary=(ai_segment.get("content", "")[:150] if ai_segment else "Tech news"),
        week_number=state.get("week_number", 0),
        year=state.get("year", 2024),
    )
    caption_response = await llm.ainvoke([HumanMessage(content=caption_prompt)])

    # Create script version (Method Description)
    version_num = 1
    existing_draft = state.get("draft_script")
    if existing_draft:
        version_num = existing_draft.get("version", 1) + 1

    script_version = ScriptVersion(
        version=version_num,
        status="pending_review",
        segments=[ScriptSegment(**seg) for seg in segments],
        full_script=full_script,
        caption=caption_response.content,
        estimated_total_duration=total_duration,
    )

    return {
        "draft_script": script_version.model_dump(),
        "status": PipelineStatus.AWAITING_SCRIPT_APPROVAL,
    }


async def revise_script(state: MayaState) -> Dict[str, Any]:
    """Revise script based on DRR feedback."""
    llm = get_llm(temperature=0.7)

    # Get the latest DRR with rejection details
    drrs = state.get("design_rationale_records", [])
    script_drrs = [d for d in drrs if d.get("review_type") == "script" and not d.get("approved")]

    if not script_drrs:
        return {}  # No rejection to revise from

    latest_drr = script_drrs[-1]
    draft = state.get("draft_script", {})

    # Build revision prompt based on rejection categories
    rejection_categories = latest_drr.get("rejection_categories", [])
    feedback_text = latest_drr.get("feedback_text", "")
    suggested_revisions = latest_drr.get("suggested_revisions", "")

    revision_instructions = []
    for cat in rejection_categories:
        if cat == "tone_too_aggressive":
            revision_instructions.append("Make the tone softer and more friendly")
        elif cat == "tone_too_casual":
            revision_instructions.append("Make the tone slightly more professional")
        elif cat == "fact_check_failed":
            revision_instructions.append("Remove or rephrase unverified claims")
        elif cat == "cultural_insensitivity":
            revision_instructions.append("Review for cultural sensitivity")
        elif cat == "timing_too_long":
            revision_instructions.append("Shorten the script significantly")
        elif cat == "timing_too_short":
            revision_instructions.append("Add more detail and context")
        elif cat == "bridge_feels_forced":
            revision_instructions.append("Remove or rephrase the promotional bridge")

    if feedback_text:
        revision_instructions.append(f"Additional feedback: {feedback_text}")
    if suggested_revisions:
        revision_instructions.append(f"Specific changes requested: {suggested_revisions}")

    # Apply revisions to each segment
    revised_segments = []
    for segment in draft.get("segments", []):
        if segment.get("segment_type") in ["intro", "outro"]:
            revised_segments.append(segment)
            continue

        revision_prompt = f"""Revise the following news anchor script segment.

ORIGINAL:
{segment.get('content', '')}

REVISION INSTRUCTIONS:
{chr(10).join(f'- {inst}' for inst in revision_instructions)}

Write the revised version, keeping Maya's warm, SEA-friendly personality:"""

        try:
            response = await llm.ainvoke([HumanMessage(content=revision_prompt)])
            segment["content"] = response.content
        except Exception:
            pass  # Keep original if revision fails

        revised_segments.append(segment)

    # Increment revision count is handled in pipeline
    return {
        "_local_segment": next((s for s in revised_segments if s.get("segment_type") == "local"), None),
        "_business_segment": next((s for s in revised_segments if s.get("segment_type") == "business"), None),
        "_ai_segment": next((s for s in revised_segments if s.get("segment_type") == "ai_tech"), None),
    }


# =============================================================================
# HITL GATES (Pattern E.9)
# =============================================================================

async def script_review_gate(state: MayaState) -> Dict[str, Any]:
    """Human approval gate for scripts with DRR support."""
    notification = get_notification_service()

    draft = state.get("draft_script", {})

    # Send notification with script details
    await notification.send_script_approval_request(
        thread_id=state["thread_id"],
        scripts={
            "full_script": draft.get("full_script", ""),
            "caption": draft.get("caption", ""),
            "estimated_duration": draft.get("estimated_total_duration", 0),
            "version": draft.get("version", 1),
        },
        week_number=state["week_number"],
        year=state["year"],
    )

    return {
        "status": PipelineStatus.AWAITING_SCRIPT_APPROVAL,
        "pending_review_type": "script",
    }


async def video_review_gate(state: MayaState) -> Dict[str, Any]:
    """Human approval gate for video with DRR support."""
    notification = get_notification_service()

    await notification.send_video_approval_request(
        thread_id=state["thread_id"],
        video_url=state.get("video_url", ""),
        caption=state.get("approved_script", {}).get("caption", ""),
    )

    return {
        "status": PipelineStatus.AWAITING_VIDEO_APPROVAL,
        "pending_review_type": "video",
    }


# =============================================================================
# VIDEO & PUBLISHING
# =============================================================================

async def generate_video(state: MayaState) -> Dict[str, Any]:
    """Generate video using HeyGen from approved script."""
    heygen = get_heygen_client()
    approved_script = state.get("approved_script", {})

    try:
        result = await heygen.generate_video(
            script=approved_script.get("full_script", ""),
            aspect_ratio="9:16",
        )

        video_id = result["video_id"]
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


async def publish_to_social(state: MayaState) -> Dict[str, Any]:
    """Publish video to social media platforms."""
    blotato = get_blotato_client()
    approved_script = state.get("approved_script", {})

    try:
        results = await blotato.schedule_multi_platform(
            video_url=state["video_url"],
            caption=approved_script.get("caption", ""),
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

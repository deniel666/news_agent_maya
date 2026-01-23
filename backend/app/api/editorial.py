"""Editorial API endpoints for story curation and ranking."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from ..core.database import supabase
from ..models.editorial import (
    BrandProfile,
    BrandProfileCreate,
    EditorialGuideline,
    EditorialGuidelineCreate,
    EditorialGuidelineUpdate,
    EditorialReview,
    EditorialStats,
    GuidelineCategory,
    RawStory,
    RawStoryCreate,
    RawStoryStatus,
    StoryRank,
)
from ..services.editorial_agent import editorial_agent

router = APIRouter()


# ===================
# Brand Profile
# ===================

@router.get("/brand-profile")
async def get_brand_profile():
    """Get the brand profile (there's only one)."""
    response = supabase.table("brand_profile").select("*").limit(1).execute()
    if response.data:
        return response.data[0]
    return None


@router.post("/brand-profile")
async def create_or_update_brand_profile(profile: BrandProfileCreate):
    """Create or update the brand profile."""
    # Check if exists
    existing = supabase.table("brand_profile").select("id").limit(1).execute()

    profile_data = {
        "name": profile.name,
        "tagline": profile.tagline,
        "mission": profile.mission,
        "vision": profile.vision,
        "values": profile.values,
        "target_audience": profile.target_audience,
        "tone_of_voice": profile.tone_of_voice,
        "content_pillars": profile.content_pillars,
        "differentiators": profile.differentiators,
        "competitors": profile.competitors,
        "ai_prompt_context": profile.ai_prompt_context or _generate_ai_context(profile),
        "updated_at": datetime.utcnow().isoformat(),
    }

    if existing.data:
        response = supabase.table("brand_profile").update(profile_data).eq("id", existing.data[0]["id"]).execute()
    else:
        response = supabase.table("brand_profile").insert(profile_data).execute()

    return response.data[0] if response.data else None


def _generate_ai_context(profile: BrandProfileCreate) -> str:
    """Generate AI prompt context from brand profile."""
    return f"""
When evaluating content for {profile.name}:
- We serve: {profile.target_audience}
- Our voice is: {profile.tone_of_voice}
- Core pillars: {', '.join(profile.content_pillars)}
- We value: {', '.join(profile.values)}
- Mission: {profile.mission}

Prioritize content that aligns with these principles and serves our audience's needs.
"""


# ===================
# Editorial Guidelines
# ===================

@router.get("/guidelines", response_model=List[EditorialGuideline])
async def list_guidelines(
    category: Optional[GuidelineCategory] = None,
    enabled: Optional[bool] = None
):
    """List all editorial guidelines."""
    query = supabase.table("editorial_guidelines").select("*")

    if category:
        query = query.eq("category", category.value)
    if enabled is not None:
        query = query.eq("enabled", enabled)

    response = query.order("category").order("weight", desc=True).execute()
    return response.data


@router.post("/guidelines")
async def create_guideline(guideline: EditorialGuidelineCreate):
    """Create a new editorial guideline."""
    data = {
        "name": guideline.name,
        "category": guideline.category.value,
        "description": guideline.description,
        "criteria": guideline.criteria,
        "weight": guideline.weight,
        "enabled": guideline.enabled,
    }
    response = supabase.table("editorial_guidelines").insert(data).execute()
    return response.data[0] if response.data else None


@router.patch("/guidelines/{guideline_id}")
async def update_guideline(guideline_id: UUID, update: EditorialGuidelineUpdate):
    """Update an editorial guideline."""
    data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    data["updated_at"] = datetime.utcnow().isoformat()
    response = supabase.table("editorial_guidelines").update(data).eq("id", str(guideline_id)).execute()
    return response.data[0] if response.data else None


@router.delete("/guidelines/{guideline_id}")
async def delete_guideline(guideline_id: UUID):
    """Delete an editorial guideline."""
    supabase.table("editorial_guidelines").delete().eq("id", str(guideline_id)).execute()
    return {"deleted": True}


@router.post("/guidelines/{guideline_id}/toggle")
async def toggle_guideline(guideline_id: UUID):
    """Toggle a guideline's enabled status."""
    current = supabase.table("editorial_guidelines").select("enabled").eq("id", str(guideline_id)).single().execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Guideline not found")

    new_enabled = not current.data["enabled"]
    response = supabase.table("editorial_guidelines").update({
        "enabled": new_enabled,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", str(guideline_id)).execute()

    return response.data[0] if response.data else None


@router.post("/guidelines/import/defaults")
async def import_default_guidelines():
    """Import a set of default editorial guidelines."""
    defaults = [
        # Topic Priority
        {
            "name": "AI & Technology Focus",
            "category": "topic_priority",
            "description": "Prioritize AI, voice technology, and tech innovation stories",
            "criteria": "Stories about AI advancements, voice assistants, automation, or tech innovation should score higher. Especially relevant: AI for business, voice solutions, conversational AI.",
            "weight": 1.5,
            "enabled": True
        },
        {
            "name": "Southeast Asia Relevance",
            "category": "topic_priority",
            "description": "Regional news gets priority",
            "criteria": "News specifically about or relevant to Southeast Asia (Malaysia, Singapore, Indonesia, Thailand, Philippines, Vietnam) should score higher than global news.",
            "weight": 1.3,
            "enabled": True
        },
        {
            "name": "Business & Enterprise",
            "category": "topic_priority",
            "description": "B2B and enterprise stories",
            "criteria": "Stories relevant to businesses, especially SMEs, enterprise software, or business transformation should be prioritized.",
            "weight": 1.2,
            "enabled": True
        },
        # Topics to Avoid
        {
            "name": "Political Controversies",
            "category": "topic_avoid",
            "description": "Avoid politically divisive content",
            "criteria": "Avoid stories that are primarily about political controversies, partisan debates, or could alienate audience segments. Reduce score significantly.",
            "weight": 1.5,
            "enabled": True
        },
        {
            "name": "Negative Sensationalism",
            "category": "topic_avoid",
            "description": "Avoid clickbait and fear-mongering",
            "criteria": "Stories with sensationalist, clickbait titles or that focus on fear-mongering without substance should be ranked lower.",
            "weight": 1.2,
            "enabled": True
        },
        # Quality Standards
        {
            "name": "Source Credibility",
            "category": "quality",
            "description": "Credible sources rank higher",
            "criteria": "Stories from established, credible news sources should rank higher than unknown or questionable sources.",
            "weight": 1.3,
            "enabled": True
        },
        {
            "name": "Depth & Substance",
            "category": "quality",
            "description": "In-depth reporting preferred",
            "criteria": "Stories with substantial reporting, data, quotes, or analysis should rank higher than brief or shallow pieces.",
            "weight": 1.1,
            "enabled": True
        },
        # Timeliness
        {
            "name": "Breaking News",
            "category": "timeliness",
            "description": "Recent news ranks higher",
            "criteria": "Stories published within the last 24-48 hours should be considered more timely. Week-old news should score lower unless it's an ongoing development.",
            "weight": 1.2,
            "enabled": True
        },
        # Audience
        {
            "name": "Business Decision Makers",
            "category": "audience",
            "description": "Content for professionals",
            "criteria": "Content should be relevant and valuable to business owners, executives, and professionals making technology decisions.",
            "weight": 1.0,
            "enabled": True
        },
        # Brand Voice
        {
            "name": "Professional Tone",
            "category": "brand_voice",
            "description": "Maintain professional standards",
            "criteria": "Content should match our professional, informative, yet approachable brand voice. Avoid overly casual or overly academic content.",
            "weight": 1.0,
            "enabled": True
        },
    ]

    inserted = []
    for guideline in defaults:
        response = supabase.table("editorial_guidelines").insert(guideline).execute()
        if response.data:
            inserted.append(response.data[0])

    return {"imported": len(inserted), "guidelines": inserted}


# ===================
# Raw Stories
# ===================

@router.get("/raw-stories")
async def list_raw_stories(
    status: Optional[RawStoryStatus] = None,
    rank: Optional[StoryRank] = None,
    category: Optional[str] = None,
    source_type: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    sort_by: str = Query(default="created_at", enum=["created_at", "score", "rank"])
):
    """List raw stories with filtering."""
    query = supabase.table("raw_stories").select("*")

    if status:
        query = query.eq("status", status.value)
    if rank:
        query = query.eq("rank", rank.value)
    if category:
        query = query.eq("category", category)
    if source_type:
        query = query.eq("source_type", source_type)
    if min_score is not None:
        query = query.gte("score", min_score)

    if sort_by == "score":
        query = query.order("score", desc=True, nullsfirst=False)
    elif sort_by == "rank":
        query = query.order("rank")
    else:
        query = query.order("created_at", desc=True)

    response = query.range(offset, offset + limit - 1).execute()
    return response.data


@router.post("/raw-stories")
async def create_raw_story(story: RawStoryCreate, auto_score: bool = False, background_tasks: BackgroundTasks = None):
    """Create a new raw story (typically from news aggregation)."""
    data = {
        "title": story.title,
        "content_markdown": story.content_markdown,
        "summary": story.summary,
        "source_name": story.source_name,
        "source_type": story.source_type,
        "source_url": story.source_url,
        "original_url": story.original_url,
        "media_urls": story.media_urls,
        "category": story.category,
        "author": story.author,
        "tags": story.tags,
        "published_at": story.published_at.isoformat() if story.published_at else None,
        "status": "pending",
    }

    response = supabase.table("raw_stories").insert(data).execute()
    created_story = response.data[0] if response.data else None

    # Optionally auto-score the story
    if auto_score and created_story and background_tasks:
        background_tasks.add_task(_score_story_background, created_story["id"])

    return created_story


async def _score_story_background(story_id: str):
    """Background task to score a single story."""
    # Get story
    story_response = supabase.table("raw_stories").select("*").eq("id", story_id).single().execute()
    if not story_response.data:
        return

    story = story_response.data

    # Get guidelines and brand profile
    guidelines_response = supabase.table("editorial_guidelines").select("*").eq("enabled", True).execute()
    guidelines = guidelines_response.data or []

    profile_response = supabase.table("brand_profile").select("*").limit(1).execute()
    brand_profile = profile_response.data[0] if profile_response.data else None

    # Score the story
    result = await editorial_agent.score_single_story(story, guidelines, brand_profile)

    # Update the story
    supabase.table("raw_stories").update({
        "status": "ranked",
        "score": result.get("score"),
        "rank": result.get("rank"),
        "rank_reason": result.get("reason"),
        "reviewed_at": datetime.utcnow().isoformat()
    }).eq("id", story_id).execute()


@router.get("/raw-stories/{story_id}")
async def get_raw_story(story_id: UUID):
    """Get a specific raw story."""
    response = supabase.table("raw_stories").select("*").eq("id", str(story_id)).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Story not found")
    return response.data


@router.post("/raw-stories/{story_id}/score")
async def score_raw_story(story_id: UUID):
    """Manually trigger scoring for a raw story."""
    # Get story
    story_response = supabase.table("raw_stories").select("*").eq("id", str(story_id)).single().execute()
    if not story_response.data:
        raise HTTPException(status_code=404, detail="Story not found")

    story = story_response.data

    # Update status to reviewing
    supabase.table("raw_stories").update({"status": "reviewing"}).eq("id", str(story_id)).execute()

    # Get guidelines and brand profile
    guidelines_response = supabase.table("editorial_guidelines").select("*").eq("enabled", True).execute()
    guidelines = guidelines_response.data or []

    profile_response = supabase.table("brand_profile").select("*").limit(1).execute()
    brand_profile = profile_response.data[0] if profile_response.data else None

    # Score the story
    result = await editorial_agent.score_single_story(story, guidelines, brand_profile)

    # Update the story
    update_response = supabase.table("raw_stories").update({
        "status": "ranked",
        "score": result.get("score"),
        "rank": result.get("rank"),
        "rank_reason": result.get("reason"),
        "reviewed_at": datetime.utcnow().isoformat()
    }).eq("id", str(story_id)).execute()

    return update_response.data[0] if update_response.data else None


@router.post("/raw-stories/{story_id}/promote")
async def promote_raw_story(story_id: UUID, title: Optional[str] = None):
    """Promote a raw story to the main content library."""
    # Get the raw story
    raw_response = supabase.table("raw_stories").select("*").eq("id", str(story_id)).single().execute()
    if not raw_response.data:
        raise HTTPException(status_code=404, detail="Raw story not found")

    raw_story = raw_response.data

    # Create a new story in the content library
    story_data = {
        "title": title or raw_story["title"],
        "description": raw_story.get("summary") or raw_story["content_markdown"][:500],
        "source_url": raw_story.get("original_url") or raw_story.get("source_url"),
        "story_type": "manual",
        "status": "draft",
        "tags": raw_story.get("tags", []),
        "script_en": None,
        "script_ms": None,
    }

    story_response = supabase.table("stories").insert(story_data).execute()
    created_story = story_response.data[0] if story_response.data else None

    if created_story:
        # Update raw story status
        supabase.table("raw_stories").update({
            "status": "promoted",
            "promoted_story_id": created_story["id"]
        }).eq("id", str(story_id)).execute()

    return created_story


@router.post("/raw-stories/{story_id}/archive")
async def archive_raw_story(story_id: UUID):
    """Archive a raw story."""
    response = supabase.table("raw_stories").update({
        "status": "archived"
    }).eq("id", str(story_id)).execute()

    return response.data[0] if response.data else None


@router.delete("/raw-stories/{story_id}")
async def delete_raw_story(story_id: UUID):
    """Delete a raw story."""
    supabase.table("raw_stories").delete().eq("id", str(story_id)).execute()
    return {"deleted": True}


# ===================
# Editorial Reviews
# ===================

@router.get("/reviews")
async def list_reviews(limit: int = Query(default=10, le=50)):
    """List editorial reviews."""
    response = supabase.table("editorial_reviews").select("*").order("created_at", desc=True).limit(limit).execute()
    return response.data


@router.get("/reviews/{review_id}")
async def get_review(review_id: UUID):
    """Get a specific editorial review."""
    response = supabase.table("editorial_reviews").select("*").eq("id", str(review_id)).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Review not found")
    return response.data


@router.get("/reviews/week/{year}/{week_number}")
async def get_review_by_week(year: int, week_number: int):
    """Get editorial review for a specific week."""
    response = supabase.table("editorial_reviews").select("*").eq("year", year).eq("week_number", week_number).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Review not found for this week")
    return response.data


@router.post("/reviews/run")
async def run_editorial_review(
    week_number: Optional[int] = None,
    year: Optional[int] = None,
    background_tasks: BackgroundTasks = None
):
    """Run a new editorial review for pending stories."""
    now = datetime.utcnow()
    if week_number is None:
        week_number = now.isocalendar()[1]
    if year is None:
        year = now.year

    # Check if review already exists for this week
    existing = supabase.table("editorial_reviews").select("id").eq("year", year).eq("week_number", week_number).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail=f"Review already exists for week {week_number}, {year}")

    # Get pending stories
    stories_response = supabase.table("raw_stories").select("*").eq("status", "pending").execute()
    stories = stories_response.data or []

    if not stories:
        raise HTTPException(status_code=400, detail="No pending stories to review")

    # Get guidelines
    guidelines_response = supabase.table("editorial_guidelines").select("*").eq("enabled", True).execute()
    guidelines = guidelines_response.data or []

    # Get brand profile
    profile_response = supabase.table("brand_profile").select("*").limit(1).execute()
    brand_profile = profile_response.data[0] if profile_response.data else None

    # Calculate review period
    review_start = now - timedelta(days=7)
    review_end = now

    # Create review record
    review_data = {
        "week_number": week_number,
        "year": year,
        "review_period_start": review_start.isoformat(),
        "review_period_end": review_end.isoformat(),
        "status": "in_progress",
        "total_stories_reviewed": len(stories),
    }
    review_response = supabase.table("editorial_reviews").insert(review_data).execute()
    review = review_response.data[0] if review_response.data else None

    if not review:
        raise HTTPException(status_code=500, detail="Failed to create review record")

    # Run the review in background
    if background_tasks:
        background_tasks.add_task(
            _run_review_background,
            review["id"],
            stories,
            guidelines,
            brand_profile,
            week_number,
            year
        )
        return {"message": "Editorial review started", "review_id": review["id"]}
    else:
        # Run synchronously
        result = await _run_review_background(
            review["id"],
            stories,
            guidelines,
            brand_profile,
            week_number,
            year
        )
        return result


async def _run_review_background(
    review_id: str,
    stories: List[dict],
    guidelines: List[dict],
    brand_profile: Optional[dict],
    week_number: int,
    year: int
):
    """Background task to run editorial review."""
    try:
        # Update stories to reviewing status
        story_ids = [s["id"] for s in stories]
        for sid in story_ids:
            supabase.table("raw_stories").update({
                "status": "reviewing",
                "editorial_review_id": review_id
            }).eq("id", sid).execute()

        # Run the editorial agent
        result = await editorial_agent.run_review(
            raw_stories=stories,
            guidelines=guidelines,
            brand_profile=brand_profile,
            week_number=week_number,
            year=year
        )

        if result.get("success"):
            # Update each story with its score
            for rec in result.get("recommendations", []):
                supabase.table("raw_stories").update({
                    "status": "ranked",
                    "score": rec.get("score"),
                    "rank": rec.get("rank"),
                    "rank_reason": rec.get("reason"),
                    "reviewed_at": datetime.utcnow().isoformat()
                }).eq("id", rec["raw_story_id"]).execute()

            # Update review record
            supabase.table("editorial_reviews").update({
                "status": "completed",
                "executive_summary": result.get("executive_summary"),
                "key_themes": result.get("key_themes", []),
                "recommendations": result.get("recommendations", []),
                "editorial_notes": result.get("editorial_notes"),
                "top_priority_count": result["stats"]["top_priority"],
                "high_count": result["stats"]["high"],
                "medium_count": result["stats"]["medium"],
                "low_count": result["stats"]["low"],
                "rejected_count": result["stats"]["rejected"],
                "completed_at": datetime.utcnow().isoformat()
            }).eq("id", review_id).execute()

            return result
        else:
            # Mark as failed
            supabase.table("editorial_reviews").update({
                "status": "failed",
                "editorial_notes": f"Error: {result.get('error')}"
            }).eq("id", review_id).execute()

            return result

    except Exception as e:
        # Mark as failed
        supabase.table("editorial_reviews").update({
            "status": "failed",
            "editorial_notes": f"Exception: {str(e)}"
        }).eq("id", review_id).execute()
        raise


# ===================
# Stats
# ===================

@router.get("/stats", response_model=EditorialStats)
async def get_editorial_stats():
    """Get editorial statistics."""
    response = supabase.rpc("get_editorial_stats_json").execute()

    # If RPC doesn't exist, calculate manually
    if not response.data:
        raw_count = supabase.table("raw_stories").select("id", count="exact").execute()
        pending_count = supabase.table("raw_stories").select("id", count="exact").eq("status", "pending").execute()

        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        reviewed_week = supabase.table("raw_stories").select("id", count="exact").gte("reviewed_at", week_ago.isoformat()).execute()
        promoted_week = supabase.table("raw_stories").select("id", count="exact").eq("status", "promoted").gte("reviewed_at", week_ago.isoformat()).execute()

        top_priority = supabase.table("raw_stories").select("id", count="exact").eq("rank", "top_priority").execute()
        high = supabase.table("raw_stories").select("id", count="exact").eq("rank", "high").execute()
        medium = supabase.table("raw_stories").select("id", count="exact").eq("rank", "medium").execute()
        low = supabase.table("raw_stories").select("id", count="exact").eq("rank", "low").execute()
        rejected = supabase.table("raw_stories").select("id", count="exact").eq("rank", "rejected").execute()

        avg_score = supabase.table("raw_stories").select("score").not_.is_("score", "null").execute()
        avg = sum(s["score"] for s in avg_score.data) / max(len(avg_score.data), 1) if avg_score.data else 0

        reviews = supabase.table("editorial_reviews").select("completed_at").order("completed_at", desc=True).limit(1).execute()

        return EditorialStats(
            total_raw_stories=raw_count.count or 0,
            pending_review=pending_count.count or 0,
            reviewed_this_week=reviewed_week.count or 0,
            promoted_this_week=promoted_week.count or 0,
            top_priority_stories=top_priority.count or 0,
            high_stories=high.count or 0,
            medium_stories=medium.count or 0,
            low_stories=low.count or 0,
            rejected_stories=rejected.count or 0,
            average_score=round(avg, 1),
            total_reviews=supabase.table("editorial_reviews").select("id", count="exact").execute().count or 0,
            latest_review_date=reviews.data[0]["completed_at"] if reviews.data and reviews.data[0].get("completed_at") else None
        )

    return response.data


@router.get("/categories")
async def get_guideline_categories():
    """Get all guideline category options."""
    return [
        {"value": "brand_voice", "label": "Brand Voice", "description": "Tone, style, and personality guidelines"},
        {"value": "topic_priority", "label": "Topic Priority", "description": "Topics to prioritize in coverage"},
        {"value": "topic_avoid", "label": "Topics to Avoid", "description": "Topics to deprioritize or reject"},
        {"value": "audience", "label": "Audience", "description": "Target audience criteria"},
        {"value": "quality", "label": "Quality Standards", "description": "Content quality requirements"},
        {"value": "timeliness", "label": "Timeliness", "description": "How fresh news should be"},
        {"value": "regional", "label": "Regional Relevance", "description": "Geographic relevance criteria"},
    ]


# ===================
# Pipeline Operations
# ===================

@router.post("/pipeline/aggregate")
async def aggregate_news(
    days: int = Query(default=7, le=30),
    auto_score: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Aggregate news from all configured sources and store as raw stories.
    This pulls from RSS feeds, Nitter (Twitter), and Telegram channels.
    """
    from ..services.editorial_pipeline import get_editorial_pipeline

    pipeline = get_editorial_pipeline()

    if background_tasks:
        background_tasks.add_task(pipeline.aggregate_and_store, days, auto_score)
        return {"message": "News aggregation started in background"}

    result = await pipeline.aggregate_and_store(days=days, auto_score=auto_score)
    return result


@router.get("/pipeline/top-stories")
async def get_top_stories(limit: int = Query(default=5, le=20)):
    """Get top-ranked stories ready for content creation."""
    from ..services.editorial_pipeline import get_editorial_pipeline

    pipeline = get_editorial_pipeline()
    stories = await pipeline.get_top_stories(limit=limit)
    return stories


@router.post("/pipeline/full-cycle")
async def run_full_editorial_cycle(
    days: int = Query(default=7, le=30),
    background_tasks: BackgroundTasks = None
):
    """
    Run a complete editorial cycle:
    1. Aggregate news from all sources
    2. Run editorial review to score and rank stories
    3. Return summary of results

    This is the main endpoint for the weekly editorial workflow.
    """
    from ..services.editorial_pipeline import get_editorial_pipeline

    pipeline = get_editorial_pipeline()

    async def _run_full_cycle():
        # Step 1: Aggregate
        agg_result = await pipeline.aggregate_and_store(days=days, auto_score=False)

        # Step 2: Review
        review_result = await pipeline.run_weekly_review()

        return {
            "aggregation": agg_result,
            "review": review_result
        }

    if background_tasks:
        background_tasks.add_task(_run_full_cycle)
        return {"message": "Full editorial cycle started in background"}

    return await _run_full_cycle()

"""API endpoints for dashboard data."""

from fastapi import APIRouter
from typing import List
from datetime import date, timedelta

from app.services.database import get_db_service
from app.models.schemas import PipelineStatus

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """Get dashboard statistics."""
    db = get_db_service()
    return await db.get_dashboard_stats()


@router.get("/recent-activity")
async def get_recent_activity(limit: int = 10):
    """Get recent pipeline activity."""
    db = get_db_service()

    briefings = await db.list_briefings(limit=limit)

    activity = []
    for briefing in briefings:
        activity.append({
            "type": "briefing",
            "thread_id": briefing.thread_id,
            "status": briefing.status.value,
            "week_number": briefing.week_number,
            "year": briefing.year,
            "created_at": briefing.created_at,
            "updated_at": briefing.published_at or briefing.video_approved_at or briefing.script_approved_at or briefing.created_at,
        })

    return {"activity": activity}


@router.get("/weekly-summary")
async def get_weekly_summary():
    """Get summary for current and recent weeks."""
    db = get_db_service()
    today = date.today()

    target_weeks = []
    thread_ids = []

    for i in range(4):  # Last 4 weeks
        week_date = today - timedelta(weeks=i)
        week_number = week_date.isocalendar()[1]
        year = week_date.isocalendar()[0]
        thread_id = f"{year}-W{week_number:02d}"

        target_weeks.append({
            "week_number": week_number,
            "year": year,
            "thread_id": thread_id
        })
        thread_ids.append(thread_id)

    briefings = await db.get_briefings_by_threads(thread_ids)
    briefing_map = {b.thread_id: b for b in briefings}

    weeks = []
    for target in target_weeks:
        briefing = briefing_map.get(target["thread_id"])

        weeks.append({
            "week_number": target["week_number"],
            "year": target["year"],
            "status": briefing.status.value if briefing else "not_started",
            "briefing_id": str(briefing.id) if briefing else None,
            "thread_id": briefing.thread_id if briefing else None,
        })

    return {"weeks": weeks}


@router.get("/pipeline-status/{thread_id}")
async def get_pipeline_status(thread_id: str):
    """Get detailed pipeline status."""
    db = get_db_service()
    briefing = await db.get_briefing_by_thread(thread_id)

    if not briefing:
        return {"error": "Briefing not found"}

    # Define pipeline stages
    stages = [
        {"name": "aggregating", "label": "Aggregating News", "status": "pending"},
        {"name": "categorizing", "label": "Categorizing", "status": "pending"},
        {"name": "synthesizing", "label": "Synthesizing Scripts", "status": "pending"},
        {"name": "awaiting_script_approval", "label": "Script Approval", "status": "pending"},
        {"name": "generating_video", "label": "Generating Video", "status": "pending"},
        {"name": "awaiting_video_approval", "label": "Video Approval", "status": "pending"},
        {"name": "publishing", "label": "Publishing", "status": "pending"},
        {"name": "completed", "label": "Completed", "status": "pending"},
    ]

    # Mark stages based on current status
    current_found = False
    for stage in stages:
        if stage["name"] == briefing.status.value:
            stage["status"] = "current"
            current_found = True
        elif not current_found:
            stage["status"] = "completed"

    return {
        "thread_id": thread_id,
        "current_status": briefing.status.value,
        "stages": stages,
        "briefing": briefing,
    }


@router.get("/sources-status")
async def get_sources_status():
    """Get status of news sources."""
    # This could check if sources are reachable
    from app.services.news_aggregator import SEA_RSS_FEEDS, TWITTER_ACCOUNTS, SEA_TELEGRAM_CHANNELS

    sources = []

    for name, url in SEA_RSS_FEEDS.items():
        sources.append({
            "name": name,
            "type": "rss",
            "url": url,
            "status": "active",  # Could add actual health check
        })

    for account in TWITTER_ACCOUNTS:
        sources.append({
            "name": f"@{account}",
            "type": "nitter",
            "url": f"https://nitter.net/{account}",
            "status": "active",
        })

    for channel in SEA_TELEGRAM_CHANNELS:
        sources.append({
            "name": channel,
            "type": "telegram",
            "url": None,
            "status": "active",
        })

    return {"sources": sources}

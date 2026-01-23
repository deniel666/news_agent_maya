"""API endpoints for weekly briefings."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.models.schemas import (
    WeeklyBriefing,
    WeeklyBriefingCreate,
    PipelineStatus,
)
from app.services.database import get_db_service
from app.agents.pipeline import get_pipeline

router = APIRouter()


@router.post("/", response_model=dict)
async def create_briefing(
    background_tasks: BackgroundTasks,
    week_number: Optional[int] = None,
    year: Optional[int] = None,
):
    """Create and start a new weekly briefing pipeline."""
    today = date.today()
    week_number = week_number or today.isocalendar()[1]
    year = year or today.year

    # Check if briefing already exists
    db = get_db_service()
    existing = await db.get_briefing_by_week(year, week_number)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Briefing for week {week_number}, {year} already exists"
        )

    # Start pipeline in background
    pipeline = get_pipeline()

    async def run_pipeline():
        await pipeline.start_briefing(week_number, year)

    background_tasks.add_task(run_pipeline)

    thread_id = f"{year}-W{week_number:02d}"

    return {
        "message": "Briefing pipeline started",
        "thread_id": thread_id,
        "week_number": week_number,
        "year": year,
    }


@router.get("/", response_model=List[WeeklyBriefing])
async def list_briefings(
    limit: int = 20,
    offset: int = 0,
    status: Optional[PipelineStatus] = None,
):
    """List all weekly briefings."""
    db = get_db_service()
    return await db.list_briefings(limit=limit, offset=offset, status=status)


@router.get("/pending", response_model=List[WeeklyBriefing])
async def list_pending_approvals():
    """List briefings awaiting approval."""
    db = get_db_service()
    return await db.get_pending_approvals()


@router.get("/current", response_model=Optional[WeeklyBriefing])
async def get_current_briefing():
    """Get the current week's briefing."""
    today = date.today()
    week_number = today.isocalendar()[1]
    year = today.year

    db = get_db_service()
    return await db.get_briefing_by_week(year, week_number)


@router.get("/{thread_id}", response_model=dict)
async def get_briefing(thread_id: str):
    """Get a specific briefing by thread ID."""
    db = get_db_service()
    briefing = await db.get_briefing_by_thread(thread_id)

    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Get pipeline state for additional details
    pipeline = get_pipeline()
    state = await pipeline.get_state(thread_id)

    return {
        "briefing": briefing,
        "state": state,
    }


@router.get("/{thread_id}/scripts", response_model=dict)
async def get_briefing_scripts(thread_id: str):
    """Get scripts for a specific briefing."""
    db = get_db_service()
    briefing = await db.get_briefing_by_thread(thread_id)

    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    return {
        "thread_id": thread_id,
        "local_script": briefing.local_script,
        "business_script": briefing.business_script,
        "ai_script": briefing.ai_script,
        "full_script": briefing.full_script,
    }


@router.get("/{thread_id}/video", response_model=dict)
async def get_briefing_video(thread_id: str):
    """Get video details for a specific briefing."""
    db = get_db_service()
    briefing = await db.get_briefing_by_thread(thread_id)

    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    video = await db.get_video_by_briefing(briefing.id)

    return {
        "thread_id": thread_id,
        "video": video,
    }


@router.get("/{thread_id}/posts", response_model=dict)
async def get_briefing_posts(thread_id: str):
    """Get social posts for a specific briefing."""
    db = get_db_service()
    briefing = await db.get_briefing_by_thread(thread_id)

    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    video = await db.get_video_by_briefing(briefing.id)
    posts = []

    if video:
        posts = await db.get_posts_by_video(video.id)

    return {
        "thread_id": thread_id,
        "posts": posts,
    }


@router.delete("/{thread_id}")
async def delete_briefing(thread_id: str):
    """Delete a briefing (admin only)."""
    # TODO: Add authentication
    db = get_db_service()
    briefing = await db.get_briefing_by_thread(thread_id)

    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # For now, just mark as failed
    from app.models.schemas import WeeklyBriefingUpdate
    await db.update_briefing(
        briefing.id,
        WeeklyBriefingUpdate(status=PipelineStatus.FAILED)
    )

    return {"message": "Briefing cancelled"}

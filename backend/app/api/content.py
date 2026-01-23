"""API endpoints for content/story management."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.content import (
    Story,
    StoryCreate,
    StoryUpdate,
    StoryWithAssets,
    StoryStatus,
    StoryType,
    VideoAsset,
    VideoAssetCreate,
    PublishRecord,
    PublishRecordCreate,
    ContentStats,
)
from app.services.database import get_db_service

router = APIRouter()


# ==================
# Stories
# ==================

@router.get("/stories", response_model=List[StoryWithAssets])
async def list_stories(
    status: Optional[StoryStatus] = None,
    story_type: Optional[StoryType] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    featured: Optional[bool] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
):
    """List all stories with filters."""
    db = get_db_service()
    stories = await db.list_stories(
        status=status,
        story_type=story_type,
        tag=tag,
        search=search,
        featured=featured,
        limit=limit,
        offset=offset,
    )
    return stories


@router.post("/stories", response_model=Story)
async def create_story(story: StoryCreate):
    """Create a new story."""
    db = get_db_service()
    result = await db.create_story(story)
    return result


@router.get("/stories/{story_id}", response_model=StoryWithAssets)
async def get_story(story_id: UUID):
    """Get a story with all its assets."""
    db = get_db_service()
    story = await db.get_story_with_assets(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.patch("/stories/{story_id}", response_model=Story)
async def update_story(story_id: UUID, update: StoryUpdate):
    """Update a story."""
    db = get_db_service()

    existing = await db.get_story(story_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Story not found")

    result = await db.update_story(story_id, update)
    return result


@router.delete("/stories/{story_id}")
async def delete_story(story_id: UUID):
    """Delete a story and all its assets."""
    db = get_db_service()

    existing = await db.get_story(story_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Story not found")

    await db.delete_story(story_id)
    return {"status": "deleted", "id": str(story_id)}


@router.post("/stories/{story_id}/feature")
async def toggle_featured(story_id: UUID):
    """Toggle story featured status."""
    db = get_db_service()

    existing = await db.get_story(story_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Story not found")

    update = StoryUpdate(featured=not existing.featured)
    result = await db.update_story(story_id, update)

    return {"id": str(story_id), "featured": result.featured}


@router.post("/stories/{story_id}/archive")
async def archive_story(story_id: UUID):
    """Archive a story."""
    db = get_db_service()

    existing = await db.get_story(story_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Story not found")

    update = StoryUpdate(status=StoryStatus.ARCHIVED)
    result = await db.update_story(story_id, update)

    return {"id": str(story_id), "status": result.status}


# ==================
# Video Assets
# ==================

@router.get("/stories/{story_id}/videos", response_model=List[VideoAsset])
async def list_story_videos(story_id: UUID):
    """List all videos for a story."""
    db = get_db_service()
    videos = await db.list_videos_by_story(story_id)
    return videos


@router.post("/stories/{story_id}/videos", response_model=VideoAsset)
async def add_video(story_id: UUID, video: VideoAssetCreate):
    """Add a video to a story."""
    db = get_db_service()

    # Verify story exists
    existing = await db.get_story(story_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Story not found")

    video.story_id = story_id
    result = await db.create_video_asset(video)

    # Update story status if first video
    if existing.status == StoryStatus.SCRIPT_READY:
        await db.update_story(story_id, StoryUpdate(status=StoryStatus.VIDEO_READY))

    return result


@router.delete("/videos/{video_id}")
async def delete_video(video_id: UUID):
    """Delete a video asset."""
    db = get_db_service()
    await db.delete_video_asset(video_id)
    return {"status": "deleted", "id": str(video_id)}


# ==================
# Publish Records
# ==================

@router.get("/stories/{story_id}/publish-records", response_model=List[PublishRecord])
async def list_publish_records(story_id: UUID):
    """List all publish records for a story."""
    db = get_db_service()
    records = await db.list_publish_records_by_story(story_id)
    return records


@router.post("/stories/{story_id}/publish", response_model=PublishRecord)
async def create_publish_record(story_id: UUID, record: PublishRecordCreate):
    """Create a publish record."""
    db = get_db_service()

    # Verify story exists
    existing = await db.get_story(story_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Story not found")

    record.story_id = story_id
    result = await db.create_publish_record(record)
    return result


@router.patch("/publish-records/{record_id}")
async def update_publish_record(
    record_id: UUID,
    post_url: Optional[str] = None,
    post_id: Optional[str] = None,
    status: Optional[str] = None,
    error: Optional[str] = None,
):
    """Update a publish record."""
    db = get_db_service()

    updates = {}
    if post_url is not None:
        updates["post_url"] = post_url
    if post_id is not None:
        updates["post_id"] = post_id
    if status is not None:
        updates["status"] = status
        if status == "published":
            updates["published_at"] = datetime.utcnow()
    if error is not None:
        updates["error"] = error

    result = await db.update_publish_record(record_id, updates)
    return result


# ==================
# Content Stats
# ==================

@router.get("/stats", response_model=ContentStats)
async def get_content_stats():
    """Get content library statistics."""
    db = get_db_service()
    stats = await db.get_content_stats()
    return stats


@router.get("/tags")
async def list_all_tags():
    """Get all unique tags used in stories."""
    db = get_db_service()
    tags = await db.get_all_tags()
    return {"tags": tags}


# ==================
# Import from existing
# ==================

@router.post("/import/from-briefing/{thread_id}")
async def import_from_briefing(thread_id: str):
    """Import a weekly briefing as stories."""
    db = get_db_service()

    briefing = await db.get_briefing_by_thread(thread_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Create story from briefing
    story_data = StoryCreate(
        title=f"Weekly Briefing - Week {briefing.week_number}, {briefing.year}",
        description=f"Weekly news roundup for Week {briefing.week_number}",
        story_type=StoryType.WEEKLY_BRIEFING,
        tags=["weekly", f"week-{briefing.week_number}", str(briefing.year)],
    )

    story = await db.create_story(story_data)

    # Link briefing to story
    await db.link_briefing_to_story(briefing.id, story.id)

    # Copy scripts
    update = StoryUpdate(
        status=StoryStatus.SCRIPT_READY if briefing.full_script else StoryStatus.DRAFT,
    )
    await db.update_story(story.id, update)
    await db.update_story_scripts(
        story.id,
        script_en=briefing.full_script,
    )

    return {
        "status": "imported",
        "story_id": str(story.id),
        "title": story.title,
    }


@router.post("/import/from-ondemand/{job_id}")
async def import_from_ondemand(job_id: UUID):
    """Import an on-demand job as a story."""
    db = get_db_service()

    job = await db.get_ondemand_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Create story from job
    story_data = StoryCreate(
        title=job.title or "Untitled Story",
        description=f"Generated from: {job.article_url}",
        source_url=job.article_url,
        story_type=StoryType.ON_DEMAND,
        tags=["on-demand"],
    )

    story = await db.create_story(story_data)

    # Link job to story
    await db.link_ondemand_to_story(job_id, story.id)

    # Copy scripts and videos
    status = StoryStatus.DRAFT
    if job.script_en or job.script_ms:
        status = StoryStatus.SCRIPT_READY
    if job.video_url_en or job.video_url_ms:
        status = StoryStatus.VIDEO_READY

    await db.update_story_scripts(
        story.id,
        script_en=job.script_en,
        script_ms=job.script_ms,
    )

    # Create video assets
    if job.video_url_en:
        await db.create_video_asset(VideoAssetCreate(
            story_id=story.id,
            language="en",
            video_url=job.video_url_en,
        ))

    if job.video_url_ms:
        await db.create_video_asset(VideoAssetCreate(
            story_id=story.id,
            language="ms",
            video_url=job.video_url_ms,
        ))

    update = StoryUpdate(status=status)
    await db.update_story(story.id, update)

    return {
        "status": "imported",
        "story_id": str(story.id),
        "title": story.title,
    }

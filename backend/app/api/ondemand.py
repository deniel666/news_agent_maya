"""API endpoints for on-demand article-to-video generation."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from uuid import UUID

from app.models.sources import OnDemandRequest, OnDemandJob, Language
from app.services.database import get_db_service
from app.services.ondemand import get_ondemand_service

router = APIRouter()


@router.post("/generate", response_model=dict)
async def generate_from_article(
    request: OnDemandRequest,
    background_tasks: BackgroundTasks,
):
    """
    Generate video from a specific article URL.

    1. Scrapes the article
    2. Rewrites content as Maya script
    3. Generates video in requested languages
    4. Sends approval via Telegram
    5. Publishes to selected platforms
    """
    db = get_db_service()
    ondemand = get_ondemand_service()

    # Create job record
    job = await db.create_ondemand_job(
        article_url=request.article_url,
        title=request.title,
        languages=[lang.value for lang in request.languages],
        platforms=request.platforms,
    )

    # Start processing in background
    async def process_job():
        await ondemand.process_article(
            job_id=job.id,
            article_url=request.article_url,
            languages=request.languages,
            platforms=request.platforms,
        )

    background_tasks.add_task(process_job)

    return {
        "status": "processing",
        "job_id": str(job.id),
        "message": "Article processing started. You will receive a Telegram message for approval.",
    }


@router.get("/jobs", response_model=List[dict])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 20,
):
    """List on-demand generation jobs."""
    db = get_db_service()
    jobs = await db.list_ondemand_jobs(status=status, limit=limit)
    return [
        {
            "id": str(job.id),
            "article_url": job.article_url,
            "title": job.title,
            "status": job.status,
            "languages": job.languages,
            "platforms": job.platforms,
            "created_at": job.created_at.isoformat(),
            "has_english": job.script_en is not None,
            "has_malay": job.script_ms is not None,
        }
        for job in jobs
    ]


@router.get("/jobs/{job_id}")
async def get_job(job_id: UUID):
    """Get details of a specific job."""
    db = get_db_service()
    job = await db.get_ondemand_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": str(job.id),
        "article_url": job.article_url,
        "title": job.title,
        "original_content": job.original_content,
        "scripts": {
            "en": job.script_en,
            "ms": job.script_ms,
        },
        "videos": {
            "en": job.video_url_en,
            "ms": job.video_url_ms,
        },
        "captions": {
            "en": job.caption_en,
            "ms": job.caption_ms,
        },
        "languages": job.languages,
        "platforms": job.platforms,
        "status": job.status,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "approved_at": job.approved_at.isoformat() if job.approved_at else None,
        "published_at": job.published_at.isoformat() if job.published_at else None,
    }


@router.post("/jobs/{job_id}/approve")
async def approve_job(
    job_id: UUID,
    approved: bool,
    feedback: Optional[str] = None,
    edited_scripts: Optional[dict] = None,
    background_tasks: BackgroundTasks = None,
):
    """Approve or reject an on-demand job."""
    db = get_db_service()
    ondemand = get_ondemand_service()

    job = await db.get_ondemand_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "awaiting_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not awaiting approval. Current status: {job.status}"
        )

    if approved:
        # Update scripts if edited
        if edited_scripts:
            await db.update_ondemand_scripts(job_id, edited_scripts)

        # Continue to video generation
        async def continue_processing():
            await ondemand.generate_videos(job_id)

        background_tasks.add_task(continue_processing)

        return {
            "status": "approved",
            "message": "Generating videos...",
        }
    else:
        await db.update_ondemand_status(job_id, "rejected", error=feedback)
        return {
            "status": "rejected",
            "message": feedback or "Job rejected",
        }


@router.post("/jobs/{job_id}/approve-video")
async def approve_video(
    job_id: UUID,
    approved: bool,
    background_tasks: BackgroundTasks = None,
):
    """Approve video for publishing."""
    db = get_db_service()
    ondemand = get_ondemand_service()

    job = await db.get_ondemand_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if approved:
        # Publish to social platforms
        async def publish():
            await ondemand.publish_to_social(job_id)

        background_tasks.add_task(publish)

        return {
            "status": "publishing",
            "message": "Publishing to social platforms...",
        }
    else:
        await db.update_ondemand_status(job_id, "video_rejected")
        return {
            "status": "rejected",
        }


@router.post("/jobs/{job_id}/regenerate")
async def regenerate_job(
    job_id: UUID,
    regenerate_script: bool = False,
    regenerate_video: bool = True,
    background_tasks: BackgroundTasks = None,
):
    """Regenerate script or video for a job."""
    db = get_db_service()
    ondemand = get_ondemand_service()

    job = await db.get_ondemand_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def regenerate():
        if regenerate_script:
            await ondemand.regenerate_scripts(job_id)
        if regenerate_video:
            await ondemand.generate_videos(job_id)

    background_tasks.add_task(regenerate)

    return {
        "status": "regenerating",
        "regenerate_script": regenerate_script,
        "regenerate_video": regenerate_video,
    }


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: UUID):
    """Delete an on-demand job."""
    db = get_db_service()

    job = await db.get_ondemand_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await db.delete_ondemand_job(job_id)

    return {"status": "deleted", "id": str(job_id)}

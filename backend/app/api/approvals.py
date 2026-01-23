"""API endpoints for approval workflow."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.models.schemas import ApprovalRequest, ApprovalResponse
from app.agents.pipeline import get_pipeline
from app.services.database import get_db_service

router = APIRouter()


class ScriptApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    feedback: Optional[str] = None
    edited_scripts: Optional[dict] = None


class VideoApprovalRequest(BaseModel):
    thread_id: str
    approved: bool
    edited_caption: Optional[str] = None


@router.post("/script", response_model=ApprovalResponse)
async def approve_script(
    request: ScriptApprovalRequest,
    background_tasks: BackgroundTasks,
):
    """Approve or reject scripts and continue pipeline."""
    pipeline = get_pipeline()
    db = get_db_service()

    # Verify briefing exists
    briefing = await db.get_briefing_by_thread(request.thread_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Update scripts if edited
    if request.edited_scripts:
        from app.models.schemas import WeeklyBriefingUpdate
        await db.update_briefing(
            briefing.id,
            WeeklyBriefingUpdate(
                local_script=request.edited_scripts.get("local"),
                business_script=request.edited_scripts.get("business"),
                ai_script=request.edited_scripts.get("ai"),
            )
        )

    # Continue pipeline in background
    async def continue_pipeline():
        await pipeline.approve_script(
            request.thread_id,
            request.approved,
            request.feedback,
        )

    background_tasks.add_task(continue_pipeline)

    return ApprovalResponse(
        status="processing",
        message="Script approval received, continuing pipeline",
        next_step="generate_video" if request.approved else "rejected",
    )


@router.post("/video", response_model=ApprovalResponse)
async def approve_video(
    request: VideoApprovalRequest,
    background_tasks: BackgroundTasks,
):
    """Approve or reject video and continue to publishing."""
    pipeline = get_pipeline()
    db = get_db_service()

    # Verify briefing exists
    briefing = await db.get_briefing_by_thread(request.thread_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    # Continue pipeline in background
    async def continue_pipeline():
        await pipeline.approve_video(
            request.thread_id,
            request.approved,
        )

    background_tasks.add_task(continue_pipeline)

    return ApprovalResponse(
        status="processing",
        message="Video approval received, continuing pipeline",
        next_step="publish" if request.approved else "rejected",
    )


@router.get("/pending")
async def get_pending_approvals():
    """Get all pending approvals."""
    db = get_db_service()
    pending = await db.get_pending_approvals()

    script_approvals = []
    video_approvals = []

    for briefing in pending:
        from app.models.schemas import PipelineStatus
        if briefing.status == PipelineStatus.AWAITING_SCRIPT_APPROVAL:
            script_approvals.append({
                "thread_id": briefing.thread_id,
                "week_number": briefing.week_number,
                "year": briefing.year,
                "created_at": briefing.created_at,
                "scripts": {
                    "local": briefing.local_script,
                    "business": briefing.business_script,
                    "ai": briefing.ai_script,
                }
            })
        elif briefing.status == PipelineStatus.AWAITING_VIDEO_APPROVAL:
            video = await db.get_video_by_briefing(briefing.id)
            video_approvals.append({
                "thread_id": briefing.thread_id,
                "week_number": briefing.week_number,
                "year": briefing.year,
                "created_at": briefing.created_at,
                "video_url": video.video_url if video else None,
            })

    return {
        "script_approvals": script_approvals,
        "video_approvals": video_approvals,
    }


# Slack webhook handler for interactive buttons
@router.post("/slack/interactive")
async def slack_interactive(payload: dict):
    """Handle Slack interactive button clicks."""
    # Parse Slack payload
    action = payload.get("actions", [{}])[0]
    action_id = action.get("action_id", "")
    thread_id = action.get("value", "")

    pipeline = get_pipeline()

    if action_id == "approve_script":
        await pipeline.approve_script(thread_id, approved=True)
        return {"text": "Script approved! Generating video..."}

    elif action_id == "reject_script":
        await pipeline.approve_script(thread_id, approved=False, feedback="Rejected via Slack")
        return {"text": "Script rejected."}

    elif action_id == "approve_video":
        await pipeline.approve_video(thread_id, approved=True)
        return {"text": "Video approved! Publishing to social media..."}

    elif action_id == "reject_video":
        await pipeline.approve_video(thread_id, approved=False)
        return {"text": "Video rejected."}

    return {"text": "Unknown action"}

"""API endpoints for cron job management."""

from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from datetime import datetime

from croniter import croniter

from app.models.sources import (
    CronSchedule,
    CronScheduleCreate,
    CronScheduleUpdate,
)
from app.services.database import get_db_service

router = APIRouter()


def validate_cron_expression(expression: str) -> bool:
    """Validate a cron expression."""
    try:
        croniter(expression)
        return True
    except Exception:
        return False


def get_next_run(expression: str) -> datetime:
    """Calculate next run time from cron expression."""
    cron = croniter(expression, datetime.utcnow())
    return cron.get_next(datetime)


def describe_cron(expression: str) -> str:
    """Get human-readable description of cron expression."""
    parts = expression.split()
    if len(parts) != 5:
        return "Invalid expression"

    minute, hour, day, month, weekday = parts

    descriptions = []

    # Weekday
    weekday_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    if weekday != "*":
        if weekday.isdigit():
            descriptions.append(f"Every {weekday_names[int(weekday)]}")
        else:
            descriptions.append(f"Weekday pattern: {weekday}")
    else:
        descriptions.append("Every day")

    # Time
    if hour != "*" and minute != "*":
        descriptions.append(f"at {hour.zfill(2)}:{minute.zfill(2)} UTC")
    elif hour != "*":
        descriptions.append(f"at hour {hour}")

    return " ".join(descriptions)


@router.get("/", response_model=List[CronSchedule])
async def list_schedules():
    """List all cron schedules."""
    db = get_db_service()
    schedules = await db.list_cron_schedules()

    # Calculate next run for each
    for schedule in schedules:
        if schedule.enabled:
            schedule.next_run = get_next_run(schedule.cron_expression)

    return schedules


@router.post("/", response_model=CronSchedule)
async def create_schedule(schedule: CronScheduleCreate):
    """Create a new cron schedule."""
    if not validate_cron_expression(schedule.cron_expression):
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression. Use format: minute hour day month weekday"
        )

    db = get_db_service()
    result = await db.create_cron_schedule(schedule)
    result.next_run = get_next_run(result.cron_expression)
    return result


@router.get("/{schedule_id}", response_model=CronSchedule)
async def get_schedule(schedule_id: UUID):
    """Get a specific schedule."""
    db = get_db_service()
    schedule = await db.get_cron_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if schedule.enabled:
        schedule.next_run = get_next_run(schedule.cron_expression)

    return schedule


@router.patch("/{schedule_id}", response_model=CronSchedule)
async def update_schedule(schedule_id: UUID, update: CronScheduleUpdate):
    """Update a cron schedule."""
    if update.cron_expression and not validate_cron_expression(update.cron_expression):
        raise HTTPException(
            status_code=400,
            detail="Invalid cron expression"
        )

    db = get_db_service()

    existing = await db.get_cron_schedule(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    result = await db.update_cron_schedule(schedule_id, update)
    if result.enabled:
        result.next_run = get_next_run(result.cron_expression)
    return result


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: UUID):
    """Delete a cron schedule."""
    db = get_db_service()

    existing = await db.get_cron_schedule(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    await db.delete_cron_schedule(schedule_id)
    return {"status": "deleted", "id": str(schedule_id)}


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: UUID):
    """Toggle schedule enabled/disabled."""
    db = get_db_service()

    existing = await db.get_cron_schedule(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update = CronScheduleUpdate(enabled=not existing.enabled)
    result = await db.update_cron_schedule(schedule_id, update)

    return {
        "id": str(schedule_id),
        "enabled": result.enabled,
        "next_run": get_next_run(result.cron_expression).isoformat() if result.enabled else None,
    }


@router.post("/{schedule_id}/run-now")
async def run_schedule_now(schedule_id: UUID):
    """Manually trigger a scheduled job."""
    db = get_db_service()

    existing = await db.get_cron_schedule(schedule_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Trigger the pipeline
    from app.agents.pipeline import get_pipeline
    pipeline = get_pipeline()

    result = await pipeline.start_briefing()

    # Update last run time
    await db.update_cron_last_run(schedule_id)

    return {
        "status": "triggered",
        "schedule_id": str(schedule_id),
        "thread_id": result.get("thread_id"),
    }


@router.get("/presets/common")
async def get_common_presets():
    """Get common cron presets."""
    return {
        "presets": [
            {
                "name": "Every Sunday 6 AM UTC (2 PM SGT)",
                "expression": "0 6 * * 0",
                "description": "Weekly on Sunday at 6:00 AM UTC",
            },
            {
                "name": "Every Sunday 8 PM SGT",
                "expression": "0 12 * * 0",
                "description": "Weekly on Sunday at 12:00 PM UTC (8 PM SGT)",
            },
            {
                "name": "Every Monday 8 AM SGT",
                "expression": "0 0 * * 1",
                "description": "Weekly on Monday at 12:00 AM UTC (8 AM SGT)",
            },
            {
                "name": "Twice a week (Wed & Sun)",
                "expression": "0 6 * * 0,3",
                "description": "Wednesday and Sunday at 6:00 AM UTC",
            },
            {
                "name": "Daily at noon SGT",
                "expression": "0 4 * * *",
                "description": "Every day at 4:00 AM UTC (12 PM SGT)",
            },
        ]
    }


@router.post("/validate")
async def validate_expression(expression: str):
    """Validate and describe a cron expression."""
    is_valid = validate_cron_expression(expression)

    if not is_valid:
        return {
            "valid": False,
            "error": "Invalid cron expression",
        }

    return {
        "valid": True,
        "description": describe_cron(expression),
        "next_runs": [
            get_next_run(expression).isoformat()
            for _ in range(3)  # Next 3 runs
        ],
    }

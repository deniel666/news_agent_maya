from supabase import create_client, Client
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import json

from app.core.config import settings
from app.models.schemas import (
    WeeklyBriefing,
    WeeklyBriefingCreate,
    WeeklyBriefingUpdate,
    WeeklyVideo,
    WeeklyVideoCreate,
    SocialPost,
    SocialPostCreate,
    PipelineStatus,
)


class DatabaseService:
    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )

    # Weekly Briefings
    async def create_briefing(self, data: WeeklyBriefingCreate) -> WeeklyBriefing:
        thread_id = f"{data.year}-W{data.week_number:02d}"

        result = self.client.table("weekly_briefings").insert({
            "thread_id": thread_id,
            "year": data.year,
            "week_number": data.week_number,
            "status": PipelineStatus.AGGREGATING.value,
        }).execute()

        return WeeklyBriefing(**result.data[0])

    async def get_briefing(self, briefing_id: UUID) -> Optional[WeeklyBriefing]:
        result = self.client.table("weekly_briefings").select("*").eq(
            "id", str(briefing_id)
        ).execute()

        if result.data:
            return WeeklyBriefing(**result.data[0])
        return None

    async def get_briefing_by_thread(self, thread_id: str) -> Optional[WeeklyBriefing]:
        result = self.client.table("weekly_briefings").select("*").eq(
            "thread_id", thread_id
        ).execute()

        if result.data:
            return WeeklyBriefing(**result.data[0])
        return None

    async def get_briefing_by_week(self, year: int, week: int) -> Optional[WeeklyBriefing]:
        thread_id = f"{year}-W{week:02d}"
        return await self.get_briefing_by_thread(thread_id)

    async def update_briefing(
        self, briefing_id: UUID, data: WeeklyBriefingUpdate
    ) -> WeeklyBriefing:
        update_data = data.model_dump(exclude_none=True)

        if "status" in update_data:
            update_data["status"] = update_data["status"].value

        result = self.client.table("weekly_briefings").update(
            update_data
        ).eq("id", str(briefing_id)).execute()

        return WeeklyBriefing(**result.data[0])

    async def list_briefings(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[PipelineStatus] = None,
    ) -> List[WeeklyBriefing]:
        query = self.client.table("weekly_briefings").select("*")

        if status:
            query = query.eq("status", status.value)

        result = query.order(
            "created_at", desc=True
        ).range(offset, offset + limit - 1).execute()

        return [WeeklyBriefing(**item) for item in result.data]

    async def get_pending_approvals(self) -> List[WeeklyBriefing]:
        result = self.client.table("weekly_briefings").select("*").in_(
            "status", [
                PipelineStatus.AWAITING_SCRIPT_APPROVAL.value,
                PipelineStatus.AWAITING_VIDEO_APPROVAL.value,
            ]
        ).order("created_at", desc=True).execute()

        return [WeeklyBriefing(**item) for item in result.data]

    # Weekly Videos
    async def create_video(self, data: WeeklyVideoCreate) -> WeeklyVideo:
        result = self.client.table("weekly_videos").insert({
            "briefing_id": str(data.briefing_id),
            "heygen_video_id": data.heygen_video_id,
            "status": "queued",
        }).execute()

        return WeeklyVideo(**result.data[0])

    async def get_video(self, video_id: UUID) -> Optional[WeeklyVideo]:
        result = self.client.table("weekly_videos").select("*").eq(
            "id", str(video_id)
        ).execute()

        if result.data:
            return WeeklyVideo(**result.data[0])
        return None

    async def get_video_by_briefing(self, briefing_id: UUID) -> Optional[WeeklyVideo]:
        result = self.client.table("weekly_videos").select("*").eq(
            "briefing_id", str(briefing_id)
        ).order("created_at", desc=True).limit(1).execute()

        if result.data:
            return WeeklyVideo(**result.data[0])
        return None

    async def update_video(
        self,
        video_id: UUID,
        video_url: Optional[str] = None,
        status: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> WeeklyVideo:
        update_data = {}
        if video_url:
            update_data["video_url"] = video_url
        if status:
            update_data["status"] = status
        if duration_seconds:
            update_data["duration_seconds"] = duration_seconds

        result = self.client.table("weekly_videos").update(
            update_data
        ).eq("id", str(video_id)).execute()

        return WeeklyVideo(**result.data[0])

    async def list_videos(self, limit: int = 20) -> List[WeeklyVideo]:
        result = self.client.table("weekly_videos").select("*").order(
            "created_at", desc=True
        ).limit(limit).execute()

        return [WeeklyVideo(**item) for item in result.data]

    # Social Posts
    async def create_post(self, data: SocialPostCreate) -> SocialPost:
        result = self.client.table("social_posts").insert({
            "video_id": str(data.video_id),
            "platform": data.platform,
            "caption": data.caption,
            "status": "draft",
        }).execute()

        return SocialPost(**result.data[0])

    async def update_post(
        self,
        post_id: UUID,
        status: Optional[str] = None,
        post_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ) -> SocialPost:
        update_data = {}
        if status:
            update_data["status"] = status
        if post_url:
            update_data["post_url"] = post_url
        if published_at:
            update_data["published_at"] = published_at.isoformat()

        result = self.client.table("social_posts").update(
            update_data
        ).eq("id", str(post_id)).execute()

        return SocialPost(**result.data[0])

    async def get_posts_by_video(self, video_id: UUID) -> List[SocialPost]:
        result = self.client.table("social_posts").select("*").eq(
            "video_id", str(video_id)
        ).execute()

        return [SocialPost(**item) for item in result.data]

    # Dashboard Stats
    async def get_dashboard_stats(self) -> dict:
        briefings = self.client.table("weekly_briefings").select(
            "id, status", count="exact"
        ).execute()

        videos = self.client.table("weekly_videos").select(
            "id", count="exact"
        ).execute()

        posts = self.client.table("social_posts").select(
            "id", count="exact"
        ).execute()

        total_briefings = briefings.count or 0
        completed = len([
            b for b in briefings.data
            if b["status"] == PipelineStatus.COMPLETED.value
        ])
        pending = len([
            b for b in briefings.data
            if b["status"] in [
                PipelineStatus.AWAITING_SCRIPT_APPROVAL.value,
                PipelineStatus.AWAITING_VIDEO_APPROVAL.value,
            ]
        ])

        return {
            "total_briefings": total_briefings,
            "completed_briefings": completed,
            "pending_approvals": pending,
            "total_videos": videos.count or 0,
            "total_posts": posts.count or 0,
        }


_db_service: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

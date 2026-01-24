from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
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

# Check if Supabase is configured
SUPABASE_ENABLED = bool(settings.supabase_url and settings.supabase_key and 
                         not settings.supabase_url.startswith("https://your-"))

if SUPABASE_ENABLED:
    from supabase import create_client, Client


class DatabaseService:
    def __init__(self):
        if SUPABASE_ENABLED:
            self.client: Client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            self.mock_mode = False
        else:
            print("⚠️  Supabase not configured - running in mock mode")
            self.client = None
            self.mock_mode = True
            # In-memory storage for mock mode
            self._briefings: dict = {}
            self._videos: dict = {}
            self._posts: dict = {}

    # Weekly Briefings
    async def create_briefing(self, data: WeeklyBriefingCreate) -> WeeklyBriefing:
        thread_id = f"{data.year}-W{data.week_number:02d}"

        if self.mock_mode:
            briefing_id = uuid4()
            briefing_data = {
                "id": briefing_id,
                "thread_id": thread_id,
                "year": data.year,
                "week_number": data.week_number,
                "status": PipelineStatus.AGGREGATING,
                "raw_news": None,
                "synthesized_script": None,
                "final_caption": None,
                "approved_script": False,
                "approved_video": False,
                "script_feedback": None,
                "video_feedback": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            self._briefings[str(briefing_id)] = briefing_data
            return WeeklyBriefing(**briefing_data)

        result = self.client.table("weekly_briefings").insert({
            "thread_id": thread_id,
            "year": data.year,
            "week_number": data.week_number,
            "status": PipelineStatus.AGGREGATING.value,
        }).execute()

        return WeeklyBriefing(**result.data[0])

    async def get_briefing(self, briefing_id: UUID) -> Optional[WeeklyBriefing]:
        if self.mock_mode:
            data = self._briefings.get(str(briefing_id))
            return WeeklyBriefing(**data) if data else None

        result = self.client.table("weekly_briefings").select("*").eq(
            "id", str(briefing_id)
        ).execute()

        if result.data:
            return WeeklyBriefing(**result.data[0])
        return None

    async def get_briefing_by_thread(self, thread_id: str) -> Optional[WeeklyBriefing]:
        if self.mock_mode:
            for data in self._briefings.values():
                if data["thread_id"] == thread_id:
                    return WeeklyBriefing(**data)
            return None

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

        if self.mock_mode:
            if str(briefing_id) in self._briefings:
                self._briefings[str(briefing_id)].update(update_data)
                self._briefings[str(briefing_id)]["updated_at"] = datetime.utcnow()
                return WeeklyBriefing(**self._briefings[str(briefing_id)])
            raise ValueError(f"Briefing {briefing_id} not found")

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
        if self.mock_mode:
            briefings = list(self._briefings.values())
            if status:
                briefings = [b for b in briefings if b["status"] == status]
            briefings.sort(key=lambda x: x["created_at"], reverse=True)
            return [WeeklyBriefing(**b) for b in briefings[offset:offset + limit]]

        query = self.client.table("weekly_briefings").select("*")

        if status:
            query = query.eq("status", status.value)

        result = query.order(
            "created_at", desc=True
        ).range(offset, offset + limit - 1).execute()

        return [WeeklyBriefing(**item) for item in result.data]

    async def get_pending_approvals(self) -> List[WeeklyBriefing]:
        if self.mock_mode:
            pending_statuses = [
                PipelineStatus.AWAITING_SCRIPT_APPROVAL,
                PipelineStatus.AWAITING_VIDEO_APPROVAL,
            ]
            briefings = [
                b for b in self._briefings.values()
                if b["status"] in pending_statuses
            ]
            briefings.sort(key=lambda x: x["created_at"], reverse=True)
            return [WeeklyBriefing(**b) for b in briefings]

        result = self.client.table("weekly_briefings").select("*").in_(
            "status", [
                PipelineStatus.AWAITING_SCRIPT_APPROVAL.value,
                PipelineStatus.AWAITING_VIDEO_APPROVAL.value,
            ]
        ).order("created_at", desc=True).execute()

        return [WeeklyBriefing(**item) for item in result.data]

    # Weekly Videos
    async def create_video(self, data: WeeklyVideoCreate) -> WeeklyVideo:
        if self.mock_mode:
            video_id = uuid4()
            video_data = {
                "id": video_id,
                "briefing_id": data.briefing_id,
                "heygen_video_id": data.heygen_video_id,
                "video_url": None,
                "status": "queued",
                "duration_seconds": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            self._videos[str(video_id)] = video_data
            return WeeklyVideo(**video_data)

        result = self.client.table("weekly_videos").insert({
            "briefing_id": str(data.briefing_id),
            "heygen_video_id": data.heygen_video_id,
            "status": "queued",
        }).execute()

        return WeeklyVideo(**result.data[0])

    async def get_video(self, video_id: UUID) -> Optional[WeeklyVideo]:
        if self.mock_mode:
            data = self._videos.get(str(video_id))
            return WeeklyVideo(**data) if data else None

        result = self.client.table("weekly_videos").select("*").eq(
            "id", str(video_id)
        ).execute()

        if result.data:
            return WeeklyVideo(**result.data[0])
        return None

    async def get_video_by_briefing(self, briefing_id: UUID) -> Optional[WeeklyVideo]:
        if self.mock_mode:
            videos = [v for v in self._videos.values() if v["briefing_id"] == briefing_id]
            if videos:
                videos.sort(key=lambda x: x["created_at"], reverse=True)
                return WeeklyVideo(**videos[0])
            return None

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

        if self.mock_mode:
            if str(video_id) in self._videos:
                self._videos[str(video_id)].update(update_data)
                self._videos[str(video_id)]["updated_at"] = datetime.utcnow()
                return WeeklyVideo(**self._videos[str(video_id)])
            raise ValueError(f"Video {video_id} not found")

        result = self.client.table("weekly_videos").update(
            update_data
        ).eq("id", str(video_id)).execute()

        return WeeklyVideo(**result.data[0])

    async def list_videos(self, limit: int = 20) -> List[WeeklyVideo]:
        if self.mock_mode:
            videos = list(self._videos.values())
            videos.sort(key=lambda x: x["created_at"], reverse=True)
            return [WeeklyVideo(**v) for v in videos[:limit]]

        result = self.client.table("weekly_videos").select("*").order(
            "created_at", desc=True
        ).limit(limit).execute()

        return [WeeklyVideo(**item) for item in result.data]

    # Social Posts
    async def create_post(self, data: SocialPostCreate) -> SocialPost:
        if self.mock_mode:
            post_id = uuid4()
            post_data = {
                "id": post_id,
                "video_id": data.video_id,
                "platform": data.platform,
                "caption": data.caption,
                "post_url": None,
                "status": "draft",
                "published_at": None,
                "created_at": datetime.utcnow(),
            }
            self._posts[str(post_id)] = post_data
            return SocialPost(**post_data)

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
            update_data["published_at"] = published_at

        if self.mock_mode:
            if str(post_id) in self._posts:
                self._posts[str(post_id)].update(update_data)
                return SocialPost(**self._posts[str(post_id)])
            raise ValueError(f"Post {post_id} not found")

        if published_at:
            update_data["published_at"] = published_at.isoformat()

        result = self.client.table("social_posts").update(
            update_data
        ).eq("id", str(post_id)).execute()

        return SocialPost(**result.data[0])

    async def get_posts_by_video(self, video_id: UUID) -> List[SocialPost]:
        if self.mock_mode:
            posts = [p for p in self._posts.values() if p["video_id"] == video_id]
            return [SocialPost(**p) for p in posts]

        result = self.client.table("social_posts").select("*").eq(
            "video_id", str(video_id)
        ).execute()

        return [SocialPost(**item) for item in result.data]

    # Dashboard Stats
    async def get_dashboard_stats(self) -> dict:
        if self.mock_mode:
            total_briefings = len(self._briefings)
            completed = len([
                b for b in self._briefings.values()
                if b["status"] == PipelineStatus.COMPLETED
            ])
            pending = len([
                b for b in self._briefings.values()
                if b["status"] in [
                    PipelineStatus.AWAITING_SCRIPT_APPROVAL,
                    PipelineStatus.AWAITING_VIDEO_APPROVAL,
                ]
            ])
            return {
                "total_briefings": total_briefings,
                "completed_briefings": completed,
                "pending_approvals": pending,
                "total_videos": len(self._videos),
                "total_posts": len(self._posts),
            }

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

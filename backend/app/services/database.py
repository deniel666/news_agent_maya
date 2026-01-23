from supabase import create_client, Client
from typing import Optional, List, Any
from datetime import datetime, timedelta
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

    # ==================
    # Content Library - Stories
    # ==================

    async def list_stories(
        self,
        status: Optional[StoryStatus] = None,
        story_type: Optional[StoryType] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        featured: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[StoryWithAssets]:
        query = self.client.table("stories").select("*")

        if status:
            query = query.eq("status", status.value)
        if story_type:
            query = query.eq("story_type", story_type.value)
        if featured is not None:
            query = query.eq("featured", featured)
        if tag:
            query = query.contains("tags", [tag])
        if search:
            query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")

        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        stories = []
        for item in result.data:
            story = StoryWithAssets(**item, videos=[], publish_records=[])
            # Get videos and publish records
            videos = await self.list_videos_by_story(story.id)
            records = await self.list_publish_records_by_story(story.id)
            story.videos = videos
            story.publish_records = records
            stories.append(story)

        return stories

    async def create_story(self, data: StoryCreate) -> Story:
        insert_data = {
            "title": data.title,
            "description": data.description,
            "source_url": data.source_url,
            "story_type": data.story_type.value,
            "status": StoryStatus.DRAFT.value,
            "tags": data.tags,
            "featured": False,
        }

        result = self.client.table("stories").insert(insert_data).execute()
        return Story(**result.data[0])

    async def get_story(self, story_id: UUID) -> Optional[Story]:
        result = self.client.table("stories").select("*").eq("id", str(story_id)).execute()
        if result.data:
            return Story(**result.data[0])
        return None

    async def get_story_with_assets(self, story_id: UUID) -> Optional[StoryWithAssets]:
        result = self.client.table("stories").select("*").eq("id", str(story_id)).execute()
        if not result.data:
            return None

        story = StoryWithAssets(**result.data[0], videos=[], publish_records=[])
        story.videos = await self.list_videos_by_story(story_id)
        story.publish_records = await self.list_publish_records_by_story(story_id)
        return story

    async def update_story(self, story_id: UUID, data: StoryUpdate) -> Story:
        update_data = data.model_dump(exclude_none=True)

        if "status" in update_data and isinstance(update_data["status"], StoryStatus):
            update_data["status"] = update_data["status"].value

        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = self.client.table("stories").update(update_data).eq("id", str(story_id)).execute()
        return Story(**result.data[0])

    async def update_story_scripts(
        self,
        story_id: UUID,
        script_en: Optional[str] = None,
        script_ms: Optional[str] = None,
    ) -> Story:
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        if script_en is not None:
            update_data["script_en"] = script_en
        if script_ms is not None:
            update_data["script_ms"] = script_ms

        result = self.client.table("stories").update(update_data).eq("id", str(story_id)).execute()
        return Story(**result.data[0])

    async def delete_story(self, story_id: UUID) -> None:
        # Delete related records first
        self.client.table("publish_records").delete().eq("story_id", str(story_id)).execute()
        self.client.table("video_assets").delete().eq("story_id", str(story_id)).execute()
        self.client.table("stories").delete().eq("id", str(story_id)).execute()

    async def link_briefing_to_story(self, briefing_id: UUID, story_id: UUID) -> None:
        self.client.table("stories").update({
            "briefing_id": str(briefing_id),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(story_id)).execute()

    async def link_ondemand_to_story(self, job_id: UUID, story_id: UUID) -> None:
        self.client.table("stories").update({
            "ondemand_job_id": str(job_id),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(story_id)).execute()

    # ==================
    # Content Library - Video Assets
    # ==================

    async def list_videos_by_story(self, story_id: UUID) -> List[VideoAsset]:
        result = self.client.table("video_assets").select("*").eq(
            "story_id", str(story_id)
        ).order("created_at", desc=True).execute()

        return [VideoAsset(**item) for item in result.data]

    async def create_video_asset(self, data: VideoAssetCreate) -> VideoAsset:
        insert_data = {
            "story_id": str(data.story_id),
            "language": data.language,
            "video_url": data.video_url,
            "thumbnail_url": data.thumbnail_url,
            "duration_seconds": data.duration_seconds,
            "heygen_video_id": data.heygen_video_id,
        }

        result = self.client.table("video_assets").insert(insert_data).execute()
        return VideoAsset(**result.data[0])

    async def delete_video_asset(self, video_id: UUID) -> None:
        # Delete related publish records first
        self.client.table("publish_records").delete().eq("video_id", str(video_id)).execute()
        self.client.table("video_assets").delete().eq("id", str(video_id)).execute()

    # ==================
    # Content Library - Publish Records
    # ==================

    async def list_publish_records_by_story(self, story_id: UUID) -> List[PublishRecord]:
        result = self.client.table("publish_records").select("*").eq(
            "story_id", str(story_id)
        ).order("created_at", desc=True).execute()

        return [PublishRecord(**item) for item in result.data]

    async def create_publish_record(self, data: PublishRecordCreate) -> PublishRecord:
        insert_data = {
            "story_id": str(data.story_id),
            "video_id": str(data.video_id),
            "platform": data.platform.value if hasattr(data.platform, 'value') else data.platform,
            "language": data.language,
            "caption": data.caption,
            "scheduled_at": data.scheduled_at.isoformat() if data.scheduled_at else None,
            "status": "pending",
        }

        result = self.client.table("publish_records").insert(insert_data).execute()
        return PublishRecord(**result.data[0])

    async def update_publish_record(self, record_id: UUID, updates: dict) -> PublishRecord:
        if "published_at" in updates and isinstance(updates["published_at"], datetime):
            updates["published_at"] = updates["published_at"].isoformat()

        result = self.client.table("publish_records").update(updates).eq("id", str(record_id)).execute()
        return PublishRecord(**result.data[0])

    # ==================
    # Content Library - Stats & Tags
    # ==================

    async def get_content_stats(self) -> ContentStats:
        # Get story counts
        stories = self.client.table("stories").select("status, story_type", count="exact").execute()

        stories_by_status = {}
        stories_by_type = {}
        for s in stories.data:
            status = s["status"]
            stype = s["story_type"]
            stories_by_status[status] = stories_by_status.get(status, 0) + 1
            stories_by_type[stype] = stories_by_type.get(stype, 0) + 1

        # Get video counts
        videos = self.client.table("video_assets").select("language", count="exact").execute()
        videos_by_language = {}
        for v in videos.data:
            lang = v["language"]
            videos_by_language[lang] = videos_by_language.get(lang, 0) + 1

        # Get publish counts
        publishes = self.client.table("publish_records").select("platform, status", count="exact").execute()
        published_by_platform = {}
        total_published = 0
        for p in publishes.data:
            if p["status"] == "published":
                platform = p["platform"]
                published_by_platform[platform] = published_by_platform.get(platform, 0) + 1
                total_published += 1

        # Get recent counts
        now = datetime.utcnow()
        week_ago = (now - timedelta(days=7)).isoformat()
        month_ago = (now - timedelta(days=30)).isoformat()

        this_week = self.client.table("stories").select("id", count="exact").gte("created_at", week_ago).execute()
        this_month = self.client.table("stories").select("id", count="exact").gte("created_at", month_ago).execute()

        return ContentStats(
            total_stories=stories.count or 0,
            stories_by_status=stories_by_status,
            stories_by_type=stories_by_type,
            total_videos=videos.count or 0,
            videos_by_language=videos_by_language,
            total_published=total_published,
            published_by_platform=published_by_platform,
            this_week=this_week.count or 0,
            this_month=this_month.count or 0,
        )

    async def get_all_tags(self) -> List[str]:
        result = self.client.table("stories").select("tags").execute()

        all_tags = set()
        for item in result.data:
            if item.get("tags"):
                all_tags.update(item["tags"])

        return sorted(list(all_tags))

    # ==================
    # On-Demand Jobs
    # ==================

    async def get_ondemand_job(self, job_id: UUID) -> Optional[Any]:
        result = self.client.table("ondemand_jobs").select("*").eq("id", str(job_id)).execute()
        if result.data:
            return result.data[0]  # Return as dict since we don't have the model imported
        return None


_db_service: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

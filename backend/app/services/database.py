from supabase import create_client, Client
from typing import Optional, List, Any
from datetime import datetime, timedelta
from uuid import UUID
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
from app.models.sources import OnDemandJob, Language, NewsSource, NewsSourceCreate, NewsSourceUpdate, SourceType

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
            self._ondemand_jobs: dict = {}
            self._sources: dict = {}

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

    async def get_briefings_by_threads(self, thread_ids: List[str]) -> List[WeeklyBriefing]:
        if not thread_ids:
            return []

        if self.mock_mode:
            briefings = []
            for thread_id in thread_ids:
                for data in self._briefings.values():
                    if data["thread_id"] == thread_id:
                        briefings.append(WeeklyBriefing(**data))
                        break
            return briefings

        result = self.client.table("weekly_briefings").select("*").in_(
            "thread_id", thread_ids
        ).execute()

        return [WeeklyBriefing(**item) for item in result.data]

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

    # On-Demand Jobs
    async def create_ondemand_job(
        self,
        article_url: str,
        title: Optional[str] = None,
        languages: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
    ) -> OnDemandJob:
        """Create a new on-demand job."""
        if self.mock_mode:
            job_id = uuid4()
            job_data = {
                "id": job_id,
                "article_url": article_url,
                "title": title,
                "original_content": None,
                "script_en": None,
                "script_ms": None,
                "video_url_en": None,
                "video_url_ms": None,
                "caption_en": None,
                "caption_ms": None,
                "languages": languages or ["en"],
                "platforms": platforms or ["instagram", "facebook"],
                "status": "pending",
                "error": None,
                "created_at": datetime.utcnow(),
                "approved_at": None,
                "published_at": None,
            }
            self._ondemand_jobs[str(job_id)] = job_data
            return OnDemandJob(**job_data)

        result = self.client.table("ondemand_jobs").insert({
            "article_url": article_url,
            "title": title,
            "languages": languages or ["en"],
            "platforms": platforms or ["instagram", "facebook"],
            "status": "pending",
        }).execute()

        return OnDemandJob(**result.data[0])

    async def get_ondemand_job(self, job_id: UUID) -> Optional[OnDemandJob]:
        """Get an on-demand job by ID."""
        if self.mock_mode:
            data = self._ondemand_jobs.get(str(job_id))
            return OnDemandJob(**data) if data else None

        result = self.client.table("ondemand_jobs").select("*").eq(
            "id", str(job_id)
        ).execute()

        if result.data:
            return OnDemandJob(**result.data[0])
        return None

    async def list_ondemand_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[OnDemandJob]:
        """List on-demand jobs."""
        if self.mock_mode:
            jobs = list(self._ondemand_jobs.values())
            if status:
                jobs = [j for j in jobs if j["status"] == status]
            jobs.sort(key=lambda x: x["created_at"], reverse=True)
            return [OnDemandJob(**j) for j in jobs[:limit]]

        query = self.client.table("ondemand_jobs").select("*")

        if status:
            query = query.eq("status", status)

        result = query.order(
            "created_at", desc=True
        ).limit(limit).execute()

        return [OnDemandJob(**item) for item in result.data]

    async def update_ondemand_status(
        self,
        job_id: UUID,
        status: str,
        error: Optional[str] = None,
    ) -> OnDemandJob:
        """Update on-demand job status."""
        update_data = {"status": status}
        if error:
            update_data["error"] = error

        if self.mock_mode:
            if str(job_id) in self._ondemand_jobs:
                self._ondemand_jobs[str(job_id)].update(update_data)
                return OnDemandJob(**self._ondemand_jobs[str(job_id)])
            raise ValueError(f"Job {job_id} not found")

        result = self.client.table("ondemand_jobs").update(
            update_data
        ).eq("id", str(job_id)).execute()

        return OnDemandJob(**result.data[0])

    async def update_ondemand_scripts(
        self,
        job_id: UUID,
        scripts: dict,
    ) -> OnDemandJob:
        """Update on-demand job scripts."""
        update_data = {}
        if "en" in scripts:
            update_data["script_en"] = scripts["en"]
        if "ms" in scripts:
            update_data["script_ms"] = scripts["ms"]

        if self.mock_mode:
            if str(job_id) in self._ondemand_jobs:
                self._ondemand_jobs[str(job_id)].update(update_data)
                return OnDemandJob(**self._ondemand_jobs[str(job_id)])
            raise ValueError(f"Job {job_id} not found")

        result = self.client.table("ondemand_jobs").update(
            update_data
        ).eq("id", str(job_id)).execute()

        return OnDemandJob(**result.data[0])

    async def delete_ondemand_job(self, job_id: UUID) -> bool:
        """Delete an on-demand job."""
        if self.mock_mode:
            if str(job_id) in self._ondemand_jobs:
                del self._ondemand_jobs[str(job_id)]
                return True
            return False

        self.client.table("ondemand_jobs").delete().eq(
            "id", str(job_id)
        ).execute()
        return True

    # News Sources
    async def create_source(self, data: NewsSourceCreate) -> NewsSource:
        """Create a new news source."""
        if self.mock_mode:
            source_id = uuid4()
            source_data = {
                "id": source_id,
                "name": data.name,
                "source_type": data.source_type,
                "url": data.url,
                "category": data.category,
                "enabled": data.enabled,
                "created_at": datetime.utcnow(),
                "updated_at": None,
            }
            self._sources[str(source_id)] = source_data
            return NewsSource(**source_data)

        result = self.client.table("news_sources").insert({
            "name": data.name,
            "source_type": data.source_type.value,
            "url": data.url,
            "category": data.category,
            "enabled": data.enabled,
        }).execute()

        return NewsSource(**result.data[0])

    async def get_source(self, source_id: UUID) -> Optional[NewsSource]:
        """Get a source by ID."""
        if self.mock_mode:
            data = self._sources.get(str(source_id))
            return NewsSource(**data) if data else None

        result = self.client.table("news_sources").select("*").eq(
            "id", str(source_id)
        ).execute()

        if result.data:
            return NewsSource(**result.data[0])
        return None

    async def list_sources(
        self,
        source_type: Optional[SourceType] = None,
        enabled: Optional[bool] = None,
    ) -> List[NewsSource]:
        """List news sources."""
        if self.mock_mode:
            sources = list(self._sources.values())
            if source_type:
                sources = [s for s in sources if s["source_type"] == source_type]
            if enabled is not None:
                sources = [s for s in sources if s["enabled"] == enabled]
            sources.sort(key=lambda x: x["created_at"], reverse=True)
            return [NewsSource(**s) for s in sources]

        query = self.client.table("news_sources").select("*")

        if source_type:
            query = query.eq("source_type", source_type.value)
        if enabled is not None:
            query = query.eq("enabled", enabled)

        result = query.order("created_at", desc=True).execute()

        return [NewsSource(**item) for item in result.data]

    async def update_source(
        self,
        source_id: UUID,
        data: NewsSourceUpdate,
    ) -> NewsSource:
        """Update a news source."""
        update_data = data.model_dump(exclude_none=True)

        if self.mock_mode:
            if str(source_id) in self._sources:
                self._sources[str(source_id)].update(update_data)
                self._sources[str(source_id)]["updated_at"] = datetime.utcnow()
                return NewsSource(**self._sources[str(source_id)])
            raise ValueError(f"Source {source_id} not found")

        result = self.client.table("news_sources").update(
            update_data
        ).eq("id", str(source_id)).execute()

        return NewsSource(**result.data[0])

    async def delete_source(self, source_id: UUID) -> bool:
        """Delete a news source."""
        if self.mock_mode:
            if str(source_id) in self._sources:
                del self._sources[str(source_id)]
                return True
            return False

        self.client.table("news_sources").delete().eq(
            "id", str(source_id)
        ).execute()
        return True

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

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings


# Default hashtags for Maya content
MAYA_HASHTAGS = [
    "MayaNews", "SEANews", "MalaysiaNews", "SingaporeNews",
    "AINews", "TechNews", "WeeklyUpdate", "AsiaNews"
]

PLATFORM_LIMITS = {
    "instagram": 2200,
    "tiktok": 4000,
    "youtube": 100,
    "linkedin": 3000,
    "twitter": 280,
}


class BlotatoClient:
    """Client for Blotato social media posting API."""

    def __init__(self):
        self.api_key = settings.blotato_api_key
        self.base_url = settings.blotato_base_url

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_post(
        self,
        platform: str,
        content: str,
        media_url: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Create a post on a specific platform."""
        payload = {
            "content": content,
            "platform": platform,
        }

        if media_url:
            payload["media_url"] = media_url

        if scheduled_at:
            payload["scheduled_at"] = scheduled_at.isoformat()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/posts",
                headers=self.headers,
                json=payload,
                timeout=60.0,
            )

            if response.status_code not in [200, 201]:
                raise Exception(f"Blotato API error: {response.text}")

            return response.json()

    async def schedule_multi_platform(
        self,
        video_url: str,
        caption: str,
        platforms: List[str],
        hashtags: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Schedule video to multiple platforms."""
        hashtags = hashtags or MAYA_HASHTAGS
        results = []

        for platform in platforms:
            adapted_caption = self._adapt_caption(caption, hashtags, platform)

            try:
                result = await self.create_post(
                    platform=platform,
                    content=adapted_caption,
                    media_url=video_url,
                    scheduled_at=scheduled_at,
                )
                results.append({
                    "platform": platform,
                    "status": "success",
                    "post_id": result.get("id"),
                    "post_url": result.get("url"),
                })
            except Exception as e:
                results.append({
                    "platform": platform,
                    "status": "error",
                    "error": str(e),
                })

        return {"posts": results}

    async def get_post_status(self, post_id: str) -> Dict[str, Any]:
        """Get the status of a post."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/posts/{post_id}",
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"Blotato API error: {response.text}")

            return response.json()

    async def list_connected_accounts(self) -> List[Dict[str, Any]]:
        """List connected social media accounts."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts",
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"Blotato API error: {response.text}")

            return response.json().get("accounts", [])

    def _adapt_caption(
        self,
        caption: str,
        hashtags: List[str],
        platform: str,
    ) -> str:
        """Adapt caption for specific platform limits."""
        hashtag_str = " ".join([f"#{tag}" for tag in hashtags[:10]])
        full = f"{caption}\n\n{hashtag_str}"

        max_len = PLATFORM_LIMITS.get(platform, 2000)

        if len(full) > max_len:
            # Truncate caption but keep hashtags
            available = max_len - len(hashtag_str) - 10
            full = f"{caption[:available]}...\n\n{hashtag_str}"

        return full

    @staticmethod
    def generate_caption(
        local_summary: str,
        business_summary: str,
        ai_summary: str,
        week_number: int,
        year: int,
    ) -> str:
        """Generate a social media caption from script summaries."""
        caption = f"""🎙️ Maya's Week {week_number} News Roundup

Your weekly dose of Southeast Asian news, business updates, and AI developments!

📍 {local_summary[:100]}...
💼 {business_summary[:100]}...
🤖 {ai_summary[:100]}...

Watch the full briefing for complete coverage!
"""
        return caption


# Singleton
_blotato_client: Optional[BlotatoClient] = None


def get_blotato_client() -> BlotatoClient:
    global _blotato_client
    if _blotato_client is None:
        _blotato_client = BlotatoClient()
    return _blotato_client

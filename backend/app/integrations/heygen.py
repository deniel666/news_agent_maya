import httpx
import asyncio
from typing import Optional, Dict, Any
from enum import Enum

from app.core.config import settings


class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HeyGenClient:
    """Client for HeyGen video generation API."""

    def __init__(self):
        self.api_key = settings.heygen_api_key
        self.base_url = "https://api.heygen.com"
        self.avatar_id = settings.maya_avatar_id
        self.voice_id = settings.maya_voice_id

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    async def generate_video(
        self,
        script: str,
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        locale: str = "en-SG",
        speed: float = 1.0,
        background_color: str = "#1a1a2e",
        aspect_ratio: str = "9:16",
    ) -> Dict[str, Any]:
        """
        Generate a video with the given script.

        Args:
            script: The text script for the avatar to speak
            avatar_id: HeyGen avatar ID (defaults to Maya)
            voice_id: HeyGen voice ID (defaults to Maya's voice)
            locale: Voice locale for accent (e.g., 'en-SG', 'ms-MY', 'en-MY')
            speed: Speech speed multiplier (0.5 to 2.0)
            background_color: Hex color for background
            aspect_ratio: Video aspect ratio

        Returns:
            Dict with video_id and status
        """
        avatar_id = avatar_id or self.avatar_id
        voice_id = voice_id or self.voice_id

        # Set dimensions based on aspect ratio
        if aspect_ratio == "9:16":
            width, height = 1080, 1920  # Vertical for TikTok/Reels
        elif aspect_ratio == "16:9":
            width, height = 1920, 1080  # Horizontal for YouTube
        else:
            width, height = 1080, 1080  # Square

        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                    "locale": locale,
                    "speed": speed
                },
                "background": {
                    "type": "color",
                    "value": background_color
                }
            }],
            "dimension": {"width": width, "height": height},
            "aspect_ratio": aspect_ratio
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/video/generate",
                headers=self.headers,
                json=payload,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise Exception(f"HeyGen API error: {response.text}")

            data = response.json()
            return {
                "video_id": data["data"]["video_id"],
                "status": VideoStatus.PENDING,
            }

    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get the status of a video generation job."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/video_status.get",
                headers=self.headers,
                params={"video_id": video_id},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"HeyGen API error: {response.text}")

            data = response.json()["data"]

            status_map = {
                "pending": VideoStatus.PENDING,
                "processing": VideoStatus.PROCESSING,
                "completed": VideoStatus.COMPLETED,
                "failed": VideoStatus.FAILED,
            }

            return {
                "video_id": video_id,
                "status": status_map.get(data["status"], VideoStatus.PENDING),
                "video_url": data.get("video_url"),
                "duration": data.get("duration"),
                "error": data.get("error"),
            }

    async def wait_for_video(
        self,
        video_id: str,
        timeout_seconds: int = 600,
        poll_interval: int = 10,
    ) -> Dict[str, Any]:
        """Wait for video generation to complete."""
        elapsed = 0

        while elapsed < timeout_seconds:
            status = await self.get_video_status(video_id)

            if status["status"] == VideoStatus.COMPLETED:
                return status
            elif status["status"] == VideoStatus.FAILED:
                raise Exception(f"Video generation failed: {status.get('error')}")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Video generation timed out after {timeout_seconds}s")

    async def list_avatars(self) -> list:
        """List available avatars."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/avatars",
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"HeyGen API error: {response.text}")

            return response.json()["data"]["avatars"]

    async def list_voices(self) -> list:
        """List available voices."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/voices",
                headers=self.headers,
                timeout=30.0,
            )

            if response.status_code != 200:
                raise Exception(f"HeyGen API error: {response.text}")

            return response.json()["data"]["voices"]


# Singleton
_heygen_client: Optional[HeyGenClient] = None


def get_heygen_client() -> HeyGenClient:
    global _heygen_client
    if _heygen_client is None:
        _heygen_client = HeyGenClient()
    return _heygen_client

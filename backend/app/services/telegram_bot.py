"""Telegram bot service for approval notifications."""

import httpx
from typing import Optional, Dict
from urllib.parse import urlencode

from app.core.config import settings


class TelegramBot:
    """Telegram bot for sending approval requests and notifications."""

    def __init__(self):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.callback_base = settings.backend_url

    async def _send_message(
        self,
        text: str,
        reply_markup: Optional[dict] = None,
        parse_mode: str = "HTML",
    ) -> dict:
        """Send a message to the configured chat."""
        if not self.token or not self.chat_id:
            print("Telegram bot not configured")
            return {"ok": False, "error": "Not configured"}

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json=payload,
                timeout=30.0,
            )
            return response.json()

    async def _send_video(
        self,
        video_url: str,
        caption: str,
        reply_markup: Optional[dict] = None,
    ) -> dict:
        """Send a video message."""
        if not self.token or not self.chat_id:
            return {"ok": False, "error": "Not configured"}

        payload = {
            "chat_id": self.chat_id,
            "video": video_url,
            "caption": caption[:1024],  # Telegram caption limit
            "parse_mode": "HTML",
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendVideo",
                json=payload,
                timeout=60.0,
            )
            return response.json()

    def _create_inline_keyboard(self, buttons: list) -> dict:
        """Create inline keyboard markup."""
        return {
            "inline_keyboard": buttons
        }

    async def send_script_approval(
        self,
        job_id: str,
        job_type: str,
        title: str,
        scripts: Dict[str, str],
    ):
        """Send script approval request with inline buttons."""
        # Format message
        message = f"""
<b>📝 Script Approval Required</b>

<b>Type:</b> {job_type.replace('_', ' ').title()}
<b>Title:</b> {title[:100]}

"""
        # Add script previews
        for lang, script in scripts.items():
            lang_name = "English" if lang == "en" else "Bahasa Melayu"
            preview = script[:300] + "..." if len(script) > 300 else script
            message += f"<b>{lang_name}:</b>\n<pre>{preview}</pre>\n\n"

        message += f"""
<b>Job ID:</b> <code>{job_id}</code>

Review the full scripts and approve to generate video.
"""

        # Create approval buttons
        buttons = [
            [
                {
                    "text": "✅ Approve",
                    "callback_data": f"approve_script:{job_id}:{job_type}"
                },
                {
                    "text": "❌ Reject",
                    "callback_data": f"reject_script:{job_id}:{job_type}"
                },
            ],
            [
                {
                    "text": "📝 View Full Scripts",
                    "url": f"{settings.frontend_url}/on-demand/{job_id}"
                },
            ],
        ]

        await self._send_message(
            text=message,
            reply_markup=self._create_inline_keyboard(buttons),
        )

    async def send_video_approval(
        self,
        job_id: str,
        job_type: str,
        video_urls: Dict[str, str],
    ):
        """Send video approval request."""
        message = f"""
<b>🎬 Video Approval Required</b>

<b>Type:</b> {job_type.replace('_', ' ').title()}
<b>Job ID:</b> <code>{job_id}</code>

Videos have been generated and are ready for review.

"""
        # List video URLs
        for lang, url in video_urls.items():
            lang_name = "English" if lang == "en" else "Bahasa Melayu"
            message += f"<b>{lang_name}:</b> <a href='{url}'>View Video</a>\n"

        message += "\nApprove to publish to social media platforms."

        buttons = [
            [
                {
                    "text": "✅ Approve & Publish",
                    "callback_data": f"approve_video:{job_id}:{job_type}"
                },
                {
                    "text": "❌ Reject",
                    "callback_data": f"reject_video:{job_id}:{job_type}"
                },
            ],
            [
                {
                    "text": "🔄 Regenerate Video",
                    "callback_data": f"regenerate_video:{job_id}:{job_type}"
                },
            ],
        ]

        await self._send_message(
            text=message,
            reply_markup=self._create_inline_keyboard(buttons),
        )

    async def send_published_notification(
        self,
        job_id: str,
        platforms: list,
    ):
        """Send notification when video is published."""
        platform_emojis = {
            "instagram": "📸",
            "facebook": "📘",
            "tiktok": "🎵",
            "youtube": "▶️",
        }

        platform_text = "\n".join([
            f"{platform_emojis.get(p, '📱')} {p.title()}"
            for p in platforms
        ])

        message = f"""
<b>✅ Published Successfully!</b>

<b>Job ID:</b> <code>{job_id}</code>

Published to:
{platform_text}

View analytics in the dashboard.
"""

        await self._send_message(text=message)

    async def send_weekly_briefing_approval(
        self,
        thread_id: str,
        week_number: int,
        year: int,
        scripts: Dict[str, str],
    ):
        """Send weekly briefing script approval."""
        message = f"""
<b>📰 Weekly Briefing - Week {week_number}, {year}</b>

Scripts are ready for your review!

<b>Local News:</b>
<pre>{scripts.get('local', 'N/A')[:200]}...</pre>

<b>Business:</b>
<pre>{scripts.get('business', 'N/A')[:200]}...</pre>

<b>AI & Tech:</b>
<pre>{scripts.get('ai', 'N/A')[:200]}...</pre>

<b>Thread ID:</b> <code>{thread_id}</code>
"""

        buttons = [
            [
                {
                    "text": "✅ Approve Scripts",
                    "callback_data": f"approve_script:{thread_id}:weekly"
                },
                {
                    "text": "❌ Reject",
                    "callback_data": f"reject_script:{thread_id}:weekly"
                },
            ],
            [
                {
                    "text": "📝 View & Edit in Dashboard",
                    "url": f"{settings.frontend_url}/briefings/{thread_id}"
                },
            ],
        ]

        await self._send_message(
            text=message,
            reply_markup=self._create_inline_keyboard(buttons),
        )

    async def send_error_notification(
        self,
        job_id: str,
        error: str,
    ):
        """Send error notification."""
        message = f"""
<b>❌ Error Occurred</b>

<b>Job ID:</b> <code>{job_id}</code>
<b>Error:</b> {error[:500]}

Please check the dashboard for details.
"""
        await self._send_message(text=message)


# Webhook handler for Telegram callbacks
async def handle_telegram_callback(callback_data: str) -> dict:
    """Handle Telegram inline button callbacks."""
    parts = callback_data.split(":")
    if len(parts) < 3:
        return {"error": "Invalid callback data"}

    action, job_id, job_type = parts[0], parts[1], parts[2]

    if job_type == "weekly":
        from app.agents.pipeline import get_pipeline
        pipeline = get_pipeline()

        if action == "approve_script":
            result = await pipeline.approve_script(job_id, approved=True)
            return {"status": "approved", "message": "Generating video..."}
        elif action == "reject_script":
            result = await pipeline.approve_script(job_id, approved=False)
            return {"status": "rejected"}
        elif action == "approve_video":
            result = await pipeline.approve_video(job_id, approved=True)
            return {"status": "approved", "message": "Publishing..."}
        elif action == "reject_video":
            result = await pipeline.approve_video(job_id, approved=False)
            return {"status": "rejected"}

    elif job_type == "on_demand":
        from app.services.ondemand import get_ondemand_service
        from app.services.database import get_db_service

        db = get_db_service()
        ondemand = get_ondemand_service()

        if action == "approve_script":
            await ondemand.generate_videos(job_id)
            return {"status": "approved", "message": "Generating video..."}
        elif action == "reject_script":
            await db.update_ondemand_status(job_id, "rejected")
            return {"status": "rejected"}
        elif action == "approve_video":
            await ondemand.publish_to_social(job_id)
            return {"status": "approved", "message": "Publishing..."}
        elif action == "reject_video":
            await db.update_ondemand_status(job_id, "video_rejected")
            return {"status": "rejected"}
        elif action == "regenerate_video":
            await ondemand.generate_videos(job_id)
            return {"status": "regenerating"}

    return {"error": "Unknown action"}


# Singleton
_telegram_bot: Optional[TelegramBot] = None


def get_telegram_bot() -> TelegramBot:
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = TelegramBot()
    return _telegram_bot

import httpx
from typing import Optional, Dict, Any
import json

from app.core.config import settings


class NotificationService:
    """Service for sending notifications via Slack or Telegram."""

    def __init__(self):
        self.slack_webhook = settings.slack_webhook_url
        self.telegram_token = settings.telegram_bot_token
        self.telegram_chat_id = settings.telegram_chat_id

    async def send_script_approval_request(
        self,
        thread_id: str,
        scripts: Dict[str, str],
        week_number: int,
        year: int,
    ) -> bool:
        """Send script approval request notification."""
        message = self._format_script_message(thread_id, scripts, week_number, year)

        if self.slack_webhook:
            return await self._send_slack(message, thread_id, "script")
        elif self.telegram_token and self.telegram_chat_id:
            return await self._send_telegram(message)

        print(f"No notification service configured. Script ready for approval: {thread_id}")
        return False

    async def send_video_approval_request(
        self,
        thread_id: str,
        video_url: str,
        caption: str,
    ) -> bool:
        """Send video approval request notification."""
        message = self._format_video_message(thread_id, video_url, caption)

        if self.slack_webhook:
            return await self._send_slack(message, thread_id, "video")
        elif self.telegram_token and self.telegram_chat_id:
            return await self._send_telegram(message)

        print(f"No notification service configured. Video ready for approval: {thread_id}")
        return False

    async def send_status_update(
        self,
        thread_id: str,
        status: str,
        details: Optional[str] = None,
    ) -> bool:
        """Send pipeline status update."""
        message = f"*Maya Pipeline Update*\n\nThread: `{thread_id}`\nStatus: {status}"
        if details:
            message += f"\n\nDetails: {details}"

        if self.slack_webhook:
            await self._send_slack_simple(message)
            return True
        elif self.telegram_token and self.telegram_chat_id:
            return await self._send_telegram(message)

        return False

    def _format_script_message(
        self,
        thread_id: str,
        scripts: Dict[str, str],
        week_number: int,
        year: int,
    ) -> str:
        """Format script approval message."""
        message = f"""*Maya Weekly Briefing - Week {week_number}, {year}*

Scripts are ready for your review!

*Local & International News:*
{scripts.get('local', 'N/A')[:500]}{'...' if len(scripts.get('local', '')) > 500 else ''}

*Business News:*
{scripts.get('business', 'N/A')[:500]}{'...' if len(scripts.get('business', '')) > 500 else ''}

*AI & Tech News:*
{scripts.get('ai', 'N/A')[:500]}{'...' if len(scripts.get('ai', '')) > 500 else ''}

Review and approve at: {settings.frontend_url}/briefings/{thread_id}
"""
        return message

    def _format_video_message(
        self,
        thread_id: str,
        video_url: str,
        caption: str,
    ) -> str:
        """Format video approval message."""
        message = f"""*Maya Video Ready for Review*

Thread: `{thread_id}`

Video URL: {video_url}

*Caption:*
{caption[:500]}{'...' if len(caption) > 500 else ''}

Review and approve at: {settings.frontend_url}/briefings/{thread_id}
"""
        return message

    async def _send_slack(
        self,
        message: str,
        thread_id: str,
        approval_type: str,
    ) -> bool:
        """Send Slack message with approval buttons."""
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": f"approve_{approval_type}",
                        "value": thread_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": f"reject_{approval_type}",
                        "value": thread_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Details"},
                        "url": f"{settings.frontend_url}/briefings/{thread_id}",
                    }
                ]
            }
        ]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook,
                    json={"blocks": blocks},
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Slack notification error: {e}")
            return False

    async def _send_slack_simple(self, message: str) -> bool:
        """Send simple Slack message without buttons."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook,
                    json={"text": message},
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Slack notification error: {e}")
            return False

    async def _send_telegram(self, message: str) -> bool:
        """Send Telegram message."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": self.telegram_chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                    },
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Telegram notification error: {e}")
            return False


# Singleton
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

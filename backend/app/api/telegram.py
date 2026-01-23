"""API endpoints for Telegram bot webhook."""

from fastapi import APIRouter, Request, HTTPException
import json

from app.services.telegram_bot import handle_telegram_callback, get_telegram_bot
from app.core.config import settings

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook updates.

    This endpoint receives updates from Telegram when users
    interact with inline buttons in approval messages.
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Handle callback queries (button clicks)
    if "callback_query" in data:
        callback = data["callback_query"]
        callback_data = callback.get("data", "")
        callback_id = callback.get("id")

        # Process the callback
        result = await handle_telegram_callback(callback_data)

        # Answer the callback to remove loading state
        bot = get_telegram_bot()
        await bot._send_callback_answer(callback_id, result.get("message", "Done"))

        return {"ok": True, "result": result}

    # Handle regular messages (could be used for commands)
    if "message" in data:
        message = data["message"]
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        # Handle commands
        if text.startswith("/"):
            return await handle_command(text, chat_id)

    return {"ok": True}


async def handle_command(text: str, chat_id: str) -> dict:
    """Handle bot commands."""
    bot = get_telegram_bot()

    if text == "/start":
        await bot._send_message(
            text="""
<b>🎙️ Maya AI News Anchor Bot</b>

I'll send you approval requests for:
• Weekly news briefings
• On-demand article videos

Commands:
/status - View pending approvals
/help - Show this help message

Dashboard: {settings.frontend_url}
""",
        )
        return {"ok": True, "handled": "start"}

    elif text == "/status":
        from app.services.database import get_db_service
        db = get_db_service()

        # Get pending items
        pending = await db.get_pending_approvals()
        ondemand_pending = await db.list_ondemand_jobs(status="awaiting_approval", limit=5)

        message = "<b>📋 Pending Approvals</b>\n\n"

        if pending:
            message += "<b>Weekly Briefings:</b>\n"
            for item in pending:
                message += f"• Week {item.week_number}, {item.year} ({item.status})\n"
        else:
            message += "No pending weekly briefings.\n"

        message += "\n"

        if ondemand_pending:
            message += "<b>On-Demand Jobs:</b>\n"
            for job in ondemand_pending:
                message += f"• {job.title[:30]}... ({job.status})\n"
        else:
            message += "No pending on-demand jobs.\n"

        await bot._send_message(text=message)
        return {"ok": True, "handled": "status"}

    elif text == "/help":
        await bot._send_message(
            text="""
<b>📚 Maya Bot Help</b>

<b>Approval Flow:</b>
1. You receive a script for review
2. Click Approve or Reject
3. If approved, video is generated
4. Review video and approve to publish
5. Content goes live on all platforms

<b>Commands:</b>
/start - Welcome message
/status - View pending approvals
/help - This help message

<b>Quick Actions:</b>
Use the inline buttons on approval messages to:
✅ Approve
❌ Reject
🔄 Regenerate

Dashboard: {settings.frontend_url}
""",
        )
        return {"ok": True, "handled": "help"}

    return {"ok": True, "handled": None}


@router.get("/setup")
async def setup_webhook():
    """
    Set up the Telegram webhook.

    Call this endpoint once to register the webhook URL with Telegram.
    """
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    webhook_url = f"{settings.backend_url}/api/v1/telegram/webhook"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook",
            json={"url": webhook_url},
            timeout=30.0,
        )
        result = response.json()

    if result.get("ok"):
        return {
            "status": "success",
            "webhook_url": webhook_url,
            "message": "Telegram webhook configured successfully",
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set webhook: {result.get('description')}"
        )


@router.delete("/webhook")
async def remove_webhook():
    """Remove the Telegram webhook."""
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/deleteWebhook",
            timeout=30.0,
        )
        result = response.json()

    return {"status": "removed" if result.get("ok") else "error", "result": result}


@router.get("/info")
async def get_webhook_info():
    """Get current webhook info."""
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo",
            timeout=30.0,
        )
        result = response.json()

    return result


# Add missing import
import httpx

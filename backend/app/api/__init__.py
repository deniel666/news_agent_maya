from fastapi import APIRouter

from .briefings import router as briefings_router
from .approvals import router as approvals_router
from .dashboard import router as dashboard_router
from .settings import router as settings_router
from .websocket import router as websocket_router
from .sources import router as sources_router
from .cron import router as cron_router
from .ondemand import router as ondemand_router
from .telegram import router as telegram_router
from .content import router as content_router

api_router = APIRouter()

api_router.include_router(briefings_router, prefix="/briefings", tags=["briefings"])
api_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(websocket_router, tags=["websocket"])
api_router.include_router(sources_router, prefix="/sources", tags=["sources"])
api_router.include_router(cron_router, prefix="/cron", tags=["cron"])
api_router.include_router(ondemand_router, prefix="/on-demand", tags=["on-demand"])
api_router.include_router(telegram_router, prefix="/telegram", tags=["telegram"])
api_router.include_router(content_router, prefix="/content", tags=["content"])

__all__ = ["api_router"]

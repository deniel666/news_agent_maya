from fastapi import APIRouter

from .briefings import router as briefings_router
from .approvals import router as approvals_router
from .dashboard import router as dashboard_router
from .settings import router as settings_router

api_router = APIRouter()

api_router.include_router(briefings_router, prefix="/briefings", tags=["briefings"])
api_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])

__all__ = ["api_router"]

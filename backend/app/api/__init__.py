from fastapi import APIRouter
from .dashboard import router as dashboard_router
from .courses import router as courses_router
from .activities import router as activities_router
from .moodle import router as moodle_router
from .logs import router as logs_router
from .settings import router as settings_router
from .workspaces import router as workspaces_router

api_router = APIRouter(prefix="/api")
api_router.include_router(dashboard_router)
api_router.include_router(courses_router)
api_router.include_router(activities_router)
api_router.include_router(moodle_router)
api_router.include_router(logs_router)
api_router.include_router(settings_router)
api_router.include_router(workspaces_router)

__all__ = ["api_router"]

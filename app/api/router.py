from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.docker import router as docker_router
from app.api.routes.health import router as health_router
from app.api.routes.mcp_sse import router as mcp_router
from app.api.routes.oauth import router as oauth_router
from app.api.routes.system import router as system_router
from app.api.routes.well_known import router as well_known_router

api_router = APIRouter()

api_router.include_router(admin_router)
api_router.include_router(docker_router)
api_router.include_router(system_router)
api_router.include_router(well_known_router)
api_router.include_router(oauth_router)
api_router.include_router(mcp_router)
api_router.include_router(health_router)


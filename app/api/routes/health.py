import os
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings

router = APIRouter(tags=["Health & Diagnostics"])

def get_spa_index_path() -> str:
    candidates = [
        os.path.join(os.environ.get("STATIC_DIR", "/app/static"), "index.html"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "index.html"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist", "index.html"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return candidates[0]


@router.get("/health", summary="Health Check")
async def health_check():
    """Returns the operational status of the server and available endpoint routes."""
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mcp_server": settings.MCP_SERVER_NAME,
        "endpoints": {
            "sse": "/mcp",
            "message": settings.MCP_MESSAGE_ENDPOINT,
            "oauth_authorize": "/authorize",
            "oauth_token": "/token",
        },
    }


@router.api_route("/app.css", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_app_css():
    """Serves the compiled Tailwind CSS v4 stylesheet."""
    candidates = [
        os.path.join(os.environ.get("STATIC_DIR", "/app/static"), "app.css"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "app.css"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist", "app.css"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return FileResponse(p, media_type="text/css")
    return JSONResponse(status_code=404, content={"error": "app.css not found"})


@router.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_spa(request: Request, full_path: str = ""):
    """Serves the Vue 3 SPA index.html for frontend client-side routes, falling back to 404 or health JSON."""
    if full_path.startswith("api/") or full_path.startswith("mcp") or full_path in ("authorize", "token", "consent"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    spa_path = get_spa_index_path()
    if os.path.isfile(spa_path):
        return FileResponse(spa_path, media_type="text/html")
    return JSONResponse(await health_check())



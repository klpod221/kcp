import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.logging import logger
from app.db.session import init_db
from app.mcp import mcp_server, register_all_tools, session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initializes DB schema, seeds data, registers tools."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")

    await init_db()
    register_all_tools(mcp_server)

    if getattr(session_manager, "_has_started", False):
        yield
    else:
        async with session_manager.run():
            yield

    logger.info(f"Shutting down {settings.APP_NAME}...")


def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = os.environ.get("STATIC_DIR", "/app/static")
    if not os.path.isdir(static_dir):
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        if not os.path.isdir(static_dir):
            static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

    assets_dir = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    if os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    app.include_router(api_router)

    return app

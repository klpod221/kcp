from app.config import settings
from app.core.logging import logger
import asyncio
import functools
import json

try:
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:
    from mcp.server.fastmcp import FastMCP as Server

from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

mcp_server = Server(
    name=settings.MCP_SERVER_NAME,
    title=settings.MCP_SERVER_NAME,
    description=settings.MCP_SERVER_DESCRIPTION,
    instructions=settings.MCP_SERVER_INSTRUCTIONS,
    version=settings.APP_VERSION,
    website_url=settings.BASE_URL,
)

# Intercept and wrap tool functions so that uncaught exceptions return informative JSON
# instead of causing an unhandled stream crash and CONNECTION_CLOSED on AI clients.
_orig_add_tool = mcp_server.add_tool


def _safe_add_tool(fn, name=None, *args, **kwargs):
    tool_name = name or getattr(fn, "__name__", "unnamed_tool")

    if asyncio.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def _safe_async_fn(*fn_args, **fn_kwargs):
            try:
                return await fn(*fn_args, **fn_kwargs)
            except Exception as exc:
                logger.error(f"Error executing MCP tool '{tool_name}': {exc}", exc_info=True)
                return json.dumps({
                    "status": "error",
                    "tool": tool_name,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }, ensure_ascii=False)
        target_fn = _safe_async_fn
    else:
        @functools.wraps(fn)
        def _safe_sync_fn(*fn_args, **fn_kwargs):
            try:
                return fn(*fn_args, **fn_kwargs)
            except Exception as exc:
                logger.error(f"Error executing MCP tool '{tool_name}': {exc}", exc_info=True)
                return json.dumps({
                    "status": "error",
                    "tool": tool_name,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }, ensure_ascii=False)
        target_fn = _safe_sync_fn

    return _orig_add_tool(target_fn, name=name, *args, **kwargs)


mcp_server.add_tool = _safe_add_tool

lowlevel_server = getattr(
    mcp_server,
    "_lowlevel_server",
    getattr(mcp_server, "_mcp_server", None),
)
if lowlevel_server is None:
    raise RuntimeError("Could not find underlying MCP server engine.")

sse_transport = SseServerTransport(settings.MCP_MESSAGE_ENDPOINT)
session_manager = StreamableHTTPSessionManager(app=lowlevel_server)

logger.info(
    f"Initialized MCP Server '{settings.MCP_SERVER_NAME}' with SSE & Streamable HTTP transports"
)

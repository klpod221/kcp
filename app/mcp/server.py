from app.config import settings
from app.core.logging import logger

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

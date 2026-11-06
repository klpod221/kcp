from typing import Any

from app.core.logging import logger
from app.mcp.tools.bazarr import register_bazarr_tools
from app.mcp.tools.docker import register_docker_tools
from app.mcp.tools.hello import register_hello_tools
from app.mcp.tools.jellyfin import register_jellyfin_tools
from app.mcp.tools.jellyseerr import register_jellyseerr_tools
from app.mcp.tools.lidarr import register_lidarr_tools
from app.mcp.tools.overview import register_overview_tools
from app.mcp.tools.prowlarr import register_prowlarr_tools
from app.mcp.tools.qbittorrent import register_qbittorrent_tools
from app.mcp.tools.radarr import register_radarr_tools
from app.mcp.tools.rclone import register_rclone_tools
from app.mcp.tools.sonarr import register_sonarr_tools
from app.mcp.tools.trilium import register_trilium_tools


def register_all_tools(server: Any) -> None:
    """Central registry to register all tool packages to the MCP Server instance."""
    logger.info("Registering MCP tools into server instance...")

    register_hello_tools(server)
    register_overview_tools(server)
    register_docker_tools(server)
    register_radarr_tools(server)
    register_sonarr_tools(server)
    register_lidarr_tools(server)
    register_prowlarr_tools(server)
    register_bazarr_tools(server)
    register_jellyfin_tools(server)
    register_jellyseerr_tools(server)
    register_qbittorrent_tools(server)
    register_trilium_tools(server)
    register_rclone_tools(server)

    logger.info("All MCP tools registered successfully.")

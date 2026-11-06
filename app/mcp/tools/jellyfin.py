from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.jellyfin import jellyfin_service


def register_jellyfin_tools(server) -> None:
    """Registers Jellyfin media server and streaming playback tools."""

    @server.tool()
    async def jellyfin_search_media(query: str, limit: int = 20) -> str:
        """Searches across all Jellyfin libraries for movies, TV series, episodes, or music.

        Args:
            query: The search term.
            limit: Maximum items to return (default 20).
        """
        logger.info(f"Executing jellyfin_search_media: query='{query}'")
        res = await jellyfin_service.search_media(query=query, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def jellyfin_get_latest(limit: int = 15) -> str:
        """Retrieves recently added movies and episodes in Jellyfin.

        Args:
            limit: Maximum items to return (default 15).
        """
        logger.info("Executing jellyfin_get_latest")
        res = await jellyfin_service.get_latest(limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def jellyfin_get_item_details(item_id: str) -> str:
        """Gets technical media information for a Jellyfin item.

        Includes resolution, video/audio codecs, available audio/subtitle tracks, and file path.

        Args:
            item_id: The Jellyfin item ID (from jellyfin_search_media or jellyfin_get_latest).
        """
        logger.info(f"Executing jellyfin_get_item_details: item_id='{item_id}'")
        res = await jellyfin_service.get_item_details(item_id=item_id)
        return to_pretty_json(res)

    @server.tool()
    async def jellyfin_get_sessions() -> str:
        """Lists active Jellyfin playback sessions (shows who is watching what, on which client, play state)."""
        logger.info("Executing jellyfin_get_sessions")
        res = await jellyfin_service.get_sessions()
        return to_pretty_json(res)

    @server.tool()
    async def jellyfin_control_session(session_id: str, command: str, message: Optional[str] = None) -> str:
        """Controls an active playback session (pause, play, stop, or display an onscreen message).

        Args:
            session_id: The session ID (from jellyfin_get_sessions).
            command: 'play', 'pause', 'stop', or 'message'.
            message: Text to display if command is 'message'.
        """
        logger.info(f"Executing jellyfin_control_session: session_id='{session_id}', command='{command}'")
        res = await jellyfin_service.control_session(session_id=session_id, command=command, text=message)
        return to_pretty_json(res)

    @server.tool()
    async def jellyfin_scan_library() -> str:
        """Triggers a library refresh/scan to detect newly added or updated media files."""
        logger.info("Executing jellyfin_scan_library")
        res = await jellyfin_service.scan_library()
        return to_pretty_json(res)

    @server.tool()
    async def jellyfin_get_system_info() -> str:
        """Retrieves Jellyfin server version, configured libraries, and user list."""
        logger.info("Executing jellyfin_get_system_info")
        res = await jellyfin_service.get_system_info()
        return to_pretty_json(res)

    logger.debug("Registered Jellyfin tools.")


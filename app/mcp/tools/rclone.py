from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.rclone import rclone_service


def register_rclone_tools(server) -> None:
    """Registers Rclone mount and VFS cache management tools."""

    @server.tool()
    async def rclone_get_status() -> str:
        """Retrieves comprehensive Rclone Google Drive mount status.

        Includes VFS cache disk usage, files cached, queued/in-progress uploads,
        Google Drive storage capacity and free space, current transfer speeds,
        and transmission error counters.
        """
        logger.info("Executing rclone_get_status")
        res = await rclone_service.get_status()
        return to_pretty_json(res)

    @server.tool()
    async def rclone_refresh_dir_cache(
        directory_path: Optional[str] = None,
        recursive: bool = True,
    ) -> str:
        """Forces an instant refresh of Rclone's directory cache so newly added cloud files appear immediately.

        Use this whenever files are uploaded directly to Google Drive or after media is moved,
        so Radarr, Sonarr, and Jellyfin can immediately detect the files without remounting.

        Args:
            directory_path: Optional relative folder path under Google Drive (e.g. 'Media', 'Media/Movies').
                           If omitted, refreshes the entire mount root.
            recursive: Whether to refresh all nested subfolders recursively (default True).
        """
        logger.info(f"Executing rclone_refresh_dir_cache: dir='{directory_path}', recursive={recursive}")
        res = await rclone_service.refresh_directory_cache(dir_path=directory_path, recursive=recursive)
        return to_pretty_json(res)

    @server.tool()
    async def rclone_forget_cache(directory_path: Optional[str] = None) -> str:
        """Clears directory cache entries from memory, forcing fresh reads from Google Drive on next access.

        Args:
            directory_path: Optional relative folder path to forget. If omitted, forgets all cached directories.
        """
        logger.info(f"Executing rclone_forget_cache: dir='{directory_path}'")
        res = await rclone_service.forget_cache(dir_path=directory_path)
        return to_pretty_json(res)

    logger.debug("Registered Rclone tools.")


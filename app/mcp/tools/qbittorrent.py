from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.qbittorrent import qbittorrent_service


def register_qbittorrent_tools(server) -> None:
    """Registers qBittorrent download client management tools."""

    @server.tool()
    async def qbit_get_torrents(
        filter_state: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """Lists torrents in qBittorrent with download/upload speeds, progress %, and ETA.

        Args:
            filter_state: 'all', 'downloading', 'seeding', 'completed', 'paused', 'active', 'inactive', 'stalled', 'errored'.
            category: Optional category filter (e.g. 'radarr', 'tv-sonarr').
            tag: Optional tag filter.
            limit: Maximum torrents to return (default 50).
        """
        logger.info(f"Executing qbit_get_torrents: filter_state='{filter_state}', category='{category}'")
        res = await qbittorrent_service.get_torrents(
            filter_state=filter_state,
            category=category,
            tag=tag,
            limit=limit,
        )
        return to_pretty_json(res)

    @server.tool()
    async def qbit_get_torrent_details(torrent_hash: str) -> str:
        """Gets detailed properties of a torrent: file list, trackers, peers, and ratio.

        Args:
            torrent_hash: The 40-character torrent hash.
        """
        logger.info(f"Executing qbit_get_torrent_details: hash='{torrent_hash}'")
        res = await qbittorrent_service.get_torrent_details(torrent_hash)
        return to_pretty_json(res)

    @server.tool()
    async def qbit_add_torrent(
        urls: str,
        category: Optional[str] = None,
        save_path: Optional[str] = None,
        paused: bool = False,
    ) -> str:
        """Adds a torrent via magnet link or .torrent URL.

        Args:
            urls: Magnet link or .torrent URL (multiple separated by newlines).
            category: Optional category (e.g. 'radarr', 'manual').
            save_path: Optional custom download destination path.
            paused: Whether to add the torrent in a paused state (default False).
        """
        logger.info("Executing qbit_add_torrent")
        res = await qbittorrent_service.add_torrent(
            urls=urls,
            category=category,
            save_path=save_path,
            paused=paused,
        )
        return to_pretty_json(res)

    @server.tool()
    async def qbit_manage_torrent(
        hashes: list[str],
        action: str,
        delete_files: bool = False,
    ) -> str:
        """Controls torrent state: pause, resume, recheck, or delete.

        By default, delete_files is False to safely preserve downloaded files on disk.

        Args:
            hashes: List of torrent hashes to control.
            action: 'pause', 'resume', 'recheck', or 'delete'.
            delete_files: If action is 'delete', set True to delete downloaded data from disk. Defaults to False for safety.
        """
        logger.info(f"Executing qbit_manage_torrent: action='{action}', delete_files={delete_files}")
        res = await qbittorrent_service.manage_torrent(hashes=hashes, action=action, delete_files=delete_files)
        return to_pretty_json(res)

    @server.tool()
    async def qbit_set_speed_limits(
        toggle_alt_mode: Optional[bool] = None,
        dl_limit_kbs: Optional[int] = None,
        up_limit_kbs: Optional[int] = None,
    ) -> str:
        """Toggles alternative speed limits mode (turtle mode) or sets global speed limits.

        Args:
            toggle_alt_mode: Set True to toggle alternative speed limit mode.
            dl_limit_kbs: Global download rate limit in KB/s.
            up_limit_kbs: Global upload rate limit in KB/s.
        """
        logger.info("Executing qbit_set_speed_limits")
        res = await qbittorrent_service.set_speed_limits(
            toggle_alt_mode=toggle_alt_mode,
            dl_limit_kbs=dl_limit_kbs,
            up_limit_kbs=up_limit_kbs,
        )
        return to_pretty_json(res)

    @server.tool()
    async def qbit_get_transfer_info() -> str:
        """Retrieves global transfer speeds, total payload data transferred, free disk space, and categories."""
        logger.info("Executing qbit_get_transfer_info")
        res = await qbittorrent_service.get_transfer_info()
        return to_pretty_json(res)

    logger.debug("Registered qBittorrent tools.")


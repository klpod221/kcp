from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.lidarr import lidarr_service


def register_lidarr_tools(server) -> None:
    """Registers Lidarr music management tools."""

    @server.tool()
    async def lidarr_search(query: str) -> str:
        """Searches for music artists or albums on MusicBrainz via Lidarr.

        Args:
            query: Artist name or album title.
        """
        logger.info(f"Executing lidarr_search: query='{query}'")
        res = await lidarr_service.search(query)
        return to_pretty_json(res)

    @server.tool()
    async def lidarr_get_artists(
        search: Optional[str] = None,
        monitored: Optional[bool] = None,
        limit: int = 50,
    ) -> str:
        """Lists music artists in your Lidarr library.

        Args:
            search: Optional filter by artist name.
            monitored: Optional filter by monitored status.
            limit: Maximum artists to return (default 50).
        """
        logger.info("Executing lidarr_get_artists")
        res = await lidarr_service.get_artists(search=search, monitored=monitored, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def lidarr_get_albums(artist_id: Optional[int] = None, limit: int = 50) -> str:
        """Lists albums for an artist or across the entire music library.

        Args:
            artist_id: Optional Lidarr artist ID to filter by.
            limit: Maximum albums to return (default 50).
        """
        logger.info(f"Executing lidarr_get_albums: artist_id={artist_id}")
        res = await lidarr_service.get_albums(artist_id=artist_id, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def lidarr_add_artist(
        foreign_artist_id: str,
        quality_profile_id: Optional[int] = None,
        root_folder_path: Optional[str] = None,
        monitored: bool = True,
        search_for_missing_albums: bool = True,
    ) -> str:
        """Adds a new artist to Lidarr and optionally triggers an album search.

        Args:
            foreign_artist_id: The MusicBrainz artist ID (from lidarr_search).
            quality_profile_id: Optional quality profile ID (default 1).
            root_folder_path: Optional storage path (default /data/media/Music).
            monitored: Whether to monitor the artist (default True).
            search_for_missing_albums: Whether to immediately search for albums (default True).
        """
        logger.info(f"Executing lidarr_add_artist: foreign_artist_id={foreign_artist_id}")
        res = await lidarr_service.add_artist(
            foreign_artist_id=foreign_artist_id,
            quality_profile_id=quality_profile_id,
            root_folder_path=root_folder_path,
            monitored=monitored,
            search_for_missing_albums=search_for_missing_albums,
        )
        return to_pretty_json(res)

    @server.tool()
    async def lidarr_delete_artist(artist_id: int, delete_files: bool = False) -> str:
        """Deletes an artist from Lidarr.

        By default, delete_files is False to safely preserve music files on disk.

        Args:
            artist_id: The Lidarr artist ID.
            delete_files: If True, deletes music audio files from storage. Defaults to False.
        """
        logger.info(f"Executing lidarr_delete_artist: artist_id={artist_id}, delete_files={delete_files}")
        res = await lidarr_service.delete_artist(artist_id=artist_id, delete_files=delete_files)
        return to_pretty_json(res)

    @server.tool()
    async def lidarr_get_queue(page: int = 1, page_size: int = 30) -> str:
        """Retrieves Lidarr's music download and import queue.

        Args:
            page: Page number (default 1).
            page_size: Number of records per page (default 30).
        """
        logger.info("Executing lidarr_get_queue")
        res = await lidarr_service.get_queue(page=page, page_size=page_size)
        return to_pretty_json(res)

    @server.tool()
    async def lidarr_trigger_search(
        artist_id: Optional[int] = None,
        album_ids: Optional[list[int]] = None,
    ) -> str:
        """Triggers an automatic search for an artist or album IDs in Lidarr.

        Args:
            artist_id: The Lidarr artist ID.
            album_ids: Optional list of specific album IDs to search for.
        """
        logger.info("Executing lidarr_trigger_search")
        res = await lidarr_service.trigger_search(artist_id=artist_id, album_ids=album_ids)
        return to_pretty_json(res)

    logger.debug("Registered Lidarr tools.")


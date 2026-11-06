from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.sonarr import sonarr_service


def register_sonarr_tools(server) -> None:
    """Registers Sonarr TV series and anime management tools."""

    @server.tool()
    async def sonarr_search_series(query: str) -> str:
        """Searches for TV series or anime on TVDB via Sonarr.

        Returns show metadata and whether each show already exists in your Sonarr library.

        Args:
            query: Series title, keyword, or TVDB ID.
        """
        logger.info(f"Executing sonarr_search_series: query='{query}'")
        res = await sonarr_service.lookup_series(query)
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_get_series(
        search: Optional[str] = None,
        monitored: Optional[bool] = None,
        series_type: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """Lists TV series in your Sonarr library with optional filters.

        Args:
            search: Optional filter by series title or TVDB ID.
            monitored: Optional filter by monitored status (True/False).
            series_type: Optional filter by type ('standard', 'anime', 'daily').
            limit: Maximum shows to return (default 50).
        """
        logger.info("Executing sonarr_get_series")
        res = await sonarr_service.get_series(search=search, monitored=monitored, series_type=series_type, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_get_series_details(
        series_id: int,
        season_number: Optional[int] = None,
        include_episodes: bool = True,
    ) -> str:
        """Gets detailed info on a series, its seasons, and episodes (air dates, file status).

        Args:
            series_id: The Sonarr series ID.
            season_number: Optional season number filter.
            include_episodes: Whether to include the list of individual episodes (default True).
        """
        logger.info(f"Executing sonarr_get_series_details: series_id={series_id}")
        res = await sonarr_service.get_series_details(
            series_id=series_id,
            season_number=season_number,
            include_episodes=include_episodes,
        )
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_add_series(
        tvdb_id: int,
        series_type: str = "standard",
        quality_profile_id: Optional[int] = None,
        root_folder_path: Optional[str] = None,
        monitor_mode: str = "all",
        season_folder: bool = True,
        search_for_missing_episodes: bool = True,
    ) -> str:
        """Adds a new TV series or anime to Sonarr and optionally searches for episodes.

        Args:
            tvdb_id: The TVDB ID (find via sonarr_search_series).
            series_type: 'standard', 'anime', or 'daily' (default 'standard').
            quality_profile_id: Quality profile ID (defaults to 'My Profile' ID 7).
            root_folder_path: Root folder (defaults to /data/media/TV_Shows).
            monitor_mode: 'all', 'future', 'missing', 'existing', 'firstSeason', 'latestSeason', or 'none'.
            season_folder: Whether to organize episodes into Season folders (default True).
            search_for_missing_episodes: Whether to immediately search for missing episodes (default True).
        """
        logger.info(f"Executing sonarr_add_series: tvdb_id={tvdb_id}")
        res = await sonarr_service.add_series(
            tvdb_id=tvdb_id,
            series_type=series_type,
            quality_profile_id=quality_profile_id,
            root_folder_path=root_folder_path,
            monitor_mode=monitor_mode,
            season_folder=season_folder,
            search_for_missing_episodes=search_for_missing_episodes,
        )
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_update_monitoring(
        series_id: int,
        monitored: Optional[bool] = None,
        season_number: Optional[int] = None,
        episode_ids: Optional[list[int]] = None,
    ) -> str:
        """Updates monitoring status for a series, a specific season, or specific episode IDs.

        Args:
            series_id: The Sonarr series ID.
            monitored: True to monitor, False to unmonitor.
            season_number: Optional season number to update.
            episode_ids: Optional list of episode IDs to update.
        """
        logger.info(f"Executing sonarr_update_monitoring: series_id={series_id}")
        res = await sonarr_service.update_monitoring(
            series_id=series_id,
            monitored=monitored,
            season_number=season_number,
            episode_ids=episode_ids,
        )
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_delete_series(
        series_id: int,
        delete_files: bool = False,
        add_import_list_exclusion: bool = False,
    ) -> str:
        """Deletes a series from Sonarr.

        By default, delete_files is False to safely preserve episode files on disk.

        Args:
            series_id: The Sonarr series ID.
            delete_files: If True, deletes downloaded video files from storage. Defaults to False for safety.
            add_import_list_exclusion: If True, prevents Sonarr from automatically re-importing the show.
        """
        logger.info(f"Executing sonarr_delete_series: series_id={series_id}, delete_files={delete_files}")
        res = await sonarr_service.delete_series(
            series_id=series_id,
            delete_files=delete_files,
            add_import_list_exclusion=add_import_list_exclusion,
        )
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_get_queue(page: int = 1, page_size: int = 30) -> str:
        """Retrieves Sonarr's download queue with episode titles, speeds, and time left.

        Args:
            page: Page number (default 1).
            page_size: Number of records per page (default 30).
        """
        logger.info("Executing sonarr_get_queue")
        res = await sonarr_service.get_queue(page=page, page_size=page_size)
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_get_calendar(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Gets upcoming TV show air dates from the Sonarr calendar.

        Args:
            start_date: ISO date string (e.g. 2026-11-01).
            end_date: ISO date string (e.g. 2026-11-08).
        """
        logger.info("Executing sonarr_get_calendar")
        res = await sonarr_service.get_calendar(start_date=start_date, end_date=end_date)
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_get_missing(page: int = 1, page_size: int = 30) -> str:
        """Gets the list of wanted/missing episodes that have aired but have not been downloaded yet.

        Args:
            page: Page number (default 1).
            page_size: Number of records per page (default 30).
        """
        logger.info("Executing sonarr_get_missing")
        res = await sonarr_service.get_missing(page=page, page_size=page_size)
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_trigger_search(
        series_id: Optional[int] = None,
        season_number: Optional[int] = None,
        episode_ids: Optional[list[int]] = None,
    ) -> str:
        """Triggers an automatic indexer search for an entire series, a specific season, or episode IDs.

        Args:
            series_id: The Sonarr series ID.
            season_number: Optional season number (use with series_id).
            episode_ids: Optional list of episode IDs to search for.
        """
        logger.info("Executing sonarr_trigger_search")
        res = await sonarr_service.trigger_search(
            series_id=series_id,
            season_number=season_number,
            episode_ids=episode_ids,
        )
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_search_releases(
        episode_id: Optional[int] = None,
        series_id: Optional[int] = None,
        season_number: Optional[int] = None,
        limit: int = 25,
    ) -> str:
        """Performs an interactive release search across all indexers for an episode or season.

        Returns available torrent releases with quality, size, and seeders.

        Args:
            episode_id: The episode ID to search for.
            series_id: Optional series ID (for season search).
            season_number: Optional season number (for season search).
            limit: Maximum releases to display (default 25).
        """
        logger.info("Executing sonarr_search_releases")
        res = await sonarr_service.search_releases(
            episode_id=episode_id,
            series_id=series_id,
            season_number=season_number,
            limit=limit,
        )
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_grab_release(guid: str, indexer_id: int) -> str:
        """Grabs a specific release from search results and sends it to the download client.

        Args:
            guid: The release guid from sonarr_search_releases.
            indexer_id: The indexer ID from sonarr_search_releases.
        """
        logger.info(f"Executing sonarr_grab_release: guid={guid}")
        res = await sonarr_service.grab_release(guid=guid, indexer_id=indexer_id)
        return to_pretty_json(res)

    @server.tool()
    async def sonarr_get_system_info() -> str:
        """Retrieves Sonarr system status, quality profiles, and root folders."""
        logger.info("Executing sonarr_get_system_info")
        res = await sonarr_service.get_system_info()
        return to_pretty_json(res)

    logger.debug("Registered Sonarr tools.")


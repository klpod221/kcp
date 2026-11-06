from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.radarr import radarr_service


def register_radarr_tools(server) -> None:
    """Registers Radarr movie management tools."""

    @server.tool()
    async def radarr_search_movie(query: str) -> str:
        """Searches for movies on TMDB via Radarr by title or keyword.

        Returns movie metadata and whether each movie is already in your Radarr library.

        Args:
            query: Movie title, keyword, or TMDB ID to search for.
        """
        logger.info(f"Executing radarr_search_movie: query='{query}'")
        results = await radarr_service.lookup_movies(query)
        return to_pretty_json(results)

    @server.tool()
    async def radarr_get_movies(
        search: Optional[str] = None,
        monitored: Optional[bool] = None,
        has_file: Optional[bool] = None,
        limit: int = 50,
    ) -> str:
        """Lists movies in your Radarr library with optional filters.

        Args:
            search: Optional filter by movie title or TMDB ID.
            monitored: Optional filter by monitored status (True/False).
            has_file: Optional filter by whether the video file is downloaded on disk (True/False).
            limit: Maximum number of movies to return (default 50).
        """
        logger.info("Executing radarr_get_movies")
        res = await radarr_service.get_movies(search=search, monitored=monitored, has_file=has_file, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def radarr_get_movie_details(movie_id: int) -> str:
        """Gets complete details of a movie in your Radarr library.

        Includes file resolution, audio/video codecs, subtitles, file size, release dates, and path.

        Args:
            movie_id: The internal Radarr movie ID.
        """
        logger.info(f"Executing radarr_get_movie_details: movie_id={movie_id}")
        res = await radarr_service.get_movie_details(movie_id)
        return to_pretty_json(res)

    @server.tool()
    async def radarr_add_movie(
        tmdb_id: int,
        quality_profile_id: Optional[int] = None,
        root_folder_path: Optional[str] = None,
        monitored: bool = True,
        search_for_movie: bool = True,
    ) -> str:
        """Adds a movie to Radarr by TMDB ID and optionally starts searching for it immediately.

        Args:
            tmdb_id: The TMDB ID of the movie (find via radarr_search_movie).
            quality_profile_id: Optional quality profile ID (defaults to 'My Profile' ID 7).
            root_folder_path: Optional root storage folder (defaults to /data/media/Movies).
            monitored: Whether Radarr should monitor the movie for new/better releases (default True).
            search_for_movie: Whether to trigger an automatic indexer search right after adding (default True).
        """
        logger.info(f"Executing radarr_add_movie: tmdb_id={tmdb_id}")
        res = await radarr_service.add_movie(
            tmdb_id=tmdb_id,
            quality_profile_id=quality_profile_id,
            root_folder_path=root_folder_path,
            monitored=monitored,
            search_for_movie=search_for_movie,
        )
        return to_pretty_json(res)

    @server.tool()
    async def radarr_update_movie(
        movie_id: int,
        monitored: Optional[bool] = None,
        quality_profile_id: Optional[int] = None,
    ) -> str:
        """Updates movie settings such as monitored status or quality profile.

        Args:
            movie_id: The Radarr movie ID.
            monitored: Set monitored state (True to monitor, False to stop monitoring).
            quality_profile_id: New quality profile ID.
        """
        logger.info(f"Executing radarr_update_movie: movie_id={movie_id}")
        res = await radarr_service.update_movie(
            movie_id=movie_id,
            monitored=monitored,
            quality_profile_id=quality_profile_id,
        )
        return to_pretty_json(res)

    @server.tool()
    async def radarr_delete_movie(
        movie_id: int,
        delete_files: bool = False,
        add_import_exclusion: bool = False,
    ) -> str:
        """Deletes a movie from Radarr.

        By default, delete_files is False to safely preserve movie files on disk.

        Args:
            movie_id: The Radarr movie ID.
            delete_files: If True, deletes downloaded video files from storage. Defaults to False for safety.
            add_import_exclusion: If True, prevents Radarr from re-importing the movie automatically.
        """
        logger.info(f"Executing radarr_delete_movie: movie_id={movie_id}, delete_files={delete_files}")
        res = await radarr_service.delete_movie(
            movie_id=movie_id,
            delete_files=delete_files,
            add_import_exclusion=add_import_exclusion,
        )
        return to_pretty_json(res)

    @server.tool()
    async def radarr_get_queue(page: int = 1, page_size: int = 30) -> str:
        """Retrieves Radarr's download and import queue with progress percentage, speeds, and time left.

        Args:
            page: Page number (default 1).
            page_size: Number of records per page (default 30).
        """
        logger.info("Executing radarr_get_queue")
        res = await radarr_service.get_queue(page=page, page_size=page_size)
        return to_pretty_json(res)

    @server.tool()
    async def radarr_get_calendar(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Gets upcoming movie cinema, digital, and physical release dates.

        Args:
            start_date: ISO date string (e.g. 2026-11-01).
            end_date: ISO date string (e.g. 2026-12-01).
        """
        logger.info("Executing radarr_get_calendar")
        res = await radarr_service.get_calendar(start_date=start_date, end_date=end_date)
        return to_pretty_json(res)

    @server.tool()
    async def radarr_search_releases(movie_id: int, limit: int = 25) -> str:
        """Performs an interactive release search across all indexers for a specific movie.

        Returns available torrent releases with quality, size, seeders, and rejections.

        Args:
            movie_id: The Radarr movie ID.
            limit: Maximum releases to display (default 25).
        """
        logger.info(f"Executing radarr_search_releases: movie_id={movie_id}")
        res = await radarr_service.search_releases(movie_id=movie_id, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def radarr_grab_release(
        guid: Optional[str] = None,
        indexer_id: Optional[int] = None,
        movie_id: Optional[int] = None,
    ) -> str:
        """Grabs a specific torrent release by guid/indexer_id, or triggers an automatic search for movie_id.

        Args:
            guid: The release guid from radarr_search_releases.
            indexer_id: The indexer ID from radarr_search_releases.
            movie_id: Alternatively, provide movie_id to trigger an automatic best-release search and grab.
        """
        logger.info("Executing radarr_grab_release")
        res = await radarr_service.grab_release(guid=guid, indexer_id=indexer_id, movie_id=movie_id)
        return to_pretty_json(res)

    @server.tool()
    async def radarr_get_system_info() -> str:
        """Retrieves Radarr system information, quality profiles, root folders, and disk space."""
        logger.info("Executing radarr_get_system_info")
        res = await radarr_service.get_system_info()
        return to_pretty_json(res)

    logger.debug("Registered Radarr tools.")


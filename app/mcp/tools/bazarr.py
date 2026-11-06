from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.bazarr import bazarr_service


def register_bazarr_tools(server) -> None:
    """Registers Bazarr subtitle management tools."""

    @server.tool()
    async def bazarr_get_status() -> str:
        """Retrieves Bazarr system status and configured subtitle providers."""
        logger.info("Executing bazarr_get_status")
        res = await bazarr_service.get_status()
        return to_pretty_json(res)

    @server.tool()
    async def bazarr_get_wanted_subtitles(media_type: str = "movies", page: int = 1, limit: int = 30) -> str:
        """Lists movies or TV episodes that are missing required subtitles.

        Args:
            media_type: 'movies' or 'episodes' (default 'movies').
            page: Page number (default 1).
            limit: Maximum items to return (default 30).
        """
        logger.info(f"Executing bazarr_get_wanted_subtitles: media_type={media_type}")
        if media_type.lower() == "episodes":
            res = await bazarr_service.get_wanted_episodes(page=page, limit=limit)
        else:
            res = await bazarr_service.get_wanted_movies(page=page, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def bazarr_search_subtitles(
        radarr_id: Optional[int] = None,
        sonarr_episode_id: Optional[int] = None,
        language: str = "vi",
    ) -> str:
        """Triggers an automated subtitle search and download for a movie or TV episode.

        Args:
            radarr_id: The Radarr movie ID.
            sonarr_episode_id: The Sonarr episode ID.
            language: Subtitle language code (e.g. 'vi' for Vietnamese, 'en' for English).
        """
        logger.info(f"Executing bazarr_search_subtitles: radarr_id={radarr_id}, sonarr_episode_id={sonarr_episode_id}")
        res = await bazarr_service.search_and_download_subtitles(
            radarr_id=radarr_id,
            sonarr_episode_id=sonarr_episode_id,
            language=language,
        )
        return to_pretty_json(res)

    @server.tool()
    async def bazarr_get_history(limit: int = 20) -> str:
        """Retrieves recent subtitle download and upgrade history.

        Args:
            limit: Maximum records to return (default 20).
        """
        logger.info("Executing bazarr_get_history")
        res = await bazarr_service.get_history(limit=limit)
        return to_pretty_json(res)

    logger.debug("Registered Bazarr tools.")


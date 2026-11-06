from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.jellyseerr import jellyseerr_service


def register_jellyseerr_tools(server) -> None:
    """Registers Jellyseerr media discovery and request management tools."""

    @server.tool()
    async def jellyseerr_search(query: str, page: int = 1) -> str:
        """Searches movies & TV shows on Jellyseerr with existing home-lab availability status.

        Args:
            query: The movie or TV show title to search for.
            page: Page number (default 1).
        """
        logger.info(f"Executing jellyseerr_search: query='{query}'")
        res = await jellyseerr_service.search(query=query, page=page)
        return to_pretty_json(res)

    @server.tool()
    async def jellyseerr_discover(category: str = "trending", page: int = 1) -> str:
        """Discovers trending or popular movies & TV shows for recommendation.

        Args:
            category: 'trending', 'movies_popular', 'tv_popular', or 'upcoming' (default 'trending').
            page: Page number (default 1).
        """
        logger.info(f"Executing jellyseerr_discover: category='{category}'")
        res = await jellyseerr_service.discover(category=category, page=page)
        return to_pretty_json(res)

    @server.tool()
    async def jellyseerr_get_requests(filter_status: str = "all", take: int = 20, skip: int = 0) -> str:
        """Lists user media requests.

        Args:
            filter_status: 'all', 'pending', 'approved', 'available', or 'processing'.
            take: Number of records to return (default 20).
            skip: Number of records to skip for pagination.
        """
        logger.info(f"Executing jellyseerr_get_requests: filter_status='{filter_status}'")
        res = await jellyseerr_service.get_requests(filter_status=filter_status, take=take, skip=skip)
        return to_pretty_json(res)

    @server.tool()
    async def jellyseerr_create_request(
        media_id: int,
        media_type: str = "movie",
        seasons: Optional[list[int]] = None,
    ) -> str:
        """Creates a new media request in Jellyseerr (routes automatically to Radarr or Sonarr).

        Args:
            media_id: The TMDB ID of the movie or show.
            media_type: 'movie' or 'tv'.
            seasons: Optional list of season numbers to request if media_type is 'tv' (defaults to all).
        """
        logger.info(f"Executing jellyseerr_create_request: media_id={media_id}, media_type='{media_type}'")
        res = await jellyseerr_service.create_request(media_id=media_id, media_type=media_type, seasons=seasons)
        return to_pretty_json(res)

    @server.tool()
    async def jellyseerr_manage_request(request_id: int, action: str) -> str:
        """Approves, declines, or deletes a media request.

        Args:
            request_id: The Jellyseerr request ID.
            action: 'approve', 'decline', or 'delete'.
        """
        logger.info(f"Executing jellyseerr_manage_request: request_id={request_id}, action='{action}'")
        res = await jellyseerr_service.manage_request(request_id=request_id, action=action)
        return to_pretty_json(res)

    @server.tool()
    async def jellyseerr_get_issues(take: int = 20) -> str:
        """Retrieves user reported media issues (e.g. video distortion, audio desync, missing subtitles).

        Args:
            take: Maximum issues to return (default 20).
        """
        logger.info("Executing jellyseerr_get_issues")
        res = await jellyseerr_service.get_issues(take=take)
        return to_pretty_json(res)

    logger.debug("Registered Jellyseerr tools.")


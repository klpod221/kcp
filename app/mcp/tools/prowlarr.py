from typing import Optional

from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.prowlarr import prowlarr_service


def register_prowlarr_tools(server) -> None:
    """Registers Prowlarr torrent indexer and direct search tools."""

    @server.tool()
    async def prowlarr_get_indexers() -> str:
        """Lists all configured indexers, privacy types, protocols, and enabled status."""
        logger.info("Executing prowlarr_get_indexers")
        res = await prowlarr_service.get_indexers()
        return to_pretty_json(res)

    @server.tool()
    async def prowlarr_test_indexers(indexer_id: Optional[int] = None) -> str:
        """Tests health and connectivity for all indexers or a specific indexer ID.

        Args:
            indexer_id: Optional specific indexer ID to test. If omitted, tests all indexers.
        """
        logger.info(f"Executing prowlarr_test_indexers: indexer_id={indexer_id}")
        res = await prowlarr_service.test_indexers(indexer_id=indexer_id)
        return to_pretty_json(res)

    @server.tool()
    async def prowlarr_search(
        query: str,
        indexer_ids: Optional[list[int]] = None,
        limit: int = 25,
    ) -> str:
        """Searches for torrent releases directly across all indexers via Prowlarr.

        Args:
            query: The search term (e.g. movie, anime, music, or software name).
            indexer_ids: Optional list of indexer IDs to limit the search to.
            limit: Maximum results to return (default 25).
        """
        logger.info(f"Executing prowlarr_search: query='{query}'")
        res = await prowlarr_service.search(query=query, indexer_ids=indexer_ids, limit=limit)
        return to_pretty_json(res)

    @server.tool()
    async def prowlarr_grab_release(guid: str, indexer_id: int) -> str:
        """Sends a release found via prowlarr_search directly to the download client.

        Args:
            guid: The release guid.
            indexer_id: The indexer ID.
        """
        logger.info(f"Executing prowlarr_grab_release: guid={guid}")
        res = await prowlarr_service.grab_release(guid=guid, indexer_id=indexer_id)
        return to_pretty_json(res)

    @server.tool()
    async def prowlarr_get_stats() -> str:
        """Retrieves query and grab performance statistics for all indexers."""
        logger.info("Executing prowlarr_get_stats")
        res = await prowlarr_service.get_stats()
        return to_pretty_json(res)

    logger.debug("Registered Prowlarr tools.")


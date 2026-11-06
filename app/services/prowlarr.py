from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes


class ProwlarrService(BaseServiceClient):
    """Asynchronous client for Prowlarr API v1."""

    def __init__(self) -> None:
        super().__init__(
            service_name="Prowlarr",
            base_url=settings.PROWLARR_URL,
            default_headers={"X-Api-Key": settings.PROWLARR_API_KEY},
        )

    async def get_indexers(self) -> list[dict[str, Any]]:
        indexers = await self.request("GET", "/api/v1/indexer")
        if not isinstance(indexers, list):
            return []
        return [
            {
                "id": idx.get("id"),
                "name": idx.get("name"),
                "enable": idx.get("enable"),
                "protocol": idx.get("protocol"),
                "privacy": idx.get("privacy"),
                "priority": idx.get("priority"),
                "supportsRss": idx.get("supportsRss"),
                "supportsSearch": idx.get("supportsSearch"),
                "capabilities": [c.get("name") for c in idx.get("capabilities", {}).get("categories", [])],
            }
            for idx in indexers
        ]

    async def test_indexers(self, indexer_id: Optional[int] = None) -> list[dict[str, Any]]:
        if indexer_id is not None:
            res = await self.request("POST", f"/api/v1/indexer/test/{indexer_id}")
            return [res] if isinstance(res, dict) else []
        res = await self.request("POST", "/api/v1/indexer/testall")
        return res if isinstance(res, list) else []

    async def search(
        self,
        query: str,
        indexer_ids: Optional[list[int]] = None,
        categories: Optional[list[int]] = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"query": query, "type": "search"}
        if indexer_ids:
            params["indexerIds"] = indexer_ids
        if categories:
            params["categories"] = categories

        results = await self.request("GET", "/api/v1/search", params=params)
        if not isinstance(results, list):
            return []
        formatted = []
        for r in results[:limit]:
            formatted.append(
                {
                    "guid": r.get("guid"),
                    "indexerId": r.get("indexerId"),
                    "indexer": r.get("indexer"),
                    "title": r.get("title"),
                    "size": format_bytes(r.get("size", 0)),
                    "seeders": r.get("seeders"),
                    "leechers": r.get("leechers"),
                    "publishDate": r.get("publishDate"),
                    "downloadUrl": r.get("downloadUrl"),
                    "infoUrl": r.get("infoUrl"),
                    "protocol": r.get("protocol"),
                }
            )
        return formatted

    async def grab_release(self, guid: str, indexer_id: int) -> dict[str, Any]:
        res = await self.request(
            "POST",
            "/api/v1/release",
            json_data={"guid": guid, "indexerId": indexer_id},
        )
        return {"action": "grabbed_release_via_prowlarr", "result": res}

    async def get_stats(self) -> dict[str, Any]:
        stats = await self.request("GET", "/api/v1/indexerstats")
        return stats if isinstance(stats, dict) else {}


prowlarr_service = ProwlarrService()


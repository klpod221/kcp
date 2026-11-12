import urllib.parse
from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient


class JellyseerrService(BaseServiceClient):
    """Asynchronous client for Jellyseerr API v1."""

    def __init__(self) -> None:
        super().__init__(
            service_name="Jellyseerr",
            base_url=settings.JELLYSEERR_URL,
            default_headers={"X-Api-Key": settings.JELLYSEERR_API_KEY},
        )

    def _format_media_status(self, media_info: Optional[dict[str, Any]]) -> str:
        if not media_info:
            return "not_requested"
        status_code = media_info.get("status")
        status_map = {
            1: "pending_approval",
            2: "processing_or_downloading",
            3: "partially_available",
            4: "available",
            5: "deleted",
        }
        return status_map.get(status_code, f"unknown_{status_code}")

    async def search(self, query: str, page: int = 1) -> dict[str, Any]:
        encoded_query = urllib.parse.quote(str(query).strip())
        endpoint = f"/api/v1/search?query={encoded_query}&page={page}"
        data = await self.request("GET", endpoint)
        results = data.get("results", []) if isinstance(data, dict) else []
        formatted = []
        for r in results:
            media_type = r.get("mediaType")
            media_info = r.get("mediaInfo")
            formatted.append(
                {
                    "id": r.get("id"),
                    "mediaType": media_type,
                    "title": r.get("title") or r.get("name"),
                    "releaseDate": r.get("releaseDate") or r.get("firstAirDate"),
                    "status_in_homelab": self._format_media_status(media_info),
                    "overview": (r.get("overview") or "")[:250],
                    "popularity": r.get("popularity"),
                }
            )
        return {
            "page": data.get("page", 1) if isinstance(data, dict) else 1,
            "totalPages": data.get("totalPages", 1) if isinstance(data, dict) else 1,
            "totalResults": data.get("totalResults", len(formatted)) if isinstance(data, dict) else len(formatted),
            "results": formatted,
        }

    async def discover(self, category: str = "trending", page: int = 1) -> list[dict[str, Any]]:
        path_map = {
            "trending": "/api/v1/discover/trending",
            "movies_popular": "/api/v1/discover/movies",
            "tv_popular": "/api/v1/discover/tv",
            "upcoming": "/api/v1/discover/movies/upcoming",
        }
        endpoint = path_map.get(category, "/api/v1/discover/trending")
        data = await self.request("GET", endpoint, params={"page": page})
        results = data.get("results", []) if isinstance(data, dict) else []
        return [
            {
                "id": r.get("id"),
                "mediaType": r.get("mediaType", "movie" if "movies" in category else "tv"),
                "title": r.get("title") or r.get("name"),
                "releaseDate": r.get("releaseDate") or r.get("firstAirDate"),
                "status_in_homelab": self._format_media_status(r.get("mediaInfo")),
                "overview": (r.get("overview") or "")[:250],
            }
            for r in results[:20]
        ]

    async def get_requests(self, filter_status: str = "all", take: int = 20, skip: int = 0) -> dict[str, Any]:
        params = {"take": take, "skip": skip}
        if filter_status != "all":
            params["filter"] = filter_status
        data = await self.request("GET", "/api/v1/request", params=params)
        results = data.get("results", []) if isinstance(data, dict) else []
        page_info = data.get("pageInfo", {}) if isinstance(data, dict) else {}
        formatted = []
        for req in results:
            media = req.get("media") or {}
            requested_by = req.get("requestedBy") or {}
            formatted.append(
                {
                    "requestId": req.get("id"),
                    "status": req.get("status"),
                    "mediaType": req.get("type"),
                    "tmdbId": media.get("tmdbId"),
                    "requestedBy": requested_by.get("displayName") or requested_by.get("email"),
                    "createdAt": req.get("createdAt"),
                }
            )
        return {
            "total": page_info.get("results", len(formatted)),
            "requests": formatted,
        }

    async def create_request(
        self,
        media_id: int,
        media_type: str = "movie",
        seasons: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        m_type = str(media_type).lower().strip()
        payload: dict[str, Any] = {
            "mediaId": int(media_id),
            "mediaType": m_type,
        }
        if m_type == "tv":
            payload["seasons"] = seasons if seasons is not None else "all"
        res = await self.request("POST", "/api/v1/request", json_data=payload)
        return {"action": "created_request", "result": res}

    async def manage_request(self, request_id: int, action: str) -> dict[str, Any]:
        act_lower = action.lower()
        if act_lower == "approve":
            res = await self.request("POST", f"/api/v1/request/{request_id}/approve")
        elif act_lower == "decline":
            res = await self.request("POST", f"/api/v1/request/{request_id}/decline")
        elif act_lower == "delete":
            res = await self.request("DELETE", f"/api/v1/request/{request_id}")
        else:
            raise ValueError(f"Unsupported action '{action}'. Supported: approve, decline, delete.")
        return {"action": act_lower, "requestId": request_id, "result": res}

    async def get_issues(self, take: int = 20) -> list[dict[str, Any]]:
        data = await self.request("GET", "/api/v1/issue", params={"take": take})
        results = data.get("results", []) if isinstance(data, dict) else []
        return [
            {
                "id": iss.get("id"),
                "issueType": iss.get("issueType"),
                "media": (iss.get("media") or {}).get("tmdbId"),
                "createdBy": (iss.get("createdBy") or {}).get("displayName"),
                "createdAt": iss.get("createdAt"),
            }
            for iss in results
        ]


jellyseerr_service = JellyseerrService()


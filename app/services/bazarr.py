from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient


class BazarrService(BaseServiceClient):
    """Asynchronous client for Bazarr API."""

    def __init__(self) -> None:
        super().__init__(
            service_name="Bazarr",
            base_url=settings.BAZARR_URL,
            default_headers={"X-API-KEY": settings.BAZARR_API_KEY},
        )

    async def get_status(self) -> dict[str, Any]:
        status = await self.request("GET", "/api/system/status")
        providers = await self.request("GET", "/api/providers")
        return {
            "status": status,
            "providers": providers if isinstance(providers, list) else [],
        }

    async def get_wanted_movies(self, page: int = 1, limit: int = 30) -> dict[str, Any]:
        data = await self.request("GET", "/api/movies/wanted", params={"start": (page - 1) * limit, "length": limit})
        data_list = data.get("data", []) if isinstance(data, dict) else []
        return {
            "total": data.get("total", len(data_list)) if isinstance(data, dict) else len(data_list),
            "movies": [
                {
                    "radarrId": m.get("radarrId"),
                    "title": m.get("title"),
                    "year": m.get("year"),
                    "missing_subtitles": m.get("missing_subtitles", []),
                }
                for m in data_list
            ],
        }

    async def get_wanted_episodes(self, page: int = 1, limit: int = 30) -> dict[str, Any]:
        data = await self.request("GET", "/api/episodes/wanted", params={"start": (page - 1) * limit, "length": limit})
        data_list = data.get("data", []) if isinstance(data, dict) else []
        return {
            "total": data.get("total", len(data_list)) if isinstance(data, dict) else len(data_list),
            "episodes": [
                {
                    "sonarrEpisodeId": ep.get("sonarrEpisodeId"),
                    "seriesTitle": ep.get("seriesTitle"),
                    "episode_number": str(ep.get("episode_number") or ""),
                    "missing_subtitles": ep.get("missing_subtitles", []),
                }
                for ep in data_list
            ],
        }

    async def search_and_download_subtitles(
        self,
        radarr_id: Optional[int] = None,
        sonarr_episode_id: Optional[int] = None,
        language: str = "vi",
    ) -> dict[str, Any]:
        if radarr_id is not None:
            res = await self.request(
                "POST",
                "/api/movies/subtitles",
                params={"action": "search", "radarrId": radarr_id, "language": language},
            )
            return {"action": "searched_movie_subtitles", "radarrId": radarr_id, "language": language, "result": res}
        if sonarr_episode_id is not None:
            res = await self.request(
                "POST",
                "/api/episodes/subtitles",
                params={"action": "search", "sonarrEpisodeId": sonarr_episode_id, "language": language},
            )
            return {
                "action": "searched_episode_subtitles",
                "sonarrEpisodeId": sonarr_episode_id,
                "language": language,
                "result": res,
            }
        raise ValueError("Provide either radarr_id or sonarr_episode_id.")

    async def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        history = await self.request("GET", "/api/history", params={"length": limit})
        data = history.get("data", []) if isinstance(history, dict) else []
        return [
            {
                "id": h.get("id"),
                "title": h.get("title"),
                "language": h.get("language"),
                "provider": h.get("provider"),
                "score": h.get("score"),
                "date": h.get("timestamp"),
            }
            for h in data
        ]


bazarr_service = BazarrService()


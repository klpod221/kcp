from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes


class SonarrService(BaseServiceClient):
    """Asynchronous client for Sonarr API v3."""

    def __init__(self) -> None:
        super().__init__(
            service_name="Sonarr",
            base_url=settings.SONARR_URL,
            default_headers={"X-Api-Key": settings.SONARR_API_KEY},
        )

    def _summarize_series(self, s: dict[str, Any], detailed: bool = False) -> dict[str, Any]:
        stats = s.get("statistics") or {}
        summary: dict[str, Any] = {
            "id": s.get("id"),
            "tvdbId": s.get("tvdbId"),
            "imdbId": s.get("imdbId"),
            "title": s.get("title"),
            "year": s.get("year"),
            "status": s.get("status"),
            "seriesType": s.get("seriesType"),
            "monitored": s.get("monitored"),
            "qualityProfileId": s.get("qualityProfileId"),
            "seasonCount": stats.get("seasonCount"),
            "episodeFileCount": stats.get("episodeFileCount", 0),
            "episodeCount": stats.get("episodeCount", 0),
            "totalEpisodeCount": stats.get("totalEpisodeCount", 0),
            "percentOfEpisodes": round(float(stats.get("percentOfEpisodes", 0.0)), 1),
            "sizeOnDisk": format_bytes(stats.get("sizeOnDisk", 0)),
            "path": s.get("path"),
        }
        if detailed:
            summary["overview"] = s.get("overview")
            summary["network"] = s.get("network")
            summary["genres"] = s.get("genres", [])
            summary["nextAiring"] = s.get("nextAiring")
            summary["previousAiring"] = s.get("previousAiring")
            summary["seasons"] = [
                {
                    "seasonNumber": sea.get("seasonNumber"),
                    "monitored": sea.get("monitored"),
                    "episodeFileCount": (sea.get("statistics") or {}).get("episodeFileCount", 0),
                    "totalEpisodeCount": (sea.get("statistics") or {}).get("totalEpisodeCount", 0),
                    "sizeOnDisk": format_bytes((sea.get("statistics") or {}).get("sizeOnDisk", 0)),
                }
                for sea in s.get("seasons", [])
            ]
        return summary

    async def lookup_series(self, query: str) -> list[dict[str, Any]]:
        results = await self.request("GET", "/api/v3/series/lookup", params={"term": query})
        if not isinstance(results, list):
            return []
        return [
            {
                "title": r.get("title"),
                "year": r.get("year"),
                "tvdbId": r.get("tvdbId"),
                "imdbId": r.get("imdbId"),
                "status": r.get("status"),
                "seriesType": r.get("seriesType"),
                "network": r.get("network"),
                "seasonCount": (r.get("statistics") or {}).get("seasonCount") or len(r.get("seasons", [])),
                "genres": r.get("genres", []),
                "inLibrary": r.get("id") is not None and r.get("id", 0) > 0,
                "sonarrId": r.get("id"),
                "overview": (r.get("overview") or "")[:350],
            }
            for r in results[:20]
        ]

    async def get_series(
        self,
        search: Optional[str] = None,
        monitored: Optional[bool] = None,
        series_type: Optional[str] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        series_list = await self.request("GET", "/api/v3/series")
        if not isinstance(series_list, list):
            return {"total": 0, "series": []}

        filtered = []
        search_lower = search.lower().strip() if search else None
        for s in series_list:
            if search_lower:
                t_match = search_lower in (s.get("title") or "").lower()
                tvdb_match = search_lower == str(s.get("tvdbId"))
                if not (t_match or tvdb_match):
                    continue
            if monitored is not None and bool(s.get("monitored")) != monitored:
                continue
            if series_type and (s.get("seriesType") or "").lower() != series_type.lower():
                continue
            filtered.append(self._summarize_series(s))

        return {
            "total_in_library": len(series_list),
            "matched_count": len(filtered),
            "showing": min(len(filtered), limit),
            "series": filtered[:limit],
        }

    async def get_series_details(
        self,
        series_id: int,
        season_number: Optional[int] = None,
        include_episodes: bool = True,
    ) -> dict[str, Any]:
        s = await self.request("GET", f"/api/v3/series/{series_id}")
        result = self._summarize_series(s, detailed=True)

        if include_episodes:
            params: dict[str, Any] = {"seriesId": series_id}
            if season_number is not None:
                params["seasonNumber"] = season_number
            episodes = await self.request("GET", "/api/v3/episode", params=params)
            if isinstance(episodes, list):
                result["episodes"] = [
                    {
                        "id": ep.get("id"),
                        "seasonNumber": ep.get("seasonNumber"),
                        "episodeNumber": ep.get("episodeNumber"),
                        "title": ep.get("title"),
                        "airDate": ep.get("airDate"),
                        "hasFile": ep.get("hasFile", False),
                        "monitored": ep.get("monitored", False),
                    }
                    for ep in episodes[:120]
                ]
                result["total_episodes_returned"] = len(episodes)
        return result

    async def add_series(
        self,
        tvdb_id: int,
        series_type: str = "standard",
        quality_profile_id: Optional[int] = None,
        root_folder_path: Optional[str] = None,
        monitor_mode: str = "all",
        season_folder: bool = True,
        search_for_missing_episodes: bool = True,
    ) -> dict[str, Any]:
        results = await self.request("GET", "/api/v3/series/lookup", params={"term": f"tvdb:{tvdb_id}"})
        if not isinstance(results, list) or not results:
            raise RuntimeError(f"Could not find series with tvdbId={tvdb_id}")

        lookup = results[0]
        if lookup.get("id"):
            return {
                "message": "Series already exists in Sonarr library.",
                "series": self._summarize_series(lookup),
            }

        payload = {
            "title": lookup.get("title"),
            "year": lookup.get("year"),
            "tvdbId": lookup.get("tvdbId"),
            "titleSlug": lookup.get("titleSlug"),
            "images": lookup.get("images", []),
            "seasons": lookup.get("seasons", []),
            "qualityProfileId": quality_profile_id or settings.SONARR_DEFAULT_QUALITY_PROFILE_ID,
            "rootFolderPath": root_folder_path or settings.SONARR_DEFAULT_ROOT_FOLDER,
            "seriesType": series_type,
            "seasonFolder": season_folder,
            "monitored": True,
            "addOptions": {
                "monitor": monitor_mode,
                "searchForMissingEpisodes": search_for_missing_episodes,
                "searchForCutoffUnmetEpisodes": False,
            },
        }
        created = await self.request("POST", "/api/v3/series", json_data=payload)
        return {
            "message": f"Added series '{created.get('title')}' to Sonarr.",
            "series": self._summarize_series(created),
        }

    async def update_monitoring(
        self,
        series_id: int,
        monitored: Optional[bool] = None,
        season_number: Optional[int] = None,
        episode_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        if episode_ids:
            await self.request(
                "PUT",
                "/api/v3/episode/monitor",
                json_data={"episodeIds": episode_ids, "monitored": bool(monitored)},
            )
            return {
                "message": f"Updated monitoring={bool(monitored)} for episodes {episode_ids}.",
            }

        series = await self.request("GET", f"/api/v3/series/{series_id}")
        if season_number is not None and monitored is not None:
            for sea in series.get("seasons", []):
                if sea.get("seasonNumber") == season_number:
                    sea["monitored"] = monitored
        elif monitored is not None:
            series["monitored"] = monitored

        updated = await self.request("PUT", f"/api/v3/series/{series_id}", json_data=series)
        return {
            "message": f"Updated monitoring for series '{updated.get('title')}'.",
            "series": self._summarize_series(updated, detailed=True),
        }

    async def delete_series(
        self,
        series_id: int,
        delete_files: bool = False,
        add_import_list_exclusion: bool = False,
    ) -> dict[str, Any]:
        s = await self.request("GET", f"/api/v3/series/{series_id}")
        title = s.get("title", f"ID {series_id}")
        await self.request(
            "DELETE",
            f"/api/v3/series/{series_id}",
            params={
                "deleteFiles": str(delete_files).lower(),
                "addImportListExclusion": str(add_import_list_exclusion).lower(),
            },
        )
        return {
            "status": "deleted",
            "series_id": series_id,
            "title": title,
            "deleted_files_from_disk": delete_files,
        }

    async def get_queue(self, page: int = 1, page_size: int = 30) -> dict[str, Any]:
        data = await self.request(
            "GET",
            "/api/v3/queue",
            params={
                "page": page,
                "pageSize": page_size,
                "includeSeries": "true",
                "includeEpisode": "true",
            },
        )
        records = data.get("records", []) if isinstance(data, dict) else []
        items = []
        for r in records:
            size = r.get("size", 0)
            sizeleft = r.get("sizeleft", 0)
            progress = round(((size - sizeleft) / size) * 100.0, 1) if size > 0 else 0.0
            ep = r.get("episode") or {}
            items.append(
                {
                    "id": r.get("id"),
                    "seriesId": r.get("seriesId"),
                    "seriesTitle": (r.get("series") or {}).get("title"),
                    "episode": (
                        f"S{ep.get('seasonNumber', 0):02d}E{ep.get('episodeNumber', 0):02d} - {ep.get('title')}"
                        if ep
                        else None
                    ),
                    "releaseTitle": r.get("title"),
                    "status": r.get("status"),
                    "trackedDownloadStatus": r.get("trackedDownloadStatus"),
                    "trackedDownloadState": r.get("trackedDownloadState"),
                    "quality": (r.get("quality") or {}).get("quality", {}).get("name"),
                    "size": format_bytes(size),
                    "sizeleft": format_bytes(sizeleft),
                    "progress_percent": progress,
                    "timeleft": r.get("timeleft"),
                    "downloadClient": r.get("downloadClient"),
                    "statusMessages": r.get("statusMessages", []),
                }
            )
        return {
            "totalRecords": data.get("totalRecords", len(items)) if isinstance(data, dict) else len(items),
            "items": items,
        }

    async def get_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        unmonitored: bool = False,
    ) -> list[dict[str, Any]]:
        results = await self.request(
            "GET",
            "/api/v3/calendar",
            params={
                "start": start_date,
                "end": end_date,
                "unmonitored": str(unmonitored).lower(),
                "includeSeries": "true",
            },
        )
        if not isinstance(results, list):
            return []
        return [
            {
                "episodeId": ep.get("id"),
                "seriesId": ep.get("seriesId"),
                "seriesTitle": (ep.get("series") or {}).get("title"),
                "seasonNumber": ep.get("seasonNumber"),
                "episodeNumber": ep.get("episodeNumber"),
                "episodeTitle": ep.get("title"),
                "airDateUtc": ep.get("airDateUtc"),
                "hasFile": ep.get("hasFile", False),
                "monitored": ep.get("monitored", False),
            }
            for ep in results
        ]

    async def get_missing(self, page: int = 1, page_size: int = 30) -> dict[str, Any]:
        data = await self.request(
            "GET",
            "/api/v3/wanted/missing",
            params={"page": page, "pageSize": page_size, "includeSeries": "true"},
        )
        records = data.get("records", []) if isinstance(data, dict) else []
        return {
            "totalRecords": data.get("totalRecords", len(records)) if isinstance(data, dict) else len(records),
            "episodes": [
                {
                    "episodeId": ep.get("id"),
                    "seriesId": ep.get("seriesId"),
                    "seriesTitle": (ep.get("series") or {}).get("title"),
                    "seasonNumber": ep.get("seasonNumber"),
                    "episodeNumber": ep.get("episodeNumber"),
                    "title": ep.get("title"),
                    "airDate": ep.get("airDate"),
                }
                for ep in records
            ],
        }

    async def trigger_search(
        self,
        series_id: Optional[int] = None,
        season_number: Optional[int] = None,
        episode_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        if episode_ids:
            cmd = await self.request(
                "POST",
                "/api/v3/command",
                json_data={"name": "EpisodeSearch", "episodeIds": episode_ids},
            )
            return {"action": "EpisodeSearch", "command": cmd}
        if series_id is not None and season_number is not None:
            cmd = await self.request(
                "POST",
                "/api/v3/command",
                json_data={
                    "name": "SeasonSearch",
                    "seriesId": series_id,
                    "seasonNumber": season_number,
                },
            )
            return {"action": "SeasonSearch", "command": cmd}
        if series_id is not None:
            cmd = await self.request(
                "POST",
                "/api/v3/command",
                json_data={"name": "SeriesSearch", "seriesId": series_id},
            )
            return {"action": "SeriesSearch", "command": cmd}
        raise ValueError("Provide episode_ids, (series_id and season_number), or series_id.")

    async def search_releases(
        self,
        episode_id: Optional[int] = None,
        series_id: Optional[int] = None,
        season_number: Optional[int] = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if episode_id is not None:
            params["episodeId"] = episode_id
        if series_id is not None:
            params["seriesId"] = series_id
        if season_number is not None:
            params["seasonNumber"] = season_number

        releases = await self.request("GET", "/api/v3/release", params=params)
        if not isinstance(releases, list):
            return []
        return [
            {
                "guid": rel.get("guid"),
                "indexerId": rel.get("indexerId"),
                "indexer": rel.get("indexer"),
                "title": rel.get("title"),
                "quality": (rel.get("quality") or {}).get("quality", {}).get("name"),
                "size": format_bytes(rel.get("size", 0)),
                "seeders": rel.get("seeders"),
                "leechers": rel.get("leechers"),
                "protocol": rel.get("protocol"),
                "customFormatScore": rel.get("customFormatScore"),
                "rejected": rel.get("rejected", False),
                "rejections": rel.get("rejections", []),
            }
            for rel in releases[:limit]
        ]

    async def grab_release(self, guid: str, indexer_id: int) -> dict[str, Any]:
        res = await self.request(
            "POST",
            "/api/v3/release",
            json_data={"guid": guid, "indexerId": indexer_id},
        )
        return {"action": "grabbed_release", "result": res}

    async def get_system_info(self) -> dict[str, Any]:
        status = await self.request("GET", "/api/v3/system/status")
        profiles = await self.request("GET", "/api/v3/qualityprofile")
        root_folders = await self.request("GET", "/api/v3/rootfolder")
        health = await self.request("GET", "/api/v3/health")
        return {
            "version": status.get("version") if isinstance(status, dict) else None,
            "qualityProfiles": [
                {"id": p.get("id"), "name": p.get("name")}
                for p in (profiles if isinstance(profiles, list) else [])
            ],
            "rootFolders": [
                {
                    "id": rf.get("id"),
                    "path": rf.get("path"),
                    "accessible": rf.get("accessible"),
                    "freeSpace": format_bytes(rf.get("freeSpace", 0)),
                }
                for rf in (root_folders if isinstance(root_folders, list) else [])
            ],
            "healthWarnings": health if isinstance(health, list) else [],
        }


sonarr_service = SonarrService()


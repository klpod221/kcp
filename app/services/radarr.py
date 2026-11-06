from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes


class RadarrService(BaseServiceClient):
    """Asynchronous client for Radarr API v3."""

    def __init__(self) -> None:
        super().__init__(
            service_name="Radarr",
            base_url=settings.RADARR_URL,
            default_headers={"X-Api-Key": settings.RADARR_API_KEY},
        )

    def _summarize_movie(self, m: dict[str, Any], detailed: bool = False) -> dict[str, Any]:
        movie_file = m.get("movieFile") or {}
        quality_name = (
            movie_file.get("quality", {}).get("quality", {}).get("name")
            if isinstance(movie_file, dict)
            else None
        )
        summary: dict[str, Any] = {
            "id": m.get("id"),
            "tmdbId": m.get("tmdbId"),
            "imdbId": m.get("imdbId"),
            "title": m.get("title"),
            "year": m.get("year"),
            "status": m.get("status"),
            "monitored": m.get("monitored"),
            "hasFile": m.get("hasFile", False),
            "sizeOnDisk": format_bytes(m.get("sizeOnDisk", 0)),
            "qualityProfileId": m.get("qualityProfileId"),
            "quality": quality_name,
            "runtime_minutes": m.get("runtime"),
            "path": m.get("path"),
        }
        if detailed:
            summary["overview"] = m.get("overview")
            summary["genres"] = m.get("genres", [])
            summary["studio"] = m.get("studio")
            summary["added"] = m.get("added")
            summary["inCinemas"] = m.get("inCinemas")
            summary["digitalRelease"] = m.get("digitalRelease")
            summary["physicalRelease"] = m.get("physicalRelease")
            summary["ratings"] = m.get("ratings", {})
            if movie_file:
                summary["fileDetails"] = {
                    "id": movie_file.get("id"),
                    "relativePath": movie_file.get("relativePath"),
                    "size": format_bytes(movie_file.get("size", 0)),
                    "dateAdded": movie_file.get("dateAdded"),
                    "releaseGroup": movie_file.get("releaseGroup"),
                    "quality": quality_name,
                    "mediaInfo": {
                        "videoCodec": (movie_file.get("mediaInfo") or {}).get("videoCodec"),
                        "audioCodec": (movie_file.get("mediaInfo") or {}).get("audioCodec"),
                        "audioChannels": (movie_file.get("mediaInfo") or {}).get("audioChannels"),
                        "resolution": (movie_file.get("mediaInfo") or {}).get("resolution"),
                        "subtitles": (movie_file.get("mediaInfo") or {}).get("subtitles"),
                    },
                }
        return summary

    async def lookup_movies(self, query: str) -> list[dict[str, Any]]:
        results = await self.request("GET", "/api/v3/movie/lookup", params={"term": query})
        if not isinstance(results, list):
            return []
        return [
            {
                "title": r.get("title"),
                "year": r.get("year"),
                "tmdbId": r.get("tmdbId"),
                "imdbId": r.get("imdbId"),
                "status": r.get("status"),
                "runtime_minutes": r.get("runtime"),
                "genres": r.get("genres", []),
                "inLibrary": r.get("id") is not None and r.get("id", 0) > 0,
                "radarrId": r.get("id"),
                "hasFile": r.get("hasFile", False),
                "overview": (r.get("overview") or "")[:350],
            }
            for r in results[:20]
        ]

    async def get_movies(
        self,
        search: Optional[str] = None,
        monitored: Optional[bool] = None,
        has_file: Optional[bool] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        movies = await self.request("GET", "/api/v3/movie")
        if not isinstance(movies, list):
            return {"total": 0, "movies": []}

        filtered = []
        search_lower = search.lower().strip() if search else None
        for m in movies:
            if search_lower:
                title_match = search_lower in (m.get("title") or "").lower()
                orig_match = search_lower in (m.get("originalTitle") or "").lower()
                tmdb_match = search_lower == str(m.get("tmdbId"))
                if not (title_match or orig_match or tmdb_match):
                    continue
            if monitored is not None and bool(m.get("monitored")) != monitored:
                continue
            if has_file is not None and bool(m.get("hasFile")) != has_file:
                continue
            filtered.append(self._summarize_movie(m))

        return {
            "total_in_library": len(movies),
            "matched_count": len(filtered),
            "showing": min(len(filtered), limit),
            "movies": filtered[:limit],
        }

    async def get_movie_details(self, movie_id: int) -> dict[str, Any]:
        m = await self.request("GET", f"/api/v3/movie/{movie_id}")
        return self._summarize_movie(m, detailed=True)

    async def add_movie(
        self,
        tmdb_id: int,
        quality_profile_id: Optional[int] = None,
        root_folder_path: Optional[str] = None,
        monitored: bool = True,
        minimum_availability: str = "released",
        search_for_movie: bool = True,
    ) -> dict[str, Any]:
        lookup = await self.request("GET", "/api/v3/movie/lookup/tmdb", params={"tmdbId": tmdb_id})
        if not isinstance(lookup, dict) or not lookup.get("tmdbId"):
            raise RuntimeError(f"Could not find movie with tmdbId={tmdb_id}")

        if lookup.get("id"):
            return {
                "message": "Movie already exists in Radarr library.",
                "movie": self._summarize_movie(lookup),
            }

        payload = {
            "title": lookup.get("title"),
            "year": lookup.get("year"),
            "tmdbId": lookup.get("tmdbId"),
            "titleSlug": lookup.get("titleSlug"),
            "images": lookup.get("images", []),
            "qualityProfileId": quality_profile_id or settings.RADARR_DEFAULT_QUALITY_PROFILE_ID,
            "rootFolderPath": root_folder_path or settings.RADARR_DEFAULT_ROOT_FOLDER,
            "monitored": monitored,
            "minimumAvailability": minimum_availability,
            "addOptions": {
                "searchForMovie": search_for_movie,
            },
        }
        created = await self.request("POST", "/api/v3/movie", json_data=payload)
        return {
            "message": f"Added movie '{created.get('title')}' ({created.get('year')}) to Radarr.",
            "movie": self._summarize_movie(created),
        }

    async def update_movie(
        self,
        movie_id: int,
        monitored: Optional[bool] = None,
        quality_profile_id: Optional[int] = None,
        minimum_availability: Optional[str] = None,
    ) -> dict[str, Any]:
        movie = await self.request("GET", f"/api/v3/movie/{movie_id}")
        if monitored is not None:
            movie["monitored"] = monitored
        if quality_profile_id is not None:
            movie["qualityProfileId"] = quality_profile_id
        if minimum_availability is not None:
            movie["minimumAvailability"] = minimum_availability

        updated = await self.request("PUT", f"/api/v3/movie/{movie_id}", json_data=movie)
        return {
            "message": f"Updated movie '{updated.get('title')}' (id={movie_id}).",
            "movie": self._summarize_movie(updated),
        }

    async def delete_movie(
        self,
        movie_id: int,
        delete_files: bool = False,
        add_import_exclusion: bool = False,
    ) -> dict[str, Any]:
        movie = await self.request("GET", f"/api/v3/movie/{movie_id}")
        title = movie.get("title", f"ID {movie_id}")
        await self.request(
            "DELETE",
            f"/api/v3/movie/{movie_id}",
            params={
                "deleteFiles": str(delete_files).lower(),
                "addImportExclusion": str(add_import_exclusion).lower(),
            },
        )
        return {
            "status": "deleted",
            "movie_id": movie_id,
            "title": title,
            "deleted_files_from_disk": delete_files,
        }

    async def get_queue(self, page: int = 1, page_size: int = 30) -> dict[str, Any]:
        data = await self.request(
            "GET",
            "/api/v3/queue",
            params={"page": page, "pageSize": page_size, "includeMovie": "true"},
        )
        records = data.get("records", []) if isinstance(data, dict) else []
        items = []
        for r in records:
            size = r.get("size", 0)
            sizeleft = r.get("sizeleft", 0)
            progress = round(((size - sizeleft) / size) * 100.0, 1) if size > 0 else 0.0
            items.append(
                {
                    "id": r.get("id"),
                    "movieId": r.get("movieId"),
                    "movieTitle": (r.get("movie") or {}).get("title") or r.get("title"),
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
                    "indexer": r.get("indexer"),
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
            },
        )
        if not isinstance(results, list):
            return []
        return [
            {
                "id": m.get("id"),
                "title": m.get("title"),
                "year": m.get("year"),
                "status": m.get("status"),
                "inCinemas": m.get("inCinemas"),
                "digitalRelease": m.get("digitalRelease"),
                "physicalRelease": m.get("physicalRelease"),
                "hasFile": m.get("hasFile"),
                "monitored": m.get("monitored"),
            }
            for m in results
        ]

    async def search_releases(self, movie_id: int, limit: int = 25) -> list[dict[str, Any]]:
        releases = await self.request("GET", "/api/v3/release", params={"movieId": movie_id})
        if not isinstance(releases, list):
            return []
        formatted = []
        for rel in releases[:limit]:
            formatted.append(
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
            )
        return formatted

    async def grab_release(
        self,
        guid: Optional[str] = None,
        indexer_id: Optional[int] = None,
        movie_id: Optional[int] = None,
    ) -> dict[str, Any]:
        if guid and indexer_id is not None:
            res = await self.request(
                "POST",
                "/api/v3/release",
                json_data={"guid": guid, "indexerId": indexer_id},
            )
            return {"action": "grabbed_specific_release", "result": res}
        if movie_id is not None:
            res = await self.request(
                "POST",
                "/api/v3/command",
                json_data={"name": "MoviesSearch", "movieIds": [movie_id]},
            )
            return {"action": "triggered_automatic_movie_search", "command": res}
        raise ValueError("Provide either (guid and indexer_id) or movie_id.")

    async def get_system_info(self) -> dict[str, Any]:
        status = await self.request("GET", "/api/v3/system/status")
        profiles = await self.request("GET", "/api/v3/qualityprofile")
        root_folders = await self.request("GET", "/api/v3/rootfolder")
        disks = await self.request("GET", "/api/v3/diskspace")
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
            "diskSpace": [
                {
                    "path": d.get("path"),
                    "label": d.get("label"),
                    "freeSpace": format_bytes(d.get("freeSpace", 0)),
                    "totalSpace": format_bytes(d.get("totalSpace", 0)),
                }
                for d in (disks if isinstance(disks, list) else [])
            ],
            "healthWarnings": health if isinstance(health, list) else [],
        }


radarr_service = RadarrService()


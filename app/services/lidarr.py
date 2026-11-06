from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes


class LidarrService(BaseServiceClient):
    """Asynchronous client for Lidarr API v1."""

    def __init__(self) -> None:
        super().__init__(
            service_name="Lidarr",
            base_url=settings.LIDARR_URL,
            default_headers={"X-Api-Key": settings.LIDARR_API_KEY},
        )

    def _summarize_artist(self, a: dict[str, Any]) -> dict[str, Any]:
        stats = a.get("statistics") or {}
        return {
            "id": a.get("id"),
            "artistName": a.get("artistName"),
            "foreignArtistId": a.get("foreignArtistId"),
            "status": a.get("status"),
            "monitored": a.get("monitored"),
            "qualityProfileId": a.get("qualityProfileId"),
            "metadataProfileId": a.get("metadataProfileId"),
            "albumCount": stats.get("albumCount", 0),
            "trackFileCount": stats.get("trackFileCount", 0),
            "trackCount": stats.get("trackCount", 0),
            "percentOfTracks": round(float(stats.get("percentOfTracks", 0.0)), 1),
            "sizeOnDisk": format_bytes(stats.get("sizeOnDisk", 0)),
            "path": a.get("path"),
        }

    async def search(self, query: str) -> list[dict[str, Any]]:
        results = await self.request("GET", "/api/v1/search", params={"term": query})
        if not isinstance(results, list):
            return []
        formatted = []
        for r in results[:20]:
            artist_data = r.get("artist") or r
            formatted.append(
                {
                    "artistName": artist_data.get("artistName") or r.get("foreignId"),
                    "foreignArtistId": artist_data.get("foreignArtistId"),
                    "inLibrary": artist_data.get("id") is not None and artist_data.get("id", 0) > 0,
                    "lidarrId": artist_data.get("id"),
                    "overview": (artist_data.get("overview") or "")[:300],
                }
            )
        return formatted

    async def get_artists(
        self,
        search: Optional[str] = None,
        monitored: Optional[bool] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        artists = await self.request("GET", "/api/v1/artist")
        if not isinstance(artists, list):
            return {"total": 0, "artists": []}

        filtered = []
        search_lower = search.lower().strip() if search else None
        for a in artists:
            if search_lower and search_lower not in (a.get("artistName") or "").lower():
                continue
            if monitored is not None and bool(a.get("monitored")) != monitored:
                continue
            filtered.append(self._summarize_artist(a))

        return {
            "total_in_library": len(artists),
            "matched_count": len(filtered),
            "showing": min(len(filtered), limit),
            "artists": filtered[:limit],
        }

    async def get_albums(self, artist_id: Optional[int] = None, limit: int = 50) -> list[dict[str, Any]]:
        params = {"artistId": artist_id} if artist_id else None
        albums = await self.request("GET", "/api/v1/album", params=params)
        if not isinstance(albums, list):
            return []
        formatted = []
        for alb in albums[:limit]:
            stats = alb.get("statistics") or {}
            formatted.append(
                {
                    "id": alb.get("id"),
                    "artistId": alb.get("artistId"),
                    "title": alb.get("title"),
                    "releaseDate": alb.get("releaseDate"),
                    "albumType": alb.get("albumType"),
                    "monitored": alb.get("monitored"),
                    "trackFileCount": stats.get("trackFileCount", 0),
                    "totalTrackCount": stats.get("totalTrackCount", 0),
                    "percentOfTracks": round(float(stats.get("percentOfTracks", 0.0)), 1),
                }
            )
        return formatted

    async def add_artist(
        self,
        foreign_artist_id: str,
        quality_profile_id: Optional[int] = None,
        metadata_profile_id: Optional[int] = None,
        root_folder_path: Optional[str] = None,
        monitored: bool = True,
        search_for_missing_albums: bool = True,
    ) -> dict[str, Any]:
        lookup = await self.request("GET", "/api/v1/artist/lookup", params={"term": f"lidarr:{foreign_artist_id}"})
        if not isinstance(lookup, list) or not lookup:
            raise RuntimeError(f"Could not find artist with foreignArtistId={foreign_artist_id}")

        item = lookup[0]
        if item.get("id"):
            return {
                "message": "Artist already exists in Lidarr library.",
                "artist": self._summarize_artist(item),
            }

        payload = {
            "artistName": item.get("artistName"),
            "foreignArtistId": item.get("foreignArtistId"),
            "qualityProfileId": quality_profile_id or settings.LIDARR_DEFAULT_QUALITY_PROFILE_ID,
            "metadataProfileId": metadata_profile_id or settings.LIDARR_DEFAULT_METADATA_PROFILE_ID,
            "rootFolderPath": root_folder_path or settings.LIDARR_DEFAULT_ROOT_FOLDER,
            "monitored": monitored,
            "addOptions": {
                "searchForMissingAlbums": search_for_missing_albums,
            },
        }
        created = await self.request("POST", "/api/v1/artist", json_data=payload)
        return {
            "message": f"Added artist '{created.get('artistName')}' to Lidarr.",
            "artist": self._summarize_artist(created),
        }

    async def delete_artist(self, artist_id: int, delete_files: bool = False) -> dict[str, Any]:
        artist = await self.request("GET", f"/api/v1/artist/{artist_id}")
        name = artist.get("artistName", f"ID {artist_id}")
        await self.request(
            "DELETE",
            f"/api/v1/artist/{artist_id}",
            params={"deleteFiles": str(delete_files).lower()},
        )
        return {
            "status": "deleted",
            "artist_id": artist_id,
            "artistName": name,
            "deleted_files_from_disk": delete_files,
        }

    async def get_queue(self, page: int = 1, page_size: int = 30) -> dict[str, Any]:
        data = await self.request(
            "GET",
            "/api/v1/queue",
            params={"page": page, "pageSize": page_size, "includeArtist": "true"},
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
                    "artistTitle": (r.get("artist") or {}).get("artistName"),
                    "title": r.get("title"),
                    "status": r.get("status"),
                    "size": format_bytes(size),
                    "progress_percent": progress,
                    "timeleft": r.get("timeleft"),
                }
            )
        return {
            "totalRecords": data.get("totalRecords", len(items)) if isinstance(data, dict) else len(items),
            "items": items,
        }

    async def trigger_search(
        self,
        artist_id: Optional[int] = None,
        album_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        if album_ids:
            cmd = await self.request(
                "POST",
                "/api/v1/command",
                json_data={"name": "AlbumSearch", "albumIds": album_ids},
            )
            return {"action": "AlbumSearch", "command": cmd}
        if artist_id is not None:
            cmd = await self.request(
                "POST",
                "/api/v1/command",
                json_data={"name": "ArtistSearch", "artistId": artist_id},
            )
            return {"action": "ArtistSearch", "command": cmd}
        raise ValueError("Provide artist_id or album_ids.")


lidarr_service = LidarrService()


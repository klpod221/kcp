from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes, format_seconds


class JellyfinService(BaseServiceClient):
    """Asynchronous client for Jellyfin API."""

    def __init__(self) -> None:
        super().__init__(
            service_name="Jellyfin",
            base_url=settings.JELLYFIN_URL,
            default_headers={"Authorization": f'MediaBrowser Token="{settings.JELLYFIN_API_KEY}"'},
        )

    def _summarize_item(self, item: dict[str, Any]) -> dict[str, Any]:
        run_time_ticks = item.get("RunTimeTicks")
        runtime_sec = (run_time_ticks / 10_000_000.0) if run_time_ticks else None
        return {
            "id": item.get("Id"),
            "name": item.get("Name"),
            "type": item.get("Type"),
            "productionYear": item.get("ProductionYear"),
            "seriesName": item.get("SeriesName"),
            "seasonName": item.get("SeasonName"),
            "indexNumber": item.get("IndexNumber"),
            "parentIndexNumber": item.get("ParentIndexNumber"),
            "communityRating": item.get("CommunityRating"),
            "overview": (item.get("Overview") or "")[:300],
            "runtime": format_seconds(runtime_sec) if runtime_sec else None,
            "genres": item.get("Genres", []),
        }

    async def search_media(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        data = await self.request(
            "GET",
            "/Items",
            params={
                "searchTerm": query,
                "recursive": "true",
                "limit": limit,
                "includeItemTypes": "Movie,Series,Episode,Audio",
            },
        )
        items = data.get("Items", []) if isinstance(data, dict) else []
        return [self._summarize_item(it) for it in items]

    async def get_latest(self, limit: int = 15) -> list[dict[str, Any]]:
        data = await self.request(
            "GET",
            "/Items",
            params={
                "sortBy": "DateCreated",
                "sortOrder": "Descending",
                "recursive": "true",
                "limit": limit,
                "includeItemTypes": "Movie,Episode",
            },
        )
        items = data.get("Items", []) if isinstance(data, dict) else []
        return [self._summarize_item(it) for it in items]

    async def get_item_details(self, item_id: str) -> dict[str, Any]:
        item = await self.request("GET", f"/Items/{item_id}")
        summary = self._summarize_item(item)
        summary["overview"] = item.get("Overview")
        media_sources = item.get("MediaSources", [])
        if media_sources:
            src = media_sources[0]
            summary["mediaSource"] = {
                "container": src.get("Container"),
                "size": format_bytes(src.get("Size")),
                "path": src.get("Path"),
                "streams": [
                    {
                        "type": st.get("Type"),
                        "codec": st.get("Codec"),
                        "resolution": f"{st.get('Width')}x{st.get('Height')}" if st.get("Width") else None,
                        "language": st.get("Language"),
                        "title": st.get("Title"),
                        "displayTitle": st.get("DisplayTitle"),
                        "isDefault": st.get("IsDefault"),
                    }
                    for st in src.get("MediaStreams", [])
                ],
            }
        return summary

    async def get_sessions(self) -> list[dict[str, Any]]:
        sessions = await self.request("GET", "/Sessions")
        if not isinstance(sessions, list):
            return []
        active = []
        for s in sessions:
            now_playing = s.get("NowPlayingItem")
            play_state = s.get("PlayState") or {}
            active.append(
                {
                    "sessionId": s.get("Id"),
                    "userName": s.get("UserName"),
                    "client": s.get("Client"),
                    "deviceName": s.get("DeviceName"),
                    "nowPlaying": self._summarize_item(now_playing) if now_playing else None,
                    "isPaused": play_state.get("IsPaused", False),
                    "playMethod": play_state.get("PlayMethod"),
                    "transcodingInfo": s.get("TranscodingInfo"),
                }
            )
        return active

    async def control_session(self, session_id: str, command: str, text: Optional[str] = None) -> dict[str, Any]:
        cmd_lower = command.lower()
        if cmd_lower in ["play", "unpause"]:
            await self.request("POST", f"/Sessions/{session_id}/Playing/Unpause")
        elif cmd_lower in ["pause"]:
            await self.request("POST", f"/Sessions/{session_id}/Playing/Pause")
        elif cmd_lower in ["stop"]:
            await self.request("POST", f"/Sessions/{session_id}/Playing/Stop")
        elif cmd_lower in ["message"]:
            await self.request(
                "POST",
                f"/Sessions/{session_id}/Message",
                json_data={"Header": "Message from Admin", "Text": text or "", "TimeoutMs": 5000},
            )
        else:
            raise ValueError(f"Unsupported command '{command}'. Supported: play, pause, stop, message.")
        return {"status": "success", "session_id": session_id, "command": command}

    async def scan_library(self) -> dict[str, Any]:
        await self.request("POST", "/Library/Refresh")
        return {"status": "success", "message": "Triggered Jellyfin library scan."}

    async def get_system_info(self) -> dict[str, Any]:
        sys_info = await self.request("GET", "/System/Info")
        virtual_folders = await self.request("GET", "/Library/VirtualFolders")
        users = await self.request("GET", "/Users")
        return {
            "serverName": (sys_info or {}).get("ServerName"),
            "version": (sys_info or {}).get("Version"),
            "operatingSystem": (sys_info or {}).get("OperatingSystem"),
            "libraries": [
                {"name": f.get("Name"), "itemId": f.get("ItemId"), "collectionType": f.get("CollectionType")}
                for f in (virtual_folders if isinstance(virtual_folders, list) else [])
            ],
            "users": [
                {"id": u.get("Id"), "name": u.get("Name"), "hasPassword": u.get("HasPassword")}
                for u in (users if isinstance(users, list) else [])
            ],
        }


jellyfin_service = JellyfinService()

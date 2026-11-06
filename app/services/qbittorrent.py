from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes, format_seconds


class QbittorrentService(BaseServiceClient):
    """Asynchronous client for qBittorrent WebUI API v2."""

    def __init__(self) -> None:
        super().__init__(
            service_name="qBittorrent",
            base_url=settings.QBITTORRENT_URL,
        )

    def _format_torrent(self, t: dict[str, Any]) -> dict[str, Any]:
        return {
            "hash": t.get("hash"),
            "name": t.get("name"),
            "size": format_bytes(t.get("size", 0)),
            "progress_percent": round(float(t.get("progress", 0.0)) * 100.0, 1),
            "state": t.get("state"),
            "dlspeed": f"{format_bytes(t.get('dlspeed', 0))}/s",
            "upspeed": f"{format_bytes(t.get('upspeed', 0))}/s",
            "eta": format_seconds(t.get("eta")),
            "ratio": round(float(t.get("ratio", 0.0)), 2),
            "num_seeds": t.get("num_seeds"),
            "num_leechs": t.get("num_leechs"),
            "category": t.get("category"),
            "added_on": t.get("added_on"),
            "save_path": t.get("save_path"),
        }

    async def get_torrents(
        self,
        filter_state: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if filter_state:
            params["filter"] = filter_state
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag

        data = await self.request("GET", "/api/v2/torrents/info", params=params)
        if not isinstance(data, list):
            return []
        return [self._format_torrent(t) for t in data]

    async def get_torrent_details(self, torrent_hash: str) -> dict[str, Any]:
        props = await self.request("GET", "/api/v2/torrents/properties", params={"hash": torrent_hash})
        files = await self.request("GET", "/api/v2/torrents/files", params={"hash": torrent_hash})
        trackers = await self.request("GET", "/api/v2/torrents/trackers", params={"hash": torrent_hash})

        return {
            "hash": torrent_hash,
            "save_path": props.get("save_path"),
            "total_size": format_bytes(props.get("total_size", 0)),
            "total_downloaded": format_bytes(props.get("total_downloaded", 0)),
            "total_uploaded": format_bytes(props.get("total_uploaded", 0)),
            "share_ratio": round(float(props.get("share_ratio", 0.0)), 2),
            "dl_speed_avg": f"{format_bytes(props.get('dl_speed_avg', 0))}/s",
            "up_speed_avg": f"{format_bytes(props.get('up_speed_avg', 0))}/s",
            "seeds": f"{props.get('seeds', 0)} ({props.get('seeds_total', 0)})",
            "peers": f"{props.get('peers', 0)} ({props.get('peers_total', 0)})",
            "files": [
                {
                    "index": f.get("index"),
                    "name": f.get("name"),
                    "size": format_bytes(f.get("size", 0)),
                    "progress": round(float(f.get("progress", 0.0)) * 100.0, 1),
                }
                for f in (files if isinstance(files, list) else [])[:30]
            ],
            "trackers": [
                {"url": tr.get("url"), "status": tr.get("status"), "num_peers": tr.get("num_peers")}
                for tr in (trackers if isinstance(trackers, list) else [])[:10]
            ],
        }

    async def add_torrent(
        self,
        urls: str,
        category: Optional[str] = None,
        save_path: Optional[str] = None,
        paused: bool = False,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {"urls": urls, "paused": "true" if paused else "false"}
        if category:
            data["category"] = category
        if save_path:
            data["savepath"] = save_path

        res = await self.request("POST", "/api/v2/torrents/add", data=data)
        return {"status": "submitted", "response": res}

    async def manage_torrent(self, hashes: list[str], action: str, delete_files: bool = False) -> dict[str, Any]:
        act_lower = action.lower()
        hashes_str = "|".join(hashes)
        if act_lower in ["pause", "stop"]:
            await self.request("POST", "/api/v2/torrents/stop", data={"hashes": hashes_str})
        elif act_lower in ["resume", "start"]:
            await self.request("POST", "/api/v2/torrents/start", data={"hashes": hashes_str})
        elif act_lower in ["recheck"]:
            await self.request("POST", "/api/v2/torrents/recheck", data={"hashes": hashes_str})
        elif act_lower in ["delete", "remove"]:
            await self.request(
                "POST",
                "/api/v2/torrents/delete",
                data={"hashes": hashes_str, "deleteFiles": "true" if delete_files else "false"},
            )
        else:
            raise ValueError(f"Unsupported action '{action}'. Supported: pause, resume, recheck, delete.")
        return {
            "status": "success",
            "action": act_lower,
            "hashes": hashes,
            "deleted_files_from_disk": delete_files if act_lower in ["delete", "remove"] else False,
        }

    async def set_speed_limits(
        self,
        toggle_alt_mode: Optional[bool] = None,
        dl_limit_kbs: Optional[int] = None,
        up_limit_kbs: Optional[int] = None,
    ) -> dict[str, Any]:
        if toggle_alt_mode is not None:
            await self.request("POST", "/api/v2/transfer/toggleSpeedLimitsMode")
        if dl_limit_kbs is not None:
            await self.request("POST", "/api/v2/transfer/setGlobalDlLimit", data={"limit": dl_limit_kbs * 1024})
        if up_limit_kbs is not None:
            await self.request("POST", "/api/v2/transfer/setGlobalUpLimit", data={"limit": up_limit_kbs * 1024})
        return {"status": "success", "alt_mode_toggled": toggle_alt_mode is not None}

    async def get_transfer_info(self) -> dict[str, Any]:
        transfer = await self.request("GET", "/api/v2/transfer/info")
        categories = await self.request("GET", "/api/v2/torrents/categories")
        server_state = await self.request("GET", "/api/v2/sync/maindata")
        server_st = server_state.get("server_state", {}) if isinstance(server_state, dict) else {}

        return {
            "dl_speed": f"{format_bytes((transfer or {}).get('dl_info_speed', 0))}/s",
            "up_speed": f"{format_bytes((transfer or {}).get('up_info_speed', 0))}/s",
            "dl_total": format_bytes((transfer or {}).get("dl_info_data", 0)),
            "up_total": format_bytes((transfer or {}).get("up_info_data", 0)),
            "connection_status": (transfer or {}).get("connection_status"),
            "free_space_on_disk": format_bytes(server_st.get("free_space_on_disk", 0)),
            "categories": list(categories.keys()) if isinstance(categories, dict) else [],
        }


qbittorrent_service = QbittorrentService()


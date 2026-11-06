import shutil
from typing import Any, Optional

from app.config import settings
from app.services.base import BaseServiceClient, format_bytes, format_seconds


class RcloneService(BaseServiceClient):
    """Asynchronous client for Rclone Remote Control (RC) API."""

    def __init__(self) -> None:
        super().__init__(
            service_name="RcloneRC",
            base_url=settings.RCLONE_RC_URL,
            default_headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    async def get_status(self) -> dict[str, Any]:
        """Retrieves comprehensive VFS cache stats, mount storage usage, and transfer stats."""
        vfs_stats = await self.request("POST", "/vfs/stats", json_data={})
        core_stats = await self.request("POST", "/core/stats", json_data={})

        disk_usage: dict[str, Any] = {}
        try:
            usage = shutil.disk_usage(settings.RCLONE_MOUNT_PATH)
            disk_usage = {
                "mount_path": settings.RCLONE_MOUNT_PATH,
                "total": format_bytes(usage.total),
                "used": format_bytes(usage.used),
                "free": format_bytes(usage.free),
                "usage_percent": round((usage.used / usage.total) * 100.0, 1) if usage.total > 0 else 0.0,
            }
        except Exception as exc:
            disk_usage = {"error": str(exc)}

        disk_cache = vfs_stats.get("diskCache", {}) if isinstance(vfs_stats, dict) else {}
        meta_cache = vfs_stats.get("metadataCache", {}) if isinstance(vfs_stats, dict) else {}

        return {
            "vfs_cache": {
                "bytes_used": format_bytes(disk_cache.get("bytesUsed", 0)),
                "files_in_cache": disk_cache.get("files", 0),
                "uploads_queued": disk_cache.get("uploadsQueued", 0),
                "uploads_in_progress": disk_cache.get("uploadsInProgress", 0),
                "out_of_space": disk_cache.get("outOfSpace", False),
                "cache_path": disk_cache.get("path"),
                "dirs_cached": meta_cache.get("dirs", 0),
                "files_cached": meta_cache.get("files", 0),
            },
            "cloud_storage_disk_space": disk_usage,
            "core_transfers": {
                "speed": f"{format_bytes(core_stats.get('speed', 0))}/s",
                "bytes_transferred": format_bytes(core_stats.get("bytes", 0)),
                "total_transfers": core_stats.get("transfers", 0),
                "errors": core_stats.get("errors", 0),
                "last_error": core_stats.get("lastError"),
                "elapsed_time": format_seconds(core_stats.get("elapsedTime")),
            },
        }

    async def refresh_directory_cache(
        self,
        dir_path: Optional[str] = None,
        recursive: bool = True,
    ) -> dict[str, Any]:
        """Refreshes the directory cache so new cloud files appear immediately without unmounting.

        Args:
            dir_path: Optional relative directory under the mount (e.g. 'Media/Movies'). If omitted, refreshes root.
            recursive: Whether to recursively refresh subdirectories (default True).
        """
        payload: dict[str, Any] = {"recursive": recursive}
        if dir_path:
            payload["dir"] = dir_path.strip("/")

        res = await self.request("POST", "/vfs/refresh", json_data=payload)
        return {
            "status": "success",
            "refreshed_dir": dir_path or "root",
            "recursive": recursive,
            "result": res.get("result", res) if isinstance(res, dict) else res,
        }

    async def forget_cache(self, dir_path: Optional[str] = None) -> dict[str, Any]:
        """Forgets cached directory contents from memory.

        Args:
            dir_path: Optional relative directory path to forget. If omitted, forgets all cached directories.
        """
        payload = {"dir": dir_path.strip("/")} if dir_path else {}
        res = await self.request("POST", "/vfs/forget", json_data=payload)
        return {"status": "success", "result": res}


rclone_service = RcloneService()


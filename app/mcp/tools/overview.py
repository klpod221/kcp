import asyncio
import time
from typing import Any

from app.config import settings
from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.bazarr import bazarr_service
from app.services.jellyfin import jellyfin_service
from app.services.jellyseerr import jellyseerr_service
from app.services.lidarr import lidarr_service
from app.services.prowlarr import prowlarr_service
from app.services.qbittorrent import qbittorrent_service
from app.services.radarr import radarr_service
from app.services.rclone import rclone_service
from app.services.sonarr import sonarr_service
from app.services.system_monitor import system_monitor_service
from app.services.trilium import trilium_service


async def _probe_radarr() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        movies_res = await radarr_service.get_movies(limit=500)
        r_queue = await radarr_service.get_queue(page=1, page_size=1)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        movies_list = movies_res.get("movies", []) if isinstance(movies_res, dict) else movies_res
        total_movies = (
            movies_res.get("total_in_library", len(movies_list))
            if isinstance(movies_res, dict)
            else len(movies_list)
        )
        monitored = sum(1 for m in movies_list if isinstance(m, dict) and m.get("monitored"))
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.RADARR_URL,
            "movies_count": total_movies,
            "monitored_movies": monitored,
            "download_queue_count": r_queue.get("totalRecords", 0),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.RADARR_URL, "error": str(exc)}


async def _probe_sonarr() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        series_res = await sonarr_service.get_series(limit=500)
        s_queue = await sonarr_service.get_queue(page=1, page_size=1)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        series_list = series_res.get("series", []) if isinstance(series_res, dict) else series_res
        total_series = (
            series_res.get("total_in_library", len(series_list))
            if isinstance(series_res, dict)
            else len(series_list)
        )
        total_eps = sum(
            int((s.get("statistics") or {}).get("episodeFileCount") or s.get("episodeFileCount") or 0)
            for s in series_list
            if isinstance(s, dict)
        )
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.SONARR_URL,
            "series_count": total_series,
            "episodes_count": total_eps,
            "download_queue_count": s_queue.get("totalRecords", 0),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.SONARR_URL, "error": str(exc)}


async def _probe_lidarr() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        artists_res = await lidarr_service.get_artists(limit=500)
        l_queue = await lidarr_service.get_queue(page=1, page_size=1)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        artists_list = artists_res.get("artists", []) if isinstance(artists_res, dict) else artists_res
        total_artists = (
            artists_res.get("total_in_library", len(artists_list))
            if isinstance(artists_res, dict)
            else len(artists_list)
        )
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.LIDARR_URL,
            "artists_count": total_artists,
            "download_queue_count": l_queue.get("totalRecords", 0),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.LIDARR_URL, "error": str(exc)}


async def _probe_prowlarr() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        indexers = await prowlarr_service.get_indexers()
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        enabled_count = sum(1 for idx in indexers if idx.get("enable"))
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.PROWLARR_URL,
            "indexers_count": enabled_count,
            "total_indexers": len(indexers),
            "enabled_indexers": enabled_count,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.PROWLARR_URL, "error": str(exc)}


async def _probe_bazarr() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        wanted_m = await bazarr_service.get_wanted_movies(page=1, limit=1)
        wanted_ep = await bazarr_service.get_wanted_episodes(page=1, limit=1)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.BAZARR_URL,
            "missing_movie_subtitles": wanted_m.get("total", 0),
            "missing_episode_subtitles": wanted_ep.get("total", 0),
            "missing_subtitles_episodes": wanted_ep.get("total", 0),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.BAZARR_URL, "error": str(exc)}


async def _probe_jellyfin() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        sys_info = await jellyfin_service.get_system_info()
        sessions = await jellyfin_service.get_sessions()
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        playing_sessions = [s for s in sessions if s.get("nowPlaying") is not None]
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.JELLYFIN_URL,
            "server_name": sys_info.get("serverName"),
            "version": sys_info.get("version"),
            "total_sessions": len(sessions),
            "currently_playing_count": len(playing_sessions),
            "now_playing": [
                {
                    "user": s.get("userName"),
                    "title": (s.get("nowPlaying") or {}).get("name"),
                    "client": s.get("client"),
                }
                for s in playing_sessions
            ],
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.JELLYFIN_URL, "error": str(exc)}


async def _probe_jellyseerr() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        pending_reqs = await jellyseerr_service.get_requests(filter_status="pending", take=1)
        all_reqs = await jellyseerr_service.get_requests(filter_status="all", take=1)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.JELLYSEERR_URL,
            "pending_requests": pending_reqs.get("total", 0),
            "pending_requests_count": pending_reqs.get("total", 0),
            "total_requests": all_reqs.get("total", 0),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.JELLYSEERR_URL, "error": str(exc)}


async def _probe_qbittorrent() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        transfer = await qbittorrent_service.get_transfer_info()
        torrents = await qbittorrent_service.get_torrents(limit=100)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        downloading = sum(1 for t in torrents if "dl" in str(t.get("state")).lower())
        seeding = sum(1 for t in torrents if "up" in str(t.get("state")).lower())
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.QBITTORRENT_URL,
            "download_speed": transfer.get("dl_speed"),
            "upload_speed": transfer.get("up_speed"),
            "download_speed_human": transfer.get("dl_speed"),
            "upload_speed_human": transfer.get("up_speed"),
            "active_torrents": len(torrents),
            "total_torrents": len(torrents),
            "downloading_count": downloading,
            "seeding_count": seeding,
            "free_disk_space": transfer.get("free_space_on_disk"),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.QBITTORRENT_URL, "error": str(exc)}


async def _probe_trilium() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        app_info = await trilium_service.get_app_info()
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.TRILIUM_URL,
            "app_version": app_info.get("appVersion"),
            "appVersion": app_info.get("appVersion"),
            "syncVersion": app_info.get("syncVersion"),
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.TRILIUM_URL, "error": str(exc)}


async def _probe_rclone() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        rc_stat = await rclone_service.get_status()
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        vfs = rc_stat.get("vfs_cache", {})
        cloud_disk = rc_stat.get("cloud_storage_disk_space", {})
        trans = rc_stat.get("core_transfers", {})
        return {
            "status": "online",
            "latency_ms": latency_ms,
            "url": settings.RCLONE_RC_URL,
            "cloud_storage_used": f"{cloud_disk.get('used')} / {cloud_disk.get('total')} ({cloud_disk.get('usage_percent')}%)",
            "cloud_storage_free": cloud_disk.get("free"),
            "cloud_storage": cloud_disk,
            "vfs_cache_used": vfs.get("bytes_used"),
            "vfs_cached_files": vfs.get("files_in_cache"),
            "uploads_queued": vfs.get("uploads_queued"),
            "transfer_errors": trans.get("errors"),
            "vfs_cache": {
                "used_human": vfs.get("bytes_used"),
                "files_cached": vfs.get("files_in_cache"),
                "uploads_in_progress": vfs.get("uploads_in_progress"),
                "uploads_queued": vfs.get("uploads_queued"),
            },
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {"status": "offline_or_error", "latency_ms": latency_ms, "url": settings.RCLONE_RC_URL, "error": str(exc)}


def register_overview_tools(server) -> None:
    """Registers the unified server hardware metrics and system overview tool."""

    @server.tool()
    async def system_overview(include_services: bool = True) -> str:
        """Retrieves comprehensive real-time server hardware metrics and full homelab services status.

        Includes:
        - Detailed Server Hardware: CPU model, cores, usage %, load average (1m/5m/15m), per-core MHz;
          Thermal sensors (CPU Package, Motherboard, PCH, Wi-Fi); RAM & Swap usage;
          Intel UHD Graphics 620 iGPU frequencies & NVIDIA GeForce MX250 dGPU runtime power state;
          Local root SSD disk space; Network RX/TX speeds; Uptime, AC/Battery power state, and Docker stats.
        - Live status & statistics for all 10 Homelab services (when include_services=True):
          Radarr, Sonarr, Lidarr, Prowlarr, Bazarr, Jellyfin, Jellyseerr, qBittorrent,
          TriliumNext, and Rclone Google Drive Mount & VFS Cache.
        """
        logger.info(f"Executing unified system_overview (include_services={include_services})")
        overview: dict[str, Any] = {}

        if include_services:
            (
                hw_res,
                radarr_res,
                sonarr_res,
                lidarr_res,
                prowlarr_res,
                bazarr_res,
                jellyfin_res,
                jellyseerr_res,
                qb_res,
                trilium_res,
                rclone_res,
            ) = await asyncio.gather(
                system_monitor_service.get_full_system_metrics(),
                _probe_radarr(),
                _probe_sonarr(),
                _probe_lidarr(),
                _probe_prowlarr(),
                _probe_bazarr(),
                _probe_jellyfin(),
                _probe_jellyseerr(),
                _probe_qbittorrent(),
                _probe_trilium(),
                _probe_rclone(),
                return_exceptions=True,
            )
        else:
            hw_res = await system_monitor_service.get_full_system_metrics()
            radarr_res = sonarr_res = lidarr_res = prowlarr_res = bazarr_res = None
            jellyfin_res = jellyseerr_res = qb_res = trilium_res = rclone_res = None

        if isinstance(hw_res, Exception):
            overview["server_hardware_error"] = str(hw_res)
            overview["server_hardware"] = {}
        else:
            overview["server_hardware"] = hw_res

        if include_services:
            overview["radarr"] = radarr_res if isinstance(radarr_res, dict) else {"status": "offline_or_error", "error": str(radarr_res)}
            overview["sonarr"] = sonarr_res if isinstance(sonarr_res, dict) else {"status": "offline_or_error", "error": str(sonarr_res)}
            overview["lidarr"] = lidarr_res if isinstance(lidarr_res, dict) else {"status": "offline_or_error", "error": str(lidarr_res)}
            overview["prowlarr"] = prowlarr_res if isinstance(prowlarr_res, dict) else {"status": "offline_or_error", "error": str(prowlarr_res)}
            overview["bazarr"] = bazarr_res if isinstance(bazarr_res, dict) else {"status": "offline_or_error", "error": str(bazarr_res)}
            overview["jellyfin"] = jellyfin_res if isinstance(jellyfin_res, dict) else {"status": "offline_or_error", "error": str(jellyfin_res)}
            overview["jellyseerr"] = jellyseerr_res if isinstance(jellyseerr_res, dict) else {"status": "offline_or_error", "error": str(jellyseerr_res)}
            overview["qbittorrent"] = qb_res if isinstance(qb_res, dict) else {"status": "offline_or_error", "error": str(qb_res)}
            overview["triliumnext"] = trilium_res if isinstance(trilium_res, dict) else {"status": "offline_or_error", "error": str(trilium_res)}
            overview["rclone_gdrive"] = rclone_res if isinstance(rclone_res, dict) else {"status": "offline_or_error", "error": str(rclone_res)}

        return to_pretty_json(overview)

    @server.tool()
    async def media_stack_overview(include_services: bool = True) -> str:
        """Alias for system_overview for backwards compatibility."""
        return await system_overview(include_services=include_services)

    logger.debug("Registered unified 'system_overview' (and 'media_stack_overview' alias) tool.")

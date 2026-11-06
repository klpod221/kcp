import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import require_authenticated_user
from app.db.models import User
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

router = APIRouter(prefix="/api/admin", tags=["System Monitor & Homelab Services"])


class TorrentActionRequest(BaseModel):
    hashes: list[str]
    action: str
    delete_files: bool = False


class RcloneRefreshRequest(BaseModel):
    dir_path: Optional[str] = None
    recursive: bool = True


@router.get("/transfers")
async def get_live_transfers(
    current_user: User = Depends(require_authenticated_user),
):
    """Returns real-time Disk R/W speed, Network DL/UL speed, active qBittorrent torrents, and Rclone transfers."""
    return await system_monitor_service.get_live_transfers()


@router.post("/transfers/torrent-action")
async def execute_torrent_action(
    payload: TorrentActionRequest,
    current_user: User = Depends(require_authenticated_user),
):
    """Pauses, resumes, rechecks, or deletes torrents in qBittorrent."""
    try:
        return await qbittorrent_service.manage_torrent(
            hashes=payload.hashes,
            action=payload.action,
            delete_files=payload.delete_files,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/transfers/rclone-refresh")
async def refresh_rclone_vfs(
    payload: RcloneRefreshRequest,
    current_user: User = Depends(require_authenticated_user),
):
    """Triggers a VFS directory cache refresh on the Rclone Google Drive mount."""
    try:
        return await rclone_service.refresh_directory_cache(
            dir_path=payload.dir_path,
            recursive=payload.recursive,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/services/details")
async def get_homelab_services_details(
    current_user: User = Depends(require_authenticated_user),
):
    """Aggregates operational queues, active sessions, and pending requests across all Homelab services."""
    async def safe_call(coro, fallback):
        try:
            return await coro
        except Exception as exc:
            return {"error": str(exc), **fallback} if isinstance(fallback, dict) else fallback

    (
        jf_sessions,
        js_requests,
        radarr_q,
        sonarr_q,
        lidarr_q,
        prowlarr_idx,
        bazarr_m,
        bazarr_ep,
        trilium_info,
    ) = await asyncio.gather(
        safe_call(jellyfin_service.get_sessions(), []),
        safe_call(jellyseerr_service.get_requests(filter_status="all", take=10), {"results": [], "total": 0}),
        safe_call(radarr_service.get_queue(page=1, page_size=15), {"records": [], "totalRecords": 0}),
        safe_call(sonarr_service.get_queue(page=1, page_size=15), {"records": [], "totalRecords": 0}),
        safe_call(lidarr_service.get_queue(page=1, page_size=15), {"records": [], "totalRecords": 0}),
        safe_call(prowlarr_service.get_indexers(), []),
        safe_call(bazarr_service.get_wanted_movies(page=1, limit=10), {"data": [], "total": 0}),
        safe_call(bazarr_service.get_wanted_episodes(page=1, limit=10), {"data": [], "total": 0}),
        safe_call(trilium_service.get_app_info(), {}),
    )

    return {
        "jellyfin": {
            "sessions": jf_sessions if isinstance(jf_sessions, list) else [],
        },
        "jellyseerr": js_requests if isinstance(js_requests, dict) else {"results": [], "total": 0},
        "queues": {
            "radarr": radarr_q if isinstance(radarr_q, dict) else {"records": [], "totalRecords": 0},
            "sonarr": sonarr_q if isinstance(sonarr_q, dict) else {"records": [], "totalRecords": 0},
            "lidarr": lidarr_q if isinstance(lidarr_q, dict) else {"records": [], "totalRecords": 0},
        },
        "prowlarr": {
            "indexers": prowlarr_idx if isinstance(prowlarr_idx, list) else [],
        },
        "bazarr": {
            "wanted_movies": bazarr_m if isinstance(bazarr_m, dict) else {"data": [], "total": 0},
            "wanted_episodes": bazarr_ep if isinstance(bazarr_ep, dict) else {"data": [], "total": 0},
        },
        "trilium": trilium_info if isinstance(trilium_info, dict) else {},
    }


@router.post("/services/jellyseerr/{request_id}/{action}")
async def handle_jellyseerr_request(
    request_id: int,
    action: str,
    current_user: User = Depends(require_authenticated_user),
):
    """Approves or declines a media request in Jellyseerr."""
    if action not in {"approve", "decline"}:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'decline'")
    try:
        return await jellyseerr_service.manage_request(request_id=request_id, action=action)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import require_authenticated_user
from app.db.models import User
from app.services.docker_service import docker_service

router = APIRouter(prefix="/api/admin/docker", tags=["Docker Container Management"])


@router.get("/containers")
async def list_docker_containers(
    all_containers: bool = Query(default=True),
    current_user: User = Depends(require_authenticated_user),
):
    """Returns all Docker containers on the host along with summary counts."""
    return await docker_service.list_containers(all_containers=all_containers)


@router.post("/containers/{container_id}/{action}")
async def control_docker_container(
    container_id: str,
    action: str,
    current_user: User = Depends(require_authenticated_user),
):
    """Executes start, stop, or restart on a Docker container."""
    try:
        return await docker_service.container_action(container_id=container_id, action=action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/containers/{container_id}/logs")
async def get_docker_container_logs(
    container_id: str,
    tail: int = Query(default=200, ge=10, le=1000),
    current_user: User = Depends(require_authenticated_user),
):
    """Fetches recent stdout/stderr logs for a Docker container."""
    try:
        return await docker_service.get_container_logs(container_id=container_id, tail=tail)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


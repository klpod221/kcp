from app.core.logging import logger
from app.services.base import to_pretty_json
from app.services.docker_service import docker_service


def register_docker_tools(server) -> None:
    """Registers Docker container management tools into the MCP server."""

    @server.tool()
    async def docker_list_containers(all_containers: bool = True) -> str:
        """Lists all Docker containers on the host server, including status, uptime, ports, and compose service."""
        logger.info("Executing docker_list_containers tool")
        data = await docker_service.list_containers(all_containers=all_containers)
        return to_pretty_json(data)

    @server.tool()
    async def docker_get_container_logs(container_id: str, tail: int = 150) -> str:
        """Fetches recent stdout/stderr logs from a specific Docker container by name or ID."""
        logger.info(f"Executing docker_get_container_logs for '{container_id}' (tail={tail})")
        try:
            data = await docker_service.get_container_logs(container_id=container_id, tail=tail)
            return to_pretty_json(data)
        except Exception as exc:
            return to_pretty_json({"status": "error", "container": container_id, "error": str(exc)})

    @server.tool()
    async def docker_restart_container(container_id: str) -> str:
        """Restarts a Docker container by name or ID."""
        logger.info(f"Executing docker_restart_container for '{container_id}'")
        try:
            data = await docker_service.container_action(container_id=container_id, action="restart")
            return to_pretty_json(data)
        except Exception as exc:
            return to_pretty_json({"status": "error", "container": container_id, "error": str(exc)})

    @server.tool()
    async def docker_start_container(container_id: str) -> str:
        """Starts a stopped Docker container by name or ID."""
        logger.info(f"Executing docker_start_container for '{container_id}'")
        try:
            data = await docker_service.container_action(container_id=container_id, action="start")
            return to_pretty_json(data)
        except Exception as exc:
            return to_pretty_json({"status": "error", "container": container_id, "error": str(exc)})

    @server.tool()
    async def docker_stop_container(container_id: str) -> str:
        """Stops a running Docker container by name or ID."""
        logger.info(f"Executing docker_stop_container for '{container_id}'")
        try:
            data = await docker_service.container_action(container_id=container_id, action="stop")
            return to_pretty_json(data)
        except Exception as exc:
            return to_pretty_json({"status": "error", "container": container_id, "error": str(exc)})

    logger.debug("Registered Docker container tools.")


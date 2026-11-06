import os
from typing import Any

import httpx

from app.core.logging import logger


class DockerService:
    """Interacts with the host Docker Engine API via Unix Domain Socket (/var/run/docker.sock)."""

    def __init__(self, socket_path: str = "/var/run/docker.sock") -> None:
        self.socket_path = socket_path
        self.base_url = "http://docker"

    def is_available(self) -> bool:
        return os.path.exists(self.socket_path)

    def _get_client(self, timeout: float = 15.0) -> httpx.AsyncClient:
        transport = httpx.AsyncHTTPTransport(uds=self.socket_path)
        return httpx.AsyncClient(transport=transport, base_url=self.base_url, timeout=timeout)

    @staticmethod
    def _format_ports(ports_raw: list[dict[str, Any]]) -> list[str]:
        seen: list[str] = []
        for p in ports_raw or []:
            priv = p.get("PrivatePort")
            pub = p.get("PublicPort")
            ptype = p.get("Type", "tcp")
            ip = p.get("IP", "")
            if ip == "::":
                continue
            if pub:
                entry = f"{pub}:{priv}/{ptype}"
            elif priv:
                entry = f"{priv}/{ptype}"
            else:
                continue
            if entry not in seen:
                seen.append(entry)
        return seen

    @staticmethod
    def _decode_docker_logs(raw_bytes: bytes) -> str:
        """Decodes Docker multiplexed stream (8-byte header per frame) or raw TTY output."""
        if not raw_bytes:
            return ""
        lines: list[str] = []
        idx = 0
        length = len(raw_bytes)
        is_multiplexed = length >= 8 and raw_bytes[0] in (0, 1, 2) and raw_bytes[1:4] == b"\x00\x00\x00"
        if is_multiplexed:
            while idx + 8 <= length:
                frame_size = int.from_bytes(raw_bytes[idx + 4 : idx + 8], byteorder="big")
                idx += 8
                if frame_size <= 0:
                    continue
                chunk = raw_bytes[idx : idx + frame_size]
                idx += frame_size
                lines.append(chunk.decode("utf-8", errors="replace"))
            return "".join(lines)
        return raw_bytes.decode("utf-8", errors="replace")

    async def list_containers(self, all_containers: bool = True) -> dict[str, Any]:
        """Lists all Docker containers on the host with status and summary counts."""
        if not self.is_available():
            return {
                "available": False,
                "error": f"Docker socket not found at {self.socket_path}",
                "summary": {"total": 0, "running": 0, "stopped": 0, "healthy": 0},
                "containers": [],
            }

        try:
            async with self._get_client() as client:
                resp = await client.get("/containers/json", params={"all": "true" if all_containers else "false"})
                resp.raise_for_status()
                raw_list = resp.json()
        except Exception as exc:
            logger.error(f"Docker list_containers error: {exc}")
            return {
                "available": False,
                "error": str(exc),
                "summary": {"total": 0, "running": 0, "stopped": 0, "healthy": 0},
                "containers": [],
            }

        containers: list[dict[str, Any]] = []
        running_count = 0
        stopped_count = 0
        healthy_count = 0

        for item in raw_list:
            names = item.get("Names") or []
            clean_name = names[0].lstrip("/") if names else item.get("Id", "")[:12]
            state = (item.get("State") or "unknown").lower()
            status_text = item.get("Status") or ""
            labels = item.get("Labels") or {}

            if state == "running":
                running_count += 1
            else:
                stopped_count += 1

            health = "none"
            if "(healthy)" in status_text.lower():
                health = "healthy"
                healthy_count += 1
            elif "(unhealthy)" in status_text.lower():
                health = "unhealthy"
            elif "health: starting" in status_text.lower():
                health = "starting"

            containers.append(
                {
                    "id": item.get("Id", ""),
                    "short_id": (item.get("Id") or "")[:12],
                    "name": clean_name,
                    "image": item.get("Image", ""),
                    "state": state,
                    "status": status_text,
                    "health": health,
                    "created": item.get("Created"),
                    "ports": self._format_ports(item.get("Ports") or []),
                    "compose_project": labels.get("com.docker.compose.project", ""),
                    "compose_service": labels.get("com.docker.compose.service", ""),
                    "is_protected": clean_name in {"kcp", "klpod221_mcp", "cloudflared", "postgres"},
                }
            )

        containers.sort(key=lambda c: (0 if c["state"] == "running" else 1, c["name"]))

        return {
            "available": True,
            "summary": {
                "total": len(containers),
                "running": running_count,
                "stopped": stopped_count,
                "healthy": healthy_count,
            },
            "containers": containers,
        }

    async def container_action(self, container_id: str, action: str) -> dict[str, Any]:
        """Performs start, stop, or restart on a Docker container."""
        action_clean = action.lower().strip()
        if action_clean not in {"start", "stop", "restart"}:
            raise ValueError(f"Unsupported container action: {action}")

        if not self.is_available():
            raise RuntimeError(f"Docker socket not available at {self.socket_path}")

        async with self._get_client(timeout=30.0) as client:
            resp = await client.post(f"/containers/{container_id}/{action_clean}")
            if resp.status_code not in (200, 204, 304):
                detail = resp.text.strip() or f"HTTP {resp.status_code}"
                raise RuntimeError(f"Docker {action_clean} failed for {container_id}: {detail}")

        return {
            "status": "ok",
            "container": container_id,
            "action": action_clean,
            "message": f"Container '{container_id}' {action_clean} executed successfully.",
        }

    async def get_container_logs(self, container_id: str, tail: int = 200) -> dict[str, Any]:
        """Fetches recent stdout/stderr logs for a Docker container."""
        if not self.is_available():
            raise RuntimeError(f"Docker socket not available at {self.socket_path}")

        safe_tail = max(10, min(int(tail), 1000))
        async with self._get_client(timeout=15.0) as client:
            resp = await client.get(
                f"/containers/{container_id}/logs",
                params={
                    "stdout": "1",
                    "stderr": "1",
                    "tail": str(safe_tail),
                    "timestamps": "1",
                },
            )
            if resp.status_code != 200:
                detail = resp.text.strip() or f"HTTP {resp.status_code}"
                raise RuntimeError(f"Failed to fetch logs for {container_id}: {detail}")

            decoded = self._decode_docker_logs(resp.content)
            lines = [line for line in decoded.splitlines() if line.strip()]
            return {
                "container": container_id,
                "tail": safe_tail,
                "line_count": len(lines),
                "logs": "\n".join(lines),
            }


docker_service = DockerService()


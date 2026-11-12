import json
from typing import Any, Optional

try:
    import httpx
except ImportError:
    import httpx2 as httpx

from app.config import settings
from app.core.logging import logger


def format_bytes(num_bytes: Optional[int | float]) -> str:
    """Formats a byte count into a human-readable string."""
    if num_bytes is None:
        return "0 B"
    val = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(val) < 1024.0:
            return f"{val:.2f} {unit}"
        val /= 1024.0
    return f"{val:.2f} EB"


def format_seconds(seconds: Optional[int | float]) -> str:
    """Formats seconds into a human-readable duration."""
    if seconds is None or seconds < 0:
        return "unknown"
    sec = int(seconds)
    if sec == 8640000 or sec >= 31536000:
        return "infinity"
    days, rem = divmod(sec, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    return " ".join(parts)


def to_pretty_json(data: Any) -> str:
    """Serializes Python objects to compact, readable UTF-8 JSON for LLM consumption."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


class BaseServiceClient:
    """Base asynchronous HTTP client for interacting with home-lab services."""

    def __init__(
        self,
        service_name: str,
        base_url: str,
        default_headers: Optional[dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.timeout = timeout or settings.HTTP_TIMEOUT_SECONDS

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[dict[str, str]] = None,
        cookies: Optional[dict[str, str]] = None,
        raw_response: bool = False,
    ) -> Any:
        """Performs an asynchronous HTTP request and returns parsed JSON or text."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        merged_headers = {**self.default_headers, **(headers or {})}

        cleaned_params = None
        if params:
            cleaned_params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    params=cleaned_params,
                    json=json_data,
                    data=data,
                    headers=merged_headers,
                    cookies=cookies,
                )
                if raw_response:
                    return response

                response.raise_for_status()

                if not response.content:
                    return {"status": "success", "http_status": response.status_code}

                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type or response.text.strip().startswith(("{", "[")):
                    try:
                        return response.json()
                    except Exception:
                        return response.text
                return response.text

        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text[:600] if exc.response else str(exc)
            logger.warning(
                f"[{self.service_name}] HTTP {exc.response.status_code} on {method} {url}: {error_body}"
            )
            error_detail = error_body
            try:
                err_json = json.loads(error_body)
                if isinstance(err_json, dict) and "message" in err_json:
                    error_detail = err_json["message"]
            except Exception:
                pass
            raise RuntimeError(
                f"{self.service_name} returned HTTP {exc.response.status_code}: {error_detail}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error(f"[{self.service_name}] Connection error on {method} {url}: {exc}")
            raise RuntimeError(
                f"Could not connect to {self.service_name} at {self.base_url}: {exc}"
            ) from exc


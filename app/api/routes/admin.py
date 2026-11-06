import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_current_user_from_session, require_authenticated_user
from app.core.logging import logger
from app.core.security import (
    create_session_cookie,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import ApiToken, OAuthClient, RefreshToken, SystemSetting, User
from app.db.session import get_db
from app.mcp import mcp_server
from app.services.base import httpx

router = APIRouter(prefix="/api/admin", tags=["Admin Portal & AI Workspace"])


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateTokenRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    expires_in_days: Optional[int] = Field(default=None, description="Null for never-expiring token")
    scopes: str = Field(default="mcp:read mcp:tools")


class CreateOAuthClientRequest(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=128)
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uris: List[str] = Field(default_factory=list)
    allowed_scopes: str = Field(default="mcp:read mcp:tools")


class UpdateOAuthClientRequest(BaseModel):
    client_name: Optional[str] = None
    redirect_uris: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ToolCallRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)


class AIConfigPayload(BaseModel):
    base_url: str = Field(default="http://host.docker.internal:11434/v1")
    api_key: str = Field(default="")
    model: str = Field(default="qwen2.5:14b")
    system_prompt: str = Field(
        default=(
            "You are the Homelab & Server AI Assistant for klpod221 Kontrol Panel (KCP). "
            "You have full access to 78 MCP tools to monitor server hardware and Docker containers, "
            "manage media (Radarr, Sonarr, Lidarr, Prowlarr, Bazarr, Jellyfin, Jellyseerr), "
            "torrents (qBittorrent), knowledge base notes (TriliumNext), and Google Drive (Rclone). "
            "Always respond concisely and accurately based on live tool data."
        )
    )
    enable_tools: bool = Field(default=True)
    max_tool_rounds: int = Field(default=5, ge=1, le=10)


class ChatMessageItem(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessageItem]
    tool_categories: Optional[List[str]] = None


def _categorize_tool(tool_name: str) -> str:
    prefixes = [
        ("docker_", "Docker Containers"),
        ("radarr_", "Radarr"),
        ("sonarr_", "Sonarr"),
        ("lidarr_", "Lidarr"),
        ("prowlarr_", "Prowlarr"),
        ("bazarr_", "Bazarr"),
        ("jellyfin_", "Jellyfin"),
        ("jellyseerr_", "Jellyseerr"),
        ("qbittorrent_", "qBittorrent"),
        ("trilium_", "TriliumNext"),
        ("rclone_", "Rclone GDrive"),
        ("server_", "Server & System"),
        ("media_stack_", "Server & System"),
        ("system_", "Server & System"),
        ("hello_", "Server & System"),
    ]
    for prefix, label in prefixes:
        if tool_name.startswith(prefix):
            return label
    return "Other"


async def _execute_mcp_tool_internal(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        call_res = await mcp_server.call_tool(tool_name, arguments or {})
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        texts = []
        for item in getattr(call_res, "content", []) or []:
            text_val = getattr(item, "text", None)
            if text_val is not None:
                texts.append(text_val)
        raw_text = "\n".join(texts).strip()
        parsed_result: Any = raw_text
        if raw_text:
            try:
                parsed_result = json.loads(raw_text)
            except Exception:
                parsed_result = raw_text
        is_err = bool(getattr(call_res, "is_error", False))
        return {
            "status": "error" if is_err else "ok",
            "tool": tool_name,
            "duration_ms": duration_ms,
            "result": parsed_result,
            "raw_text": raw_text,
        }
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        logger.error(f"Error calling tool '{tool_name}': {exc}")
        return {
            "status": "error",
            "tool": tool_name,
            "duration_ms": duration_ms,
            "result": {"error": str(exc)},
            "raw_text": json.dumps({"error": str(exc)}, ensure_ascii=False),
        }


@router.get("/me")
async def admin_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Checks current authentication session for the SPA."""
    user = await get_current_user_from_session(request, db)
    if not user:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "server": {
            "name": settings.MCP_SERVER_NAME,
            "version": settings.APP_VERSION,
            "base_url": settings.BASE_URL,
            "mcp_endpoint": f"{settings.BASE_URL}/mcp",
        },
    }


@router.post("/login")
async def admin_login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticates user credentials for the SPA and sets the session cookie."""
    result = await db.execute(
        select(User).where(User.username == payload.username, User.is_active == True)
    )
    user = result.scalars().first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    cookie_token = create_session_cookie(user.id)
    response.set_cookie(
        key="mcp_session",
        value=cookie_token,
        max_age=86400 * 7,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
        },
    }


@router.post("/logout")
async def admin_logout(response: Response):
    """Logs out the current user by deleting the session cookie."""
    response.delete_cookie(key="mcp_session")
    return {"status": "ok"}


@router.get("/overview")
async def admin_overview(
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns live server hardware metrics, 10-service health overview, and auth statistics."""
    overview_exec = await _execute_mcp_tool_internal("system_overview", {})
    stack_data = overview_exec.get("result") if isinstance(overview_exec.get("result"), dict) else {}

    tokens_count_res = await db.execute(
        select(func.count(ApiToken.id)).where(
            ApiToken.user_id == current_user.id, ApiToken.revoked == False
        )
    )
    active_tokens_count = tokens_count_res.scalar() or 0

    clients_count_res = await db.execute(
        select(func.count(OAuthClient.id)).where(OAuthClient.is_active == True)
    )
    active_clients_count = clients_count_res.scalar() or 0

    now = datetime.now(timezone.utc)
    sessions_count_res = await db.execute(
        select(func.count(RefreshToken.id)).where(
            RefreshToken.revoked == False, RefreshToken.expires_at > now
        )
    )
    active_sessions_count = sessions_count_res.scalar() or 0

    mcp_tools = await mcp_server.list_tools()

    return {
        "server_info": {
            "name": settings.MCP_SERVER_NAME,
            "version": settings.APP_VERSION,
            "base_url": settings.BASE_URL,
            "mcp_endpoint": f"{settings.BASE_URL}/mcp",
            "sse_endpoint": f"{settings.BASE_URL}/sse",
            "total_tools": len(mcp_tools),
            "active_api_tokens": active_tokens_count,
            "active_oauth_clients": active_clients_count,
            "active_oauth_sessions": active_sessions_count,
        },
        "stack": stack_data,
    }


@router.get("/tokens")
async def list_api_tokens(
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all Personal Access Tokens belonging to the user."""
    result = await db.execute(
        select(ApiToken)
        .where(ApiToken.user_id == current_user.id)
        .order_by(ApiToken.created_at.desc())
    )
    tokens = result.scalars().all()
    now = datetime.now(timezone.utc)
    items = []
    for t in tokens:
        exp = t.expires_at
        if exp and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        is_expired = bool(exp and exp < now)
        items.append(
            {
                "id": t.id,
                "name": t.name,
                "token_prefix": t.token_prefix,
                "scopes": t.scopes,
                "revoked": t.revoked,
                "is_expired": is_expired,
                "expires_at": t.expires_at.isoformat() if t.expires_at else None,
                "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
        )
    return {"tokens": items}


@router.post("/tokens")
async def create_api_token(
    payload: CreateTokenRequest,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates a new Static API Token (klpod_pat_...) and returns the raw secret once."""
    raw_secret = f"klpod_pat_{generate_secure_token(32)}"
    token_prefix = f"{raw_secret[:16]}...{raw_secret[-4:]}"
    token_h = hash_token(raw_secret)

    now = datetime.now(timezone.utc)
    expires_at = None
    if payload.expires_in_days and payload.expires_in_days > 0:
        expires_at = now + timedelta(days=payload.expires_in_days)

    record = ApiToken(
        name=payload.name.strip(),
        token_prefix=token_prefix,
        token_hash=token_h,
        user_id=current_user.id,
        scopes=payload.scopes.strip() or "mcp:read mcp:tools",
        expires_at=expires_at,
        revoked=False,
        created_at=now,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(f"Created Personal Access Token '{record.name}' (id={record.id}) for user='{current_user.username}'")

    return {
        "token": raw_secret,
        "record": {
            "id": record.id,
            "name": record.name,
            "token_prefix": record.token_prefix,
            "scopes": record.scopes,
            "revoked": record.revoked,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        },
    }


@router.delete("/tokens/{token_id}")
async def revoke_api_token(
    token_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes or revokes a Personal Access Token."""
    result = await db.execute(
        select(ApiToken).where(ApiToken.id == token_id, ApiToken.user_id == current_user.id)
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    await db.delete(record)
    await db.commit()
    logger.info(f"Deleted Personal Access Token id={token_id} ('{record.name}')")
    return {"status": "deleted", "id": token_id}


@router.get("/clients")
async def list_oauth_clients(
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all OAuth 2.0 Clients and active RefreshToken sessions."""
    result = await db.execute(select(OAuthClient).order_by(OAuthClient.created_at.desc()))
    clients = result.scalars().all()

    now = datetime.now(timezone.utc)
    sessions_res = await db.execute(
        select(RefreshToken, User.username, OAuthClient.client_name)
        .outerjoin(User, RefreshToken.user_id == User.id)
        .outerjoin(OAuthClient, RefreshToken.client_id == OAuthClient.client_id)
        .where(RefreshToken.revoked == False, RefreshToken.expires_at > now)
        .order_by(RefreshToken.created_at.desc())
    )
    raw_sessions = sessions_res.all()

    session_counts: Dict[str, int] = {}
    for row in raw_sessions:
        s = row[0]
        session_counts[s.client_id] = session_counts.get(s.client_id, 0) + 1

    return {
        "clients": [
            {
                "id": c.id,
                "client_id": c.client_id,
                "client_name": c.client_name,
                "redirect_uris": c.redirect_uris,
                "allowed_scopes": c.allowed_scopes,
                "is_active": c.is_active,
                "active_sessions": session_counts.get(c.client_id, 0),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in clients
        ],
        "active_sessions": [
            {
                "id": s.id,
                "client_id": s.client_id,
                "client_name": c_name or s.client_id,
                "username": u_name or "Unknown",
                "family_id": s.family_id[:10] + "...",
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            }
            for (s, u_name, c_name) in raw_sessions[:50]
        ],
    }


@router.post("/clients")
async def create_oauth_client(
    payload: CreateOAuthClientRequest,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new OAuth 2.0 Client application."""
    client_id = (payload.client_id or "").strip() or f"client_{generate_secure_token(8)}"
    raw_secret = (payload.client_secret or "").strip() or generate_secure_token(24)

    existing = await db.execute(select(OAuthClient).where(OAuthClient.client_id == client_id))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Client ID '{client_id}' đã tồn tại.",
        )

    client = OAuthClient(
        client_id=client_id,
        client_secret_hash=hash_password(raw_secret),
        client_name=payload.client_name.strip(),
        redirect_uris_json=json.dumps([u.strip() for u in payload.redirect_uris if u.strip()]),
        allowed_scopes=payload.allowed_scopes.strip() or "mcp:read mcp:tools",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    return {
        "client_secret": raw_secret,
        "client": {
            "id": client.id,
            "client_id": client.client_id,
            "client_name": client.client_name,
            "redirect_uris": client.redirect_uris,
            "allowed_scopes": client.allowed_scopes,
            "is_active": client.is_active,
            "created_at": client.created_at.isoformat() if client.created_at else None,
        },
    }


@router.put("/clients/{client_db_id}")
async def update_oauth_client(
    client_db_id: int,
    payload: UpdateOAuthClientRequest,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates an OAuth 2.0 Client's name, redirect URIs, or active status."""
    result = await db.execute(select(OAuthClient).where(OAuthClient.id == client_db_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth Client not found")

    if payload.client_name is not None:
        client.client_name = payload.client_name.strip()
    if payload.redirect_uris is not None:
        client.redirect_uris = [u.strip() for u in payload.redirect_uris if u.strip()]
    if payload.is_active is not None:
        client.is_active = payload.is_active

    await db.commit()
    return {"status": "updated", "id": client.id}


@router.delete("/clients/{client_db_id}")
async def delete_oauth_client(
    client_db_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes an OAuth 2.0 Client and revokes its sessions."""
    result = await db.execute(select(OAuthClient).where(OAuthClient.id == client_db_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OAuth Client not found")

    await db.execute(delete(RefreshToken).where(RefreshToken.client_id == client.client_id))
    await db.delete(client)
    await db.commit()
    return {"status": "deleted", "id": client_db_id}


@router.delete("/sessions/{session_id}")
async def revoke_oauth_session(
    session_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Revokes an active OAuth 2.0 Refresh Token session."""
    result = await db.execute(select(RefreshToken).where(RefreshToken.id == session_id))
    token_rec = result.scalars().first()
    if not token_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    token_rec.revoked = True
    await db.commit()
    return {"status": "revoked", "id": session_id}


@router.get("/tools")
async def list_mcp_tools(
    current_user: User = Depends(require_authenticated_user),
):
    """Returns all 74 registered MCP tools with schemas and service categorization."""
    mcp_tools = await mcp_server.list_tools()
    items = []
    categories_map: Dict[str, int] = {}

    for t in mcp_tools:
        schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {}
        cat = _categorize_tool(t.name)
        categories_map[cat] = categories_map.get(cat, 0) + 1
        items.append(
            {
                "name": t.name,
                "category": cat,
                "description": (t.description or "").strip(),
                "input_schema": schema,
            }
        )

    return {
        "total": len(items),
        "categories": [{"name": k, "count": v} for k, v in categories_map.items()],
        "tools": items,
    }


@router.post("/tools/{tool_name}/call")
async def execute_mcp_tool(
    tool_name: str,
    payload: ToolCallRequest,
    current_user: User = Depends(require_authenticated_user),
):
    """Executes an MCP tool directly from the Admin Playground UI."""
    return await _execute_mcp_tool_internal(tool_name, payload.arguments)


async def _get_ai_config_dict(db: AsyncSession) -> Dict[str, Any]:
    default_cfg = AIConfigPayload().model_dump()
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "ai_config"))
    rec = result.scalars().first()
    if not rec:
        return default_cfg
    try:
        stored = json.loads(rec.value_json)
        default_cfg.update(stored)
    except Exception:
        pass
    return default_cfg


@router.get("/ai-config")
async def get_ai_config(
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the AI Server configuration for Direct AI Chat."""
    cfg = await _get_ai_config_dict(db)
    masked_key = ""
    raw_key = cfg.get("api_key") or ""
    if raw_key:
        masked_key = f"{raw_key[:6]}...{raw_key[-4:]}" if len(raw_key) > 12 else "••••••••"
    return {
        **cfg,
        "has_api_key": bool(raw_key),
        "api_key_masked": masked_key,
    }


@router.put("/ai-config")
async def update_ai_config(
    payload: AIConfigPayload,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Saves the AI Server configuration (Base URL, Model, API Key, System Prompt)."""
    existing_cfg = await _get_ai_config_dict(db)
    new_data = payload.model_dump()
    if new_data.get("api_key") == "KEEP_EXISTING":
        new_data["api_key"] = existing_cfg.get("api_key", "")

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "ai_config"))
    rec = result.scalars().first()
    now = datetime.now(timezone.utc)
    if not rec:
        rec = SystemSetting(
            key="ai_config",
            value_json=json.dumps(new_data, ensure_ascii=False),
            updated_at=now,
        )
        db.add(rec)
    else:
        rec.value_json = json.dumps(new_data, ensure_ascii=False)
        rec.updated_at = now
    await db.commit()
    return {"status": "saved"}


@router.post("/ai-config/test")
async def test_ai_server_connection(
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Tests connectivity and lists available models from the configured AI Server."""
    cfg = await _get_ai_config_dict(db)
    base_url = (cfg.get("base_url") or "").rstrip("/")
    if not base_url:
        raise HTTPException(status_code=400, detail="Chưa cấu hình AI Server Base URL.")

    headers: Dict[str, str] = {"Accept": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(f"{base_url}/models", headers=headers)
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            if resp.status_code >= 400:
                return {
                    "status": "error",
                    "http_status": resp.status_code,
                    "latency_ms": latency_ms,
                    "error": resp.text[:300],
                }
            data = resp.json()
            models = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]
            return {
                "status": "online",
                "latency_ms": latency_ms,
                "models": models[:50],
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "status": "offline",
            "latency_ms": latency_ms,
            "error": str(exc),
        }


@router.post("/chat")
async def chat_with_homelab_ai(
    payload: ChatCompletionRequest,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Executes an AI Chat turn with automatic MCP tool calling against the configured AI Server."""
    cfg = await _get_ai_config_dict(db)
    base_url = (cfg.get("base_url") or "").rstrip("/")
    model = (cfg.get("model") or "").strip()
    if not base_url or not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng cấu hình AI Server Base URL và Model trước khi chat.",
        )

    mcp_tools = await mcp_server.list_tools()
    openai_tools = []
    if cfg.get("enable_tools", True):
        for t in mcp_tools:
            cat = _categorize_tool(t.name)
            if payload.tool_categories and cat not in payload.tool_categories:
                continue
            schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {
                "type": "object",
                "properties": {},
            }
            openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": (t.description or "")[:500],
                        "parameters": schema,
                    },
                }
            )

    messages: List[Dict[str, Any]] = []
    sys_prompt = (cfg.get("system_prompt") or "").strip()
    if sys_prompt:
        messages.append({"role": "system", "content": sys_prompt})

    for m in payload.messages:
        messages.append({"role": m.role, "content": m.content})

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"

    tool_executions: List[Dict[str, Any]] = []
    max_rounds = int(cfg.get("max_tool_rounds") or 5)

    try:
        async with httpx.AsyncClient(timeout=90.0, verify=False) as client:
            for _ in range(max_rounds):
                req_body: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                }
                if openai_tools:
                    req_body["tools"] = openai_tools
                    req_body["tool_choice"] = "auto"

                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json=req_body,
                )
                if resp.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"AI Server trả về HTTP {resp.status_code}: {resp.text[:400]}",
                    )

                data = resp.json()
                choices = data.get("choices") or []
                if not choices:
                    break

                assistant_msg = choices[0].get("message") or {}
                tool_calls = assistant_msg.get("tool_calls") or []

                if not tool_calls:
                    return {
                        "reply": assistant_msg.get("content") or "",
                        "model": data.get("model") or model,
                        "tool_executions": tool_executions,
                    }

                messages.append(assistant_msg)

                for tc in tool_calls:
                    fn_obj = tc.get("function") or {}
                    t_name = fn_obj.get("name") or ""
                    raw_args = fn_obj.get("arguments") or "{}"
                    try:
                        parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    except Exception:
                        parsed_args = {}

                    exec_res = await _execute_mcp_tool_internal(t_name, parsed_args)
                    tool_executions.append(
                        {
                            "id": tc.get("id") or f"call_{len(tool_executions)}",
                            "tool": t_name,
                            "arguments": parsed_args,
                            "status": exec_res["status"],
                            "duration_ms": exec_res["duration_ms"],
                            "result": exec_res["result"],
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.get("id") or "",
                            "name": t_name,
                            "content": exec_res["raw_text"][:12000] or "{}",
                        }
                    )

            final_resp = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages},
            )
            final_data = final_resp.json()
            final_msg = (final_data.get("choices") or [{}])[0].get("message") or {}
            return {
                "reply": final_msg.get("content") or "",
                "model": final_data.get("model") or model,
                "tool_executions": tool_executions,
            }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to connect to AI Server ({base_url}): {exc}",
        )


class UpdateProfileRequest(BaseModel):
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    is_admin: bool = False


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


@router.put("/profile")
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates profile of currently authenticated user."""
    if payload.email is not None:
        current_user.email = payload.email.strip() or None

    if payload.new_password:
        if not payload.current_password or not verify_password(payload.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )
        if len(payload.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters.",
            )
        current_user.hashed_password = hash_password(payload.new_password)

    await db.commit()
    await db.refresh(current_user)
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "is_admin": current_user.is_admin,
        },
    }


@router.get("/users")
async def list_users(
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists all registered system users (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    res = await db.execute(select(User).order_by(User.id))
    users = res.scalars().all()
    return {
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "is_admin": u.is_admin,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@router.post("/users")
async def create_user(
    payload: CreateUserRequest,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Creates a new user account (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    exist_res = await db.execute(select(User).where(User.username == payload.username.strip()))
    if exist_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken.",
        )

    new_user = User(
        username=payload.username.strip(),
        hashed_password=hash_password(payload.password),
        email=payload.email.strip() if payload.email else None,
        is_admin=payload.is_admin,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "success": True,
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "is_admin": new_user.is_admin,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
        },
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Updates user information, active state, or resets password (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    res = await db.execute(select(User).where(User.id == user_id))
    target_user = res.scalars().first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if payload.email is not None:
        target_user.email = payload.email.strip() or None
    if payload.is_admin is not None:
        target_user.is_admin = payload.is_admin
    if payload.is_active is not None:
        if target_user.id == current_user.id and not payload.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account.",
            )
        target_user.is_active = payload.is_active
    if payload.password:
        if len(payload.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters.",
            )
        target_user.hashed_password = hash_password(payload.password)

    await db.commit()
    await db.refresh(target_user)
    return {
        "success": True,
        "user": {
            "id": target_user.id,
            "username": target_user.username,
            "email": target_user.email,
            "is_admin": target_user.is_admin,
            "is_active": target_user.is_active,
        },
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Deletes a user account (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account.",
        )

    res = await db.execute(select(User).where(User.id == user_id))
    target_user = res.scalars().first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    await db.delete(target_user)
    await db.commit()
    return {"success": True, "message": f"User {target_user.username} deleted."}



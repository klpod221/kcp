from typing import Tuple

from fastapi import APIRouter, Depends, Request, Response

from app.config import settings
from app.core.dependencies import get_current_user_from_token
from app.core.logging import logger
from app.db.models import User
from app.mcp import lowlevel_server, session_manager, sse_transport

router = APIRouter(tags=["MCP Protocol"])


class RawAsgiResponse(Response):
    """Delegates response handling directly to ASGI handler."""

    async def __call__(self, scope, receive, send) -> None:
        pass


@router.head("/mcp", summary="MCP Endpoint Probe (HEAD)")
@router.head("/mcp/", include_in_schema=False)
async def handle_mcp_head(
    request: Request,
    auth_data: Tuple[User, dict] = Depends(get_current_user_from_token),
):
    return Response(
        status_code=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.options("/mcp", include_in_schema=False)
@router.options("/mcp/", include_in_schema=False)
@router.options("/mcp/message", include_in_schema=False)
@router.options("/mcp/message/", include_in_schema=False)
async def handle_mcp_options():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD, DELETE",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, mcp-session-id, mcp-protocol-version",
            "Access-Control-Expose-Headers": "mcp-session-id, mcp-protocol-version",
        },
    )


@router.api_route("/mcp", methods=["GET", "POST", "DELETE"], summary="Streamable HTTP & SSE MCP Endpoint")
@router.api_route("/mcp/", methods=["GET", "POST", "DELETE"], include_in_schema=False)
async def handle_mcp(
    request: Request,
    auth_data: Tuple[User, dict] = Depends(get_current_user_from_token),
):
    user, payload = auth_data
    request.scope["user"] = user

    client_id = payload.get("client_id", "unknown")
    logger.info(
        f"Incoming MCP {request.method} request from user='{user.username}' (client='{client_id}') - path: {request.url.path}, query: {request.url.query}, headers: {dict(request.headers)}"
    )

    if request.method == "GET" and "mcp-session-id" not in request.headers:
        logger.info(f"Establishing SSE stream for user='{user.username}' (client='{client_id}')")
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await lowlevel_server.run(
                read_stream,
                write_stream,
                lowlevel_server.create_initialization_options(),
            )
        return RawAsgiResponse()

    if request.method == "POST" and "session_id" in request.query_params:
        await sse_transport.handle_post_message(request.scope, request.receive, request._send)
        return RawAsgiResponse()

    await session_manager.asgi_app(request.scope, request.receive, request._send)
    return RawAsgiResponse()


@router.post("/mcp/message", summary="MCP Message Handling Endpoint (/mcp/message)")
@router.post("/mcp/message/", include_in_schema=False)
async def handle_post_message(
    request: Request,
    auth_data: Tuple[User, dict] = Depends(get_current_user_from_token),
):
    user, payload = auth_data
    request.scope["user"] = user

    if "session_id" in request.query_params:
        await sse_transport.handle_post_message(request.scope, request.receive, request._send)
    else:
        await session_manager.asgi_app(request.scope, request.receive, request._send)
    return RawAsgiResponse()

import asyncio
import functools
import json
from typing import Any
from uuid import uuid4

import anyio
from anyio.abc import TaskStatus
from mcp_types import INTERNAL_ERROR
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from app.config import settings
from app.core.logging import logger

try:
    from mcp.server.mcpserver import MCPServer as Server
except ImportError:
    from mcp.server.fastmcp import FastMCP as Server

from mcp.server.auth.middleware.bearer_auth import (
    AuthenticatedUser,
    AuthorizationContext,
    authorization_context,
)
from mcp.server.connection import Connection
from mcp.server.runner import serve_connection
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http import (
    MCP_SESSION_ID_HEADER,
    SESSION_ID_PATTERN,
    StreamableHTTPServerTransport,
)
from mcp.server.streamable_http_manager import (
    StreamableHTTPSessionManager,
    _error_response,
)
from mcp.shared.jsonrpc_dispatcher import JSONRPCDispatcher
from mcp.shared.transport_context import TransportContext


class ResilientStreamableHTTPSessionManager(StreamableHTTPSessionManager):
    """Streamable HTTP session manager that gracefully recovers stale or expired session IDs.

    Cloud AI clients such as Google Gemini distribute tool calls across worker nodes
    that may cache an mcp-session-id across container restarts or idle periods.
    Instead of returning HTTP 404 Session not found (which causes Gemini to abort with
    'MCP session with server terminated'), this manager transparently re-admits the
    requested session ID in an initialized state so tool calls succeed seamlessly.
    """

    async def _resurrect_session(
        self,
        requestor: AuthorizationContext | None,
        requested_session_id: str,
    ) -> StreamableHTTPServerTransport | None:
        if self.max_sessions is not None and len(self._server_instances) >= self.max_sessions:
            return None

        clean_session_id = (
            requested_session_id
            if SESSION_ID_PATTERN.match(requested_session_id)
            else uuid4().hex
        )

        http_transport = StreamableHTTPServerTransport(
            mcp_session_id=clean_session_id,
            is_json_response_enabled=self.json_response,
            event_store=self.event_store,
            security_settings=self.security_settings,
            retry_interval=self.retry_interval,
            idle_timeout=self.session_idle_timeout,
        )
        session_id = http_transport.mcp_session_id
        assert session_id is not None

        async def run_resurrected_server(
            *, task_status: TaskStatus[None] = anyio.TASK_STATUS_IGNORED
        ) -> None:
            async with http_transport.connect() as streams:
                read_stream, write_stream = streams
                dispatcher: JSONRPCDispatcher[TransportContext] = JSONRPCDispatcher(
                    read_stream,
                    write_stream,
                    raise_handler_exceptions=False,
                    inline_methods=frozenset({"initialize"}),
                )
                connection = Connection.for_loop(dispatcher, session_id=session_id)
                connection.initialized.set()
                task_status.started()
                try:
                    idle_scope = http_transport.idle_scope
                    if idle_scope is None:
                        idle_scope = anyio.CancelScope()
                    with idle_scope:
                        await serve_connection(
                            self.app,
                            dispatcher,
                            connection=connection,
                            lifespan_state=self._lifespan_state,
                        )
                    if idle_scope.cancelled_caught:
                        logger.info(f"Session {session_id} idle timeout")
                except Exception:
                    logger.exception(f"Resurrected session {session_id} crashed")
                finally:
                    await self._discard_session(session_id, http_transport)

        assert self._task_group is not None
        await self._task_group.start(run_resurrected_server)

        if requestor is not None:
            self._session_owners[session_id] = requestor
        self._server_instances[session_id] = http_transport
        logger.info(f"Auto-recovered MCP session with ID: {session_id[:64]}")
        return http_transport

    async def _handle_stateful_request(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        request_mcp_session_id = request.headers.get(MCP_SESSION_ID_HEADER)

        user = scope.get("user")
        requestor = authorization_context(user) if isinstance(user, AuthenticatedUser) else None

        if request.method == "DELETE":
            if request_mcp_session_id and request_mcp_session_id in self._server_instances:
                transport = self._server_instances[request_mcp_session_id]
                await self._discard_session(request_mcp_session_id, transport)
            await Response(status_code=200)(scope, receive, send)
            return

        if request_mcp_session_id is not None and request_mcp_session_id in self._server_instances:
            transport = self._server_instances[request_mcp_session_id]
            logger.debug("Session already exists, handling request directly")
            await transport.handle_request(scope, receive, send)
            if transport.is_terminated:
                await self._discard_session(request_mcp_session_id, transport)
            return

        if request_mcp_session_id is None:
            async with self._session_creation_lock:
                http_transport = self._admit_session(requestor)
            if http_transport is None:
                logger.warning("Refusing to open a new session: %d sessions are already open", self.max_sessions)
                await _error_response("Too many open sessions", 503, INTERNAL_ERROR)(scope, receive, send)
                return
            await self._serve_opening_request(http_transport, scope, receive, send)
            return

        async with self._session_creation_lock:
            http_transport = self._server_instances.get(request_mcp_session_id)
            if http_transport is None:
                http_transport = await self._resurrect_session(requestor, request_mcp_session_id)

        if http_transport is None:
            logger.warning("Refusing to recover session: %d sessions are already open", self.max_sessions)
            await _error_response("Too many open sessions", 503, INTERNAL_ERROR)(scope, receive, send)
            return

        await http_transport.handle_request(scope, receive, send)
        if http_transport.is_terminated:
            await self._discard_session(request_mcp_session_id, http_transport)


mcp_server = Server(
    name=settings.MCP_SERVER_NAME,
    title=settings.MCP_SERVER_NAME,
    description=settings.MCP_SERVER_DESCRIPTION,
    instructions=settings.MCP_SERVER_INSTRUCTIONS,
    version=settings.APP_VERSION,
    website_url=settings.BASE_URL,
)

# Intercept and wrap tool functions so that uncaught exceptions return informative JSON
# instead of causing an unhandled stream crash and CONNECTION_CLOSED on AI clients.
_orig_add_tool = mcp_server.add_tool


def _safe_add_tool(fn, name=None, *args, **kwargs):
    tool_name = name or getattr(fn, "__name__", "unnamed_tool")

    if asyncio.iscoroutinefunction(fn):
        @functools.wraps(fn)
        async def _safe_async_fn(*fn_args, **fn_kwargs):
            try:
                return await fn(*fn_args, **fn_kwargs)
            except Exception as exc:
                logger.error(f"Error executing MCP tool '{tool_name}': {exc}", exc_info=True)
                return json.dumps({
                    "status": "error",
                    "tool": tool_name,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }, ensure_ascii=False)
        target_fn = _safe_async_fn
    else:
        @functools.wraps(fn)
        def _safe_sync_fn(*fn_args, **fn_kwargs):
            try:
                return fn(*fn_args, **fn_kwargs)
            except Exception as exc:
                logger.error(f"Error executing MCP tool '{tool_name}': {exc}", exc_info=True)
                return json.dumps({
                    "status": "error",
                    "tool": tool_name,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }, ensure_ascii=False)
        target_fn = _safe_sync_fn

    return _orig_add_tool(target_fn, name=name, *args, **kwargs)


mcp_server.add_tool = _safe_add_tool

lowlevel_server = getattr(
    mcp_server,
    "_lowlevel_server",
    getattr(mcp_server, "_mcp_server", None),
)
if lowlevel_server is None:
    raise RuntimeError("Could not find underlying MCP server engine.")

sse_transport = SseServerTransport(settings.MCP_MESSAGE_ENDPOINT)
session_manager = ResilientStreamableHTTPSessionManager(
    app=lowlevel_server,
    session_idle_timeout=None,
)

logger.info(
    f"Initialized MCP Server '{settings.MCP_SERVER_NAME}' with SSE & Resilient Streamable HTTP transports"
)

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import decode_access_token, hash_token, verify_session_cookie
from app.db.models import ApiToken, User
from app.db.session import AsyncSessionLocal, get_db

bearer_scheme = HTTPBearer(auto_error=False)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@asynccontextmanager
async def _resolve_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            try:
                await session.close()
            except Exception:
                pass


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Tuple[User, dict]:
    """Authenticates API requests via Bearer JWT Access Token or Static Personal Access Token."""
    if not credentials or not credentials.credentials:
        resource_metadata_url = f"{settings.BASE_URL}/.well-known/oauth-protected-resource"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer access token",
            headers={
                "WWW-Authenticate": f'Bearer realm="{settings.MCP_SERVER_NAME}", resource_metadata="{resource_metadata_url}"',
                "Access-Control-Expose-Headers": "WWW-Authenticate, mcp-session-id, mcp-protocol-version",
            },
        )

    raw_token = credentials.credentials.strip()

    async with _resolve_db_session() as session:
        if raw_token.startswith("klpod_pat_"):
            t_hash = hash_token(raw_token)
            result = await session.execute(select(ApiToken).where(ApiToken.token_hash == t_hash))
            pat = result.scalars().first()
            now = datetime.now(timezone.utc)

            if not pat or pat.revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked personal access token",
                    headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
                )

            if pat.expires_at and _ensure_utc(pat.expires_at) < now:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Personal access token has expired",
                    headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
                )

            user_result = await session.execute(select(User).where(User.id == pat.user_id))
            user = user_result.scalars().first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account does not exist or has been disabled",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            pat.last_used_at = now
            await session.commit()

            payload = {
                "sub": str(user.id),
                "username": user.username,
                "client_id": f"pat:{pat.name}",
                "scopes": pat.scopes.split(),
                "token_type": "pat",
            }
            return user, payload

        payload = decode_access_token(raw_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id = int(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account does not exist or has been disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user, payload


async def get_current_user_from_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Retrieves authenticated user from signed HTTP-only session cookie."""
    cookie_value = request.cookies.get("mcp_session")
    if not cookie_value:
        return None

    user_id = verify_session_cookie(cookie_value)
    if not user_id:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user or not user.is_active:
        return None

    return user


async def require_authenticated_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Requires an authenticated user via session cookie or Bearer token."""
    session_user = await get_current_user_from_session(request, db)
    if session_user:
        return session_user

    if credentials and credentials.credentials:
        token_user, _ = await get_current_user_from_token(credentials)
        return token_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )



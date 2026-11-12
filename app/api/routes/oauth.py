import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_current_user_from_session
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    create_session_cookie,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
    verify_pkce,
)
from app.db.models import AuthorizationCode, OAuthClient, RefreshToken, User
from app.db.session import get_db

router = APIRouter(tags=["OAuth 2.0"])
templates = Jinja2Templates(directory="app/templates")


def ensure_utc(dt: datetime) -> datetime:
    """Ensures datetime object is timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/authorize", summary="OAuth 2.0 Authorization Endpoint", response_class=HTMLResponse)
async def oauth_authorize(
    request: Request,
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    state: Optional[str] = None,
    scope: str = "mcp:read mcp:tools",
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_session),
):
    """Handles OAuth 2.0 authorization requests with client whitelist check & consent."""
    logger.info(f"Incoming /authorize request for client_id='{client_id}', redirect_uri='{redirect_uri}'")

    result = await db.execute(
        select(OAuthClient).where(OAuthClient.client_id == client_id, OAuthClient.is_active == True)
    )
    client = result.scalars().first()
    if not client:
        is_trusted_redirect = any(
            redirect_uri.startswith(trusted)
            for trusted in [
                "https://oauth-redirect.googleusercontent.com",
            ]
        )
        if is_trusted_redirect:
            logger.info(f"Auto-registering trusted client_id='{client_id}' for Google Connected Apps")
            client = OAuthClient(
                client_id=client_id,
                client_secret_hash=hash_password(generate_secure_token(32)),
                client_name=f"Google Gemini ({client_id})",
                redirect_uris_json=json.dumps([redirect_uri]),
                allowed_scopes="mcp:read mcp:tools",
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(client)
            await db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown or inactive client_id")

    allowed_uris = client.redirect_uris
    if redirect_uri not in allowed_uris:
        is_trusted_redirect = any(
            redirect_uri.startswith(trusted)
            for trusted in [
                "https://oauth-redirect.googleusercontent.com",
                "https://gemini.google.com",
                "https://oauth.google.com",
                "https://developers.google.com",
                "https://oauth.pstmn.io",
            ]
        )

        if is_trusted_redirect:
            logger.info(f"Dynamically trusting redirect_uri '{redirect_uri}' for client '{client_id}'")
            new_allowed = list(set(allowed_uris + [redirect_uri]))
            client.redirect_uris = new_allowed
            await db.commit()
        else:
            logger.warning(f"Unauthorized redirect_uri '{redirect_uri}' for client '{client_id}'. Allowed: {allowed_uris}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Redirect URI '{redirect_uri}' is not registered for this client",
            )

    if response_type != "code":
        return RedirectResponse(
            url=f"{redirect_uri}?error=unsupported_response_type&state={state or ''}",
            status_code=status.HTTP_302_FOUND,
        )

    return_to = str(request.url)
    if not current_user:
        login_url = f"/login?return_to={urllib.parse.quote_plus(return_to)}"
        return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)

    consent_params = {
        "client_id": client_id,
        "client_name": client.client_name,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "return_to": return_to,
    }
    if state:
        consent_params["state"] = state
    if code_challenge:
        consent_params["code_challenge"] = code_challenge
    if code_challenge_method:
        consent_params["code_challenge_method"] = code_challenge_method

    consent_url = f"/consent?{urllib.parse.urlencode(consent_params)}"
    return RedirectResponse(url=consent_url, status_code=status.HTTP_302_FOUND)


@router.get("/login")
async def login_page(request: Request, return_to: Optional[str] = "/"):
    from app.api.routes.health import serve_spa
    return await serve_spa(request)


@router.post("/login")
async def login_submit(
    request: Request,
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    return_to: str = Form("/"),
    db: AsyncSession = Depends(get_db),
):
    """Authenticates user credentials and sets signed session cookie (supports Form & JSON)."""
    # Parse JSON if request is application/json
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
            return_to = body.get("return_to", "/")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    result = await db.execute(select(User).where(User.username == username, User.is_active == True))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for username='{username}'")
        if "application/json" in content_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )
        # Form post fallback for standard browser
        login_err_url = f"/login?return_to={urllib.parse.quote_plus(return_to)}&error=Invalid+username+or+password."
        return RedirectResponse(url=login_err_url, status_code=status.HTTP_302_FOUND)

    logger.info(f"User '{username}' logged in successfully.")
    cookie_token = create_session_cookie(user.id)

    if "application/json" in content_type:
        res = JSONResponse({"status": "ok", "return_to": return_to, "user": {"id": user.id, "username": user.username}})
    else:
        res = RedirectResponse(url=return_to, status_code=status.HTTP_302_FOUND)

    res.set_cookie(
        key="mcp_session",
        value=cookie_token,
        max_age=86400 * 7,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
    )
    return res


@router.get("/logout")
async def logout(return_to: str = "/login"):
    response = RedirectResponse(url=return_to, status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="mcp_session")
    return response


@router.get("/consent")
async def consent_page(request: Request):
    from app.api.routes.health import serve_spa
    return await serve_spa(request)


@router.post("/consent")
async def consent_submit(
    request: Request,
    action: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    scope: str = Form("mcp:read mcp:tools"),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user_from_session),
    db: AsyncSession = Depends(get_db),
):
    """Processes user decision on Consent Screen and issues Authorization Code."""
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type
    if is_json:
        try:
            body = await request.json()
            action = body.get("action")
            client_id = body.get("client_id")
            redirect_uri = body.get("redirect_uri")
            state = body.get("state")
            scope = body.get("scope", "mcp:read mcp:tools")
            code_challenge = body.get("code_challenge")
            code_challenge_method = body.get("code_challenge_method")
        except Exception:
            pass

    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    if not client_id or not redirect_uri:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing client_id or redirect_uri")

    if action != "allow":
        logger.info(f"User '{current_user.username}' denied authorization for client '{client_id}'")
        target_url = f"{redirect_uri}?error=access_denied"
        if state:
            target_url += f"&state={urllib.parse.quote_plus(state)}"
        if is_json:
            return JSONResponse({"status": "denied", "redirect_url": target_url})
        return RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)

    raw_code = generate_secure_token(32)
    code_h = hash_token(raw_code)

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
    auth_code = AuthorizationCode(
        code_hash=code_h,
        client_id=client_id,
        user_id=current_user.id,
        redirect_uri=redirect_uri,
        scope=scope,
        code_challenge=code_challenge if code_challenge else None,
        code_challenge_method=code_challenge_method if code_challenge_method else None,
        expires_at=expires_at,
        used=False,
    )
    db.add(auth_code)
    await db.commit()

    logger.info(
        f"Issued authorization code for user='{current_user.username}' to client='{client_id}' (state length: {len(state) if state else 0})"
    )

    parsed = urllib.parse.urlparse(redirect_uri)
    params = urllib.parse.parse_qs(parsed.query)
    params["code"] = [raw_code]
    if state is not None:
        params["state"] = [state]

    new_query = urllib.parse.urlencode(params, doseq=True)
    target_url = urllib.parse.urlunparse(parsed._replace(query=new_query))

    logger.info(f"Redirecting consent to target_url='{target_url[:120]}...'")
    if is_json:
        return JSONResponse({"status": "allowed", "redirect_url": target_url})
    return RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)


@router.post("/token", summary="OAuth 2.0 Token Exchange Endpoint")
async def oauth_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Exchanges Authorization Code or Refresh Token for JWT Access Token."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = await request.json()
        except Exception:
            data = {}
    else:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            data = {}

    grant_type = data.get("grant_type")
    client_id = data.get("client_id")
    client_secret = data.get("client_secret")

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        import base64
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            if ":" in decoded:
                c_id, c_secret = decoded.split(":", 1)
                client_id = c_id
                client_secret = c_secret
        except Exception:
            pass

    if not client_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_client", "error_description": "client_id is required"},
        )

    result = await db.execute(
        select(OAuthClient).where(OAuthClient.client_id == client_id, OAuthClient.is_active == True)
    )
    client = result.scalars().first()
    if not client:
        logger.warning(f"Client '{client_id}' not found.")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "invalid_client", "error_description": "Unknown client_id"},
        )

    if client_secret:
        if not verify_password(client_secret, client.client_secret_hash):
            logger.warning(f"Invalid client_secret for client_id='{client_id}'")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "invalid_client", "error_description": "Invalid client_id or client_secret"},
            )
    else:
        if grant_type != "authorization_code":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "invalid_client", "error_description": "Client secret is required for this grant type"},
            )

    now = datetime.now(timezone.utc)

    if grant_type == "authorization_code":
        code = data.get("code")
        redirect_uri = data.get("redirect_uri")
        code_verifier = data.get("code_verifier")

        if not code or not redirect_uri:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_request", "error_description": "Missing code or redirect_uri"},
            )

        code_h = hash_token(code)
        result = await db.execute(
            select(AuthorizationCode).where(AuthorizationCode.code_hash == code_h)
        )
        auth_code = result.scalars().first()

        if not auth_code or auth_code.used:
            logger.warning("Attempted reuse of authorization code or unknown code!")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "Authorization code is invalid or already used"},
            )

        if ensure_utc(auth_code.expires_at) < now:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "Authorization code has expired"},
            )

        if auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "Client ID or redirect URI mismatch"},
            )

        if auth_code.code_challenge:
            if not code_verifier or not verify_pkce(
                code_verifier, auth_code.code_challenge, auth_code.code_challenge_method or "S256"
            ):
                logger.warning("PKCE verification failed.")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "invalid_grant", "error_description": "PKCE verification failed"},
                )
        elif not client_secret:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "invalid_client", "error_description": "Client secret or PKCE verifier is required"},
            )

        auth_code.used = True
        await db.commit()

        user_result = await db.execute(select(User).where(User.id == auth_code.user_id))
        user = user_result.scalars().first()
        if not user or not user.is_active:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "User is inactive or deleted"},
            )

        scopes = auth_code.scope.split()
        access_token = create_access_token(user.id, user.username, client_id, scopes)

        raw_refresh_token = generate_secure_token(48)
        refresh_token_entry = RefreshToken(
            token_hash=hash_token(raw_refresh_token),
            client_id=client_id,
            user_id=user.id,
            family_id=generate_secure_token(16),
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False,
        )
        db.add(refresh_token_entry)
        await db.commit()

        logger.info(f"Granted access token to client='{client_id}' for user='{user.username}'")

        return JSONResponse(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "refresh_token": raw_refresh_token,
                "scope": auth_code.scope,
            }
        )

    elif grant_type == "refresh_token":
        raw_refresh_token = data.get("refresh_token")
        if not raw_refresh_token:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_request", "error_description": "Missing refresh_token"},
            )

        r_hash = hash_token(raw_refresh_token)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == r_hash))
        token_record = result.scalars().first()

        if token_record and token_record.revoked:
            logger.critical(f"Compromise detected! Revoking entire token family '{token_record.family_id}'")
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == token_record.family_id)
                .values(revoked=True)
            )
            await db.commit()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "Refresh token has been revoked"},
            )

        if not token_record or ensure_utc(token_record.expires_at) < now or token_record.client_id != client_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "Invalid or expired refresh token"},
            )

        token_record.revoked = True

        user_result = await db.execute(select(User).where(User.id == token_record.user_id))
        user = user_result.scalars().first()
        if not user or not user.is_active:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "invalid_grant", "error_description": "User is inactive or deleted"},
            )

        scopes = client.allowed_scopes.split()
        new_access_token = create_access_token(user.id, user.username, client_id, scopes)

        new_raw_refresh = generate_secure_token(48)
        new_refresh_record = RefreshToken(
            token_hash=hash_token(new_raw_refresh),
            client_id=client_id,
            user_id=user.id,
            family_id=token_record.family_id,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False,
        )
        db.add(new_refresh_record)
        await db.commit()

        logger.info(f"Rotated refresh token for user='{user.username}'")

        return JSONResponse(
            {
                "access_token": new_access_token,
                "token_type": "Bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "refresh_token": new_raw_refresh,
            }
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "unsupported_grant_type", "error_description": f"Grant type '{grant_type}' is unsupported"},
    )


@router.options("/register", include_in_schema=False)
@router.options("/oauth/register", include_in_schema=False)
async def oauth_register_options():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept",
        },
    )


@router.post("/register", summary="OAuth 2.0 Dynamic Client Registration (RFC 7591)", status_code=status.HTTP_201_CREATED)
@router.post("/oauth/register", include_in_schema=False)
async def oauth_register_client(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """RFC 7591: Dynamic Client Registration Endpoint for Gemini, Claude, and MCP clients."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    client_name = body.get("client_name") or "Dynamic MCP Client"
    redirect_uris = body.get("redirect_uris") or []
    if isinstance(redirect_uris, str):
        redirect_uris = [redirect_uris]

    client_id = f"client_{generate_secure_token(16)}"
    raw_secret = generate_secure_token(32)
    secret_hash = hash_password(raw_secret)

    client = OAuthClient(
        client_id=client_id,
        client_secret_hash=secret_hash,
        client_name=str(client_name)[:128],
        redirect_uris_json=json.dumps(redirect_uris),
        allowed_scopes="mcp:read mcp:tools",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(client)
    await db.commit()

    logger.info(f"Dynamically registered OAuth client '{client_id}' ({client_name}) with redirect_uris={redirect_uris}")

    auth_method = body.get("token_endpoint_auth_method") or "client_secret_post"
    issued_at = int(datetime.now(timezone.utc).timestamp())

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "client_id": client_id,
            "client_secret": raw_secret,
            "client_id_issued_at": issued_at,
            "client_secret_expires_at": 0,
            "client_name": client.client_name,
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": auth_method,
            "scope": "mcp:read mcp:tools",
        },
        headers={
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )

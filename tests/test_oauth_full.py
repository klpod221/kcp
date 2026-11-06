import asyncio
import base64
import hashlib
import os
import pytest
from starlette.testclient import TestClient

# Set testing DB URL to a temporary SQLite file before loading settings
TEST_DB_FILE = "/tmp/test_kcp_shared.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
os.environ["DEBUG"] = "True"

from app import create_app
from app.config import settings
from app.db.session import async_engine, init_db
from app.db.models import Base


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
def client():
    asyncio.run(init_db())
    app = create_app()
    with TestClient(app, follow_redirects=False) as c:
        yield c


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["app_name"] == "klpod221 Kontrol Panel"


def test_client_validation_rejects_unknown_client(client):
    res = client.get(
        "/authorize?client_id=unknown_client&redirect_uri=https://oauth.google.com/callback&response_type=code"
    )
    assert res.status_code == 400
    assert "Unknown or inactive client_id" in res.json()["detail"]


def test_client_validation_rejects_unauthorized_redirect_uri(client):
    res = client.get(
        f"/authorize?client_id={settings.DEFAULT_CLIENT_ID}&redirect_uri=https://malicious.com/callback&response_type=code"
    )
    assert res.status_code == 400
    assert "Redirect URI" in res.json()["detail"]


def test_protected_mcp_rejects_unauthenticated_request(client):
    # Calling /mcp without Bearer token must return 401
    res = client.get("/mcp")
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers


def test_protected_mcp_rejects_tampered_token(client):
    res = client.get("/mcp", headers={"Authorization": "Bearer tampered.fake.jwt"})
    assert res.status_code == 401


def test_full_oauth_flow_and_token_exchange(client):
    auth_url = (
        f"/authorize?client_id={settings.DEFAULT_CLIENT_ID}"
        f"&redirect_uri=https://oauth.google.com/callback"
        f"&response_type=code"
        f"&state=test_state_123"
        f"&scope=mcp:read+mcp:tools"
    )
    res = client.get(auth_url)
    assert res.status_code == 302
    assert "/login?return_to=" in res.headers["location"]

    res = client.post(
        "/login",
        data={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": "WrongPassword!",
            "return_to": auth_url,
        },
    )
    assert res.status_code == 302
    assert "error=" in res.headers["location"]

    res = client.post(
        "/login",
        data={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": settings.DEFAULT_ADMIN_PASSWORD,
            "return_to": auth_url,
        },
    )
    assert res.status_code == 302
    assert "mcp_session" in res.cookies
    session_cookie = res.cookies["mcp_session"]

    res = client.get(auth_url, cookies={"mcp_session": session_cookie})
    assert res.status_code == 302
    assert "/consent?" in res.headers["location"]

    res = client.post(
        "/consent",
        data={
            "action": "deny",
            "client_id": settings.DEFAULT_CLIENT_ID,
            "redirect_uri": "https://oauth.google.com/callback",
            "state": "test_state_123",
            "scope": "mcp:read mcp:tools",
        },
        cookies={"mcp_session": session_cookie},
    )
    assert res.status_code == 302
    assert "error=access_denied" in res.headers["location"]

    res = client.post(
        "/consent",
        data={
            "action": "allow",
            "client_id": settings.DEFAULT_CLIENT_ID,
            "redirect_uri": "https://oauth.google.com/callback",
            "state": "test_state_123",
            "scope": "mcp:read mcp:tools",
        },
        cookies={"mcp_session": session_cookie},
    )
    assert res.status_code == 302
    location = res.headers["location"]
    assert "code=" in location
    assert "state=test_state_123" in location

    import urllib.parse
    parsed = urllib.parse.urlparse(location)
    query_params = urllib.parse.parse_qs(parsed.query)
    auth_code = query_params["code"][0]
    assert len(auth_code) > 20

    token_res = client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "https://oauth.google.com/callback",
            "client_id": settings.DEFAULT_CLIENT_ID,
            "client_secret": settings.DEFAULT_CLIENT_SECRET,
        },
    )
    assert token_res.status_code == 200
    token_data = token_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"
    assert "refresh_token" in token_data
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    replay_res = client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "https://oauth.google.com/callback",
            "client_id": settings.DEFAULT_CLIENT_ID,
            "client_secret": settings.DEFAULT_CLIENT_SECRET,
        },
    )
    assert replay_res.status_code == 400
    assert replay_res.json()["error"] == "invalid_grant"

    headers = {"Authorization": f"Bearer {access_token}"}
    with client.stream("GET", "/mcp", headers=headers) as sse_stream:
        assert sse_stream.status_code == 200

    refresh_res = client.post(
        "/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.DEFAULT_CLIENT_ID,
            "client_secret": settings.DEFAULT_CLIENT_SECRET,
        },
    )
    assert refresh_res.status_code == 200
    new_token_data = refresh_res.json()
    assert "access_token" in new_token_data
    assert "refresh_token" in new_token_data
    new_refresh_token = new_token_data["refresh_token"]
    assert new_refresh_token != refresh_token

    revoked_reuse_res = client.post(
        "/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.DEFAULT_CLIENT_ID,
            "client_secret": settings.DEFAULT_CLIENT_SECRET,
        },
    )
    assert revoked_reuse_res.status_code == 400
    assert revoked_reuse_res.json()["error"] == "invalid_grant"


def test_pkce_authorization_code_flow(client):
    code_verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    verifier_digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(verifier_digest).decode("ascii").rstrip("=")

    login_res = client.post(
        "/login",
        data={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": settings.DEFAULT_ADMIN_PASSWORD,
            "return_to": "/",
        },
    )
    session_cookie = login_res.cookies["mcp_session"]

    res = client.post(
        "/consent",
        data={
            "action": "allow",
            "client_id": settings.DEFAULT_CLIENT_ID,
            "redirect_uri": "https://oauth.google.com/callback",
            "state": "pkce_state",
            "scope": "mcp:read mcp:tools",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        },
        cookies={"mcp_session": session_cookie},
    )
    assert res.status_code == 302
    import urllib.parse
    parsed = urllib.parse.urlparse(res.headers["location"])
    code = urllib.parse.parse_qs(parsed.query)["code"][0]

    fail_res = client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://oauth.google.com/callback",
            "client_id": settings.DEFAULT_CLIENT_ID,
            "client_secret": settings.DEFAULT_CLIENT_SECRET,
            "code_verifier": "wrong_verifier_12345678901234567890",
        },
    )
    assert fail_res.status_code == 400
    assert "PKCE verification failed" in fail_res.json()["error_description"]


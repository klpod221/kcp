import asyncio
import os
import pytest
from starlette.testclient import TestClient

TEST_DB_FILE = "/tmp/test_kcp_shared.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
os.environ["DEBUG"] = "True"

from app import create_app
from app.config import settings
from app.db.session import init_db


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
def client():
    asyncio.run(init_db())
    app = create_app()
    with TestClient(app, follow_redirects=False) as c:
        yield c


def test_admin_login_and_cookie_session(client):
    res = client.get("/api/admin/me")
    assert res.status_code == 200
    assert res.json()["authenticated"] is False

    res = client.post(
        "/api/admin/login",
        json={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": settings.DEFAULT_ADMIN_PASSWORD,
        },
    )
    assert res.status_code == 200
    assert res.json()["authenticated"] is True
    assert "mcp_session" in res.cookies
    session_cookie = res.cookies["mcp_session"]

    res = client.get("/api/admin/me", cookies={"mcp_session": session_cookie})
    assert res.status_code == 200
    data = res.json()
    assert data["authenticated"] is True
    assert data["user"]["username"] == settings.DEFAULT_ADMIN_USERNAME


def test_pat_creation_and_mcp_authentication(client):
    login_res = client.post(
        "/api/admin/login",
        json={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": settings.DEFAULT_ADMIN_PASSWORD,
        },
    )
    session_cookie = login_res.cookies["mcp_session"]

    # Create Personal Access Token
    res = client.post(
        "/api/admin/tokens",
        json={"name": "Test Cursor Token", "expires_in_days": None},
        cookies={"mcp_session": session_cookie},
    )
    assert res.status_code == 200
    token_data = res.json()
    pat_secret = token_data["token"]
    pat_id = token_data["record"]["id"]
    assert pat_secret.startswith("klpod_pat_")

    # Access /mcp with PAT Bearer token
    headers = {"Authorization": f"Bearer {pat_secret}"}
    with client.stream("GET", "/mcp", headers=headers) as sse_stream:
        assert sse_stream.status_code == 200

    # Revoke PAT
    del_res = client.delete(f"/api/admin/tokens/{pat_id}", cookies={"mcp_session": session_cookie})
    assert del_res.status_code == 200

    # Access /mcp with revoked PAT should be rejected
    res = client.get("/mcp", headers=headers)
    assert res.status_code == 401


def test_admin_tools_catalog_and_call(client):
    login_res = client.post(
        "/api/admin/login",
        json={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": settings.DEFAULT_ADMIN_PASSWORD,
        },
    )
    session_cookie = login_res.cookies["mcp_session"]

    res = client.get("/api/admin/tools", cookies={"mcp_session": session_cookie})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 73

    call_res = client.post(
        "/api/admin/tools/hello_world/call",
        json={"arguments": {"name": "Antigravity"}},
        cookies={"mcp_session": session_cookie},
    )
    assert call_res.status_code == 200
    call_data = call_res.json()
    assert call_data["status"] == "ok"
    assert "Antigravity" in call_data["raw_text"]

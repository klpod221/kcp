from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings

router = APIRouter(tags=["OAuth Discovery & Metadata"])


@router.get("/.well-known/oauth-protected-resource")
@router.get("/.well-known/oauth-protected-resource/")
@router.get("/.well-known/oauth-protected-resource/mcp")
@router.get("/.well-known/oauth-protected-resource/mcp/")
async def oauth_protected_resource():
    """RFC 9728: OAuth 2.0 Protected Resource Metadata for MCP."""
    return JSONResponse(
        {
            "resource": f"{settings.BASE_URL}/mcp",
            "authorization_servers": [settings.BASE_URL],
            "scopes_supported": ["mcp:read", "mcp:tools"],
            "bearer_methods_supported": ["header"],
            "resource_name": settings.APP_NAME,
            "resource_description": settings.MCP_SERVER_DESCRIPTION,
            "resource_documentation": f"{settings.BASE_URL}/health",
        }
    )


@router.get("/.well-known/oauth-authorization-server")
@router.get("/.well-known/oauth-authorization-server/")
@router.get("/.well-known/oauth-authorization-server/mcp")
@router.get("/.well-known/oauth-authorization-server/mcp/")
@router.get("/.well-known/openid-configuration")
@router.get("/.well-known/openid-configuration/")
async def oauth_authorization_server_metadata():
    """RFC 8414 & RFC 7591: OAuth 2.0 Authorization Server & Dynamic Client Registration Metadata."""
    return JSONResponse(
        {
            "issuer": settings.BASE_URL,
            "authorization_endpoint": f"{settings.BASE_URL}/authorize",
            "token_endpoint": f"{settings.BASE_URL}/token",
            "registration_endpoint": f"{settings.BASE_URL}/register",
            "scopes_supported": ["mcp:read", "mcp:tools"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"],
            "code_challenge_methods_supported": ["S256"],
        }
    )


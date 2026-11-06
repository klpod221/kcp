import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings
from app.core.logging import logger

# Initialize Argon2 Password Hasher
ph = PasswordHasher()

# Initialize Signed Session Serializer
session_serializer = URLSafeTimedSerializer(
    settings.SESSION_SECRET_KEY, salt="klpod221-oauth-session"
)


def hash_password(password: str) -> str:
    """Hashes a password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hexadecimal hash for storing codes/tokens safely in DB."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically secure random token string."""
    return secrets.token_urlsafe(nbytes)


def verify_pkce(code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
    """Validates PKCE code_verifier against code_challenge according to RFC 7636."""
    if method == "plain":
        return secrets.compare_digest(code_verifier, code_challenge)
    elif method == "S256":
        # S256: BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        clean_target_challenge = code_challenge.rstrip("=")
        return secrets.compare_digest(computed_challenge, clean_target_challenge)
    return False


def create_access_token(
    user_id: int,
    username: str,
    client_id: str,
    scopes: list[str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a signed JWT Access Token with standard claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "username": username,
        "client_id": client_id,
        "scope": " ".join(scopes),
        "iss": settings.BASE_URL,
        "aud": settings.MCP_SERVER_NAME,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16),
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decodes and validates a JWT Access Token.

    Returns payload dict or None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.MCP_SERVER_NAME,
            issuer=settings.BASE_URL,
            options={"require": ["exp", "iss", "sub"]},
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception) as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def create_session_cookie(user_id: int) -> str:
    """Generates a cryptographically signed cookie token storing user_id."""
    return session_serializer.dumps({"user_id": user_id})


def verify_session_cookie(cookie_str: str, max_age: int = 3600) -> Optional[int]:
    """Verifies and extracts user_id from a signed session cookie.

    Returns user_id or None if expired/tampered.
    """
    try:
        data = session_serializer.loads(cookie_str, max_age=max_age)
        return data.get("user_id")
    except (SignatureExpired, BadSignature, Exception):
        return None


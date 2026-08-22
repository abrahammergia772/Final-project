"""Authentication, password hashing, and authorization helpers.

The API uses a compact HMAC-signed access token to avoid adding another
runtime dependency. Passwords use salted PBKDF2; legacy SHA-256 hashes are
still accepted on login so existing seeded demo databases can migrate without
a forced password reset.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import SECRET_KEY


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 310_000
SALT_BYTES = 16
TOKEN_ALGORITHM = "sha256"
VALID_ROLES = frozenset({
    "admin", "manager", "doctor", "nurse", "pharmacist", "laboratory", "reception", "patient",
})

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Return a salted, versioned password hash suitable for database storage."""
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    if len(password) > 128:
        raise ValueError("password is too long")
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${encode(salt)}${encode(derived)}"


def _decode_b64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify PBKDF2 hashes and transparently support legacy SHA-256 hashes."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    if stored_hash.startswith(f"{PASSWORD_ALGORITHM}$"):
        try:
            algorithm, iterations_raw, salt_raw, expected_raw = stored_hash.split("$", 3)
            iterations = int(iterations_raw)
            if algorithm != PASSWORD_ALGORITHM or not (100_000 <= iterations <= 2_000_000):
                return False
            salt = _decode_b64(salt_raw)
            expected = _decode_b64(expected_raw)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError, binascii.Error):
            return False

    # Existing installations documented SHA-256. Keep this only as a migration
    # path; new accounts always receive PBKDF2 hashes.
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy, stored_hash)


def issue_token(user_id: str, role: str, expires_in: int = 8 * 3600, name: str = "") -> str:
    """Issue an expiring HMAC-signed token with minimal claims."""
    if not user_id or role not in VALID_ROLES:
        raise ValueError("invalid token claims")
    if not isinstance(expires_in, int) or not (60 <= expires_in <= 7 * 24 * 3600):
        raise ValueError("invalid token lifetime")
    now = int(time.time())
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + expires_in}
    if name:
        payload["name"] = str(name)[:120]
    raw = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def decode_token(token: str) -> Dict[str, Any]:
    """Validate a token and return its claims, converting malformed input to 401."""
    try:
        if not isinstance(token, str) or len(token) > 4096:
            raise ValueError("invalid token")
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("invalid token format")
        raw, signature = parts
        expected = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("bad signature")
        payload = json.loads(_decode_b64(raw).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("invalid claims")
        subject = payload.get("sub")
        role = payload.get("role")
        exp = payload.get("exp")
        if not subject or role not in VALID_ROLES or not isinstance(exp, (int, float)):
            raise ValueError("invalid claims")
        if int(exp) <= int(time.time()):
            raise ValueError("expired")
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeError,
            binascii.Error, OverflowError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def require_roles(*roles: str):
    allowed = set(roles)

    def dependency(user=Depends(current_user)):
        if user["role"] not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency

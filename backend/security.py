"""Authentication and authorization helpers for the API.

This deliberately uses a small HMAC-signed token so the service has no extra
runtime dependency. Tokens are not persisted; use a full identity provider for
multi-service deployments.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import SECRET_KEY

_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Salted PBKDF2 hash. Stored form: pbkdf2_sha256$rounds$salt$digest."""
    rounds = 200_000
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), rounds).hex()
    return f"pbkdf2_sha256${rounds}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Accept the current hash and the older unsalted SHA-256 demo hashes."""
    if not stored or not password:
        return False
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt, digest = stored.split("$", 3)
            check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds)).hex()
            return hmac.compare_digest(check, digest)
        except (ValueError, TypeError):
            return False
    legacy = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(stored, legacy)


def issue_token(user_id: str, role: str, expires_in: int = 8 * 3600, email: str = "", name: str = "") -> str:
    if SECRET_KEY == "mediq-pro-dev-secret-change-me" and os.getenv("RENDER") == "true":
        raise HTTPException(status_code=500, detail="Server secret is not configured")
    payload = {"sub": str(user_id), "role": role, "exp": int(time.time()) + expires_in}
    if email:
        payload["email"] = email
    if name:
        payload["name"] = name
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def decode_token(token: str) -> Dict[str, str]:
    try:
        raw, sig = token.split(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")
        if not payload.get("sub") or not payload.get("role"):
            raise ValueError("invalid claims")
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    return decode_token(credentials.credentials)


def require_roles(*roles):
    def dependency(user=Depends(current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

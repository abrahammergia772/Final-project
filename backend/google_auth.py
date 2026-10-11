# =============================================================================
# Wolaita Sodo Hospital — google_auth.py
# Verifies a Google ID token. Never logs the token.
# =============================================================================
import json
import os
import urllib.parse
import urllib.request


class GoogleAuthError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def client_id() -> str:
    for name in ("GOOGLE_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_ID"):
        value = os.getenv(name, "").strip().strip('"').strip("'")
        if value:
            return value
    return ""


def parse_identity(payload: dict, expected_client_id: str) -> dict:
    """Return email, name, and sub. Reject anything that is not this app's user."""
    if not isinstance(payload, dict) or payload.get("error"):
        raise GoogleAuthError("invalid")
    audience = str(payload.get("aud") or "")
    if not expected_client_id or audience != expected_client_id:
        raise GoogleAuthError("audience")
    issuer = str(payload.get("iss") or "")
    if issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleAuthError("issuer")
    verified = payload.get("email_verified")
    if verified not in (True, "true", "True"):
        raise GoogleAuthError("unverified")
    email = str(payload.get("email") or "").strip().lower()
    if "@" not in email or " " in email:
        raise GoogleAuthError("email")
    subject = str(payload.get("sub") or "").strip()
    if not subject:
        raise GoogleAuthError("subject")
    name = str(payload.get("name") or payload.get("given_name") or "").strip()
    if not name:
        name = email.split("@", 1)[0]
    return {"email": email, "name": name[:120], "sub": subject}


def fetch_identity(credential: str, expected_client_id: str) -> dict:
    token = (credential or "").strip()
    if not token or len(token) > 4000:
        raise GoogleAuthError("invalid")
    body = urllib.parse.urlencode({"id_token": token}).encode()
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/tokeninfo",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode() or "{}")
    except Exception as exc:  # noqa: BLE001
        raise GoogleAuthError("invalid") from exc
    return parse_identity(payload, expected_client_id)

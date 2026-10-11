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


def _email(payload: dict) -> str:
    email = str(payload.get("email") or "").strip().lower()
    if "@" not in email or " " in email:
        raise GoogleAuthError("email")
    return email


def _verified(payload: dict) -> bool:
    verified = payload.get("email_verified", payload.get("verified_email"))
    return verified in (True, "true", "True")


def _name(payload: dict, email: str) -> str:
    name = str(payload.get("name") or payload.get("given_name") or "").strip()
    return (name or email.split("@", 1)[0])[:120]


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
    if not _verified(payload):
        raise GoogleAuthError("unverified")
    email = _email(payload)
    subject = str(payload.get("sub") or "").strip()
    if not subject:
        raise GoogleAuthError("subject")
    return {"email": email, "name": _name(payload, email), "sub": subject}


def parse_access_identity(payload: dict, expected_client_id: str) -> dict:
    """Accept Google's access-token check. The account was chosen in Google's list."""
    if not isinstance(payload, dict) or payload.get("error"):
        raise GoogleAuthError("invalid")
    audiences = {
        str(payload.get("aud") or ""),
        str(payload.get("azp") or ""),
        str(payload.get("audience") or ""),
        str(payload.get("issued_to") or ""),
    }
    if not expected_client_id or expected_client_id not in audiences:
        raise GoogleAuthError("audience")
    if not _verified(payload):
        raise GoogleAuthError("unverified")
    email = _email(payload)
    subject = str(payload.get("sub") or payload.get("user_id") or "").strip()
    if not subject:
        raise GoogleAuthError("subject")
    return {"email": email, "name": _name(payload, email), "sub": subject}


def fetch_identity(credential: str, expected_client_id: str) -> dict:
    token = (credential or "").strip()
    if not token or len(token) > 8000:
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


def fetch_access_identity(access_token: str, expected_client_id: str) -> dict:
    token = (access_token or "").strip()
    if not token or len(token) > 8000 or " " in token:
        raise GoogleAuthError("invalid")
    url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"access_token": token})
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode() or "{}")
    except Exception as exc:  # noqa: BLE001
        raise GoogleAuthError("invalid") from exc
    identity = parse_access_identity(payload, expected_client_id)
    if identity["name"] == identity["email"].split("@", 1)[0]:
        try:
            info_req = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": "Bearer " + token},
                method="GET",
            )
            with urllib.request.urlopen(info_req, timeout=12) as response:
                info = json.loads(response.read().decode() or "{}")
            if isinstance(info, dict) and info.get("name"):
                identity["name"] = str(info.get("name")).strip()[:120]
        except Exception:  # noqa: BLE001
            pass
    return identity

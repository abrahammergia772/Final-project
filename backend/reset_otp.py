# =============================================================================
# Wolaita Sodo Hospital — reset_otp.py
# Short-lived password-reset codes. The code itself is kept in memory and
# only a keyed hash is written to the database. Never return the code.
# =============================================================================
import hashlib
import hmac
import secrets
import time

TTL = 600
_CODES = {}
_HITS = {}


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def remember(email: str, code: str, now: float | None = None) -> None:
    now = time.time() if now is None else now
    _CODES[email] = (code, now + TTL)


def forget(email: str) -> None:
    _CODES.pop(email, None)


def memory_matches(email: str, code: str, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    record = _CODES.get(email)
    if not record or now > record[1] or len(code) != len(record[0]):
        return False
    return secrets.compare_digest(code, record[0])


def seal(code: str, secret: str, exp: int) -> dict:
    mac = hmac.new(secret.encode(), f"{code}:{int(exp)}".encode(), hashlib.sha256).hexdigest()
    return {"h": mac, "exp": int(exp)}


def sealed_matches(code: str, blob, secret: str, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    if not isinstance(blob, dict):
        return False
    try:
        exp = int(blob.get("exp") or 0)
    except (TypeError, ValueError):
        return False
    if now > exp:
        return False
    digest = str(blob.get("h") or "")
    mac = hmac.new(secret.encode(), f"{code}:{exp}".encode(), hashlib.sha256).hexdigest()
    if len(digest) != len(mac):
        return False
    return secrets.compare_digest(digest, mac)


def too_many(email: str, limit: int = 5, window: int = 600, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    hits = [t for t in _HITS.get(email, []) if now - t < window]
    _HITS[email] = hits
    return len(hits) >= limit


def note_request(email: str, now: float | None = None) -> None:
    now = time.time() if now is None else now
    _HITS.setdefault(email, []).append(now)

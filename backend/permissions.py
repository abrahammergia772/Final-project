"""Role permissions saved by the administrator.

The Roles & Permissions page stores one app_settings row, id "permissions".
A role can use a resource only when an administrator has left that permission on.
If no saved row exists yet, the built-in defaults apply.
"""
import json
import logging
import time
from typing import Dict

from fastapi import Depends, HTTPException

from db import get_client
from security import current_user

log = logging.getLogger("mediq.permissions")

# Keep this in step with CONFIG.PERMISSIONS in assets/js/config.js.
DEFAULTS = {
    "admin": {"users": 1, "roles": 1, "announcements": 1, "audit": 1, "settings": 1, "shifts": 1, "documents": 1, "patients": 1, "reports": 1, "wards": 1, "ai": 1, "messages": 1},
    "manager": {"departments": 1, "staff": 1, "reports": 1, "finance": 1, "complaints": 1, "shifts": 1, "documents": 1, "patients": 1, "wards": 1, "ai": 1, "messages": 1, "settings": 1},
    "doctor": {"patients": 1, "bedrequests": 1, "consultation": 1, "prescriptions": 1, "appointments": 1, "referrals": 1, "theatre": 1, "imaging": 1, "shifts": 1, "documents": 1, "videos": 1, "ai": 1, "messages": 1, "settings": 1},
    "nurse": {"beds": 1, "vitals": 1, "observations": 1, "medications": 1, "careplans": 1, "shifts": 1, "documents": 1, "patients": 1, "reports": 1, "messages": 1, "settings": 1},
    "pharmacist": {"prescriptions": 1, "inventory": 1, "suppliers": 1, "shifts": 1, "documents": 1, "patients": 1, "reports": 1, "ai": 1, "messages": 1, "settings": 1},
    "laboratory": {"testrequests": 1, "samples": 1, "bloodbank": 1, "results": 1, "shifts": 1, "documents": 1, "patients": 1, "reports": 1, "ai": 1, "messages": 1, "settings": 1},
    "reception": {"registration": 1, "admissions": 1, "appointments": 1, "insurance": 1, "queue": 1, "ambulance": 1, "billing": 1, "shifts": 1, "documents": 1, "patients": 1, "reports": 1, "messages": 1, "settings": 1},
    "patient": {"appointments": 1, "records": 1, "bills": 1, "complaints": 1, "healthcard": 1, "videos": 1, "messages": 1, "ai": 1, "settings": 1},
}

# A permission key unlocks these API resources. A resource is blocked only when
# every key that unlocks it has been turned off for that role.
UNLOCKS = {
    "users": ("users",),
    "announcements": ("announcements",),
    "audit": ("audit_logs",),
    "shifts": ("shifts", "roster", "attendance"),
    "documents": ("documents",),
    "records": ("documents",),
    "patients": ("patients",),
    "registration": ("patients",),
    "wards": ("beds",),
    "beds": ("beds",),
    "admissions": ("beds",),
    "bedrequests": ("bed_requests",),
    "messages": ("messages",),
    "departments": ("departments",),
    "staff": ("staff",),
    "finance": ("finance",),
    "complaints": ("complaints",),
    "prescriptions": ("prescriptions",),
    "appointments": ("appointments",),
    "referrals": ("referrals",),
    "theatre": ("theatre_cases",),
    "imaging": ("imaging_studies",),
    "videos": ("videos",),
    "vitals": ("vitals",),
    "observations": ("observations",),
    "medications": ("medications",),
    "careplans": ("care_plans",),
    "inventory": ("inventory",),
    "suppliers": ("suppliers", "purchase_orders"),
    "testrequests": ("lab_requests",),
    "samples": ("samples",),
    "bloodbank": ("blood_units",),
    "results": ("lab_results",),
    "insurance": ("insurance",),
    "queue": ("queue",),
    "ambulance": ("ambulances", "ambulance_missions"),
    "billing": ("cashier_invoices", "bills"),
    "bills": ("bills", "cashier_invoices"),
}

DENIED = "An administrator has not given your role permission for this."
_ROW_ID = "permissions"
_FALLBACK_ID = "__permissions"

_cache: Dict[str, object] = {"at": 0.0, "value": {}}


def _on(value) -> bool:
    return value in (1, True, "1")


def _object(raw):
    guard = 0
    while isinstance(raw, str) and guard < 3:
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None
        guard += 1
    return raw if isinstance(raw, dict) else None


def _extract(row: dict) -> dict:
    if not isinstance(row, dict):
        return {}
    raw = _object(row.get("value"))
    if raw:
        wrapped = raw.get("permissions") if isinstance(raw.get("permissions"), dict) else None
        if wrapped and not any(key in raw for key in ("admin", "doctor", "nurse", "patient")):
            return wrapped
        return raw
    details = _object(row.get("details")) or {}
    inner = details.get("permissions") if isinstance(details.get("permissions"), dict) else None
    return inner or {}


def _read_primary(client) -> dict:
    resp = client.table("app_settings").select("id,value").eq("id", _ROW_ID).limit(1).execute()
    rows = resp.data or []
    return _extract(rows[0]) if rows else {}


def _read_fallback(client) -> dict:
    resp = client.table("announcements").select("id,details").eq("id", _FALLBACK_ID).limit(1).execute()
    rows = resp.data or []
    return _extract(rows[0]) if rows else {}


def load_saved(force: bool = False) -> dict:
    now = time.monotonic()
    if not force and now - float(_cache["at"] or 0) < 5:
        saved = _cache["value"]
        return saved if isinstance(saved, dict) else {}
    value: dict = {}
    client = get_client()
    if client is not None:
        try:
            value = _read_primary(client)
        except Exception as exc:  # noqa: BLE001
            log.warning("permission load failed: %s", type(exc).__name__)
            value = {}
        if not value:
            try:
                value = _read_fallback(client)
            except Exception as exc:  # noqa: BLE001
                log.warning("permission fallback load failed: %s", type(exc).__name__)
    _cache["at"] = now
    _cache["value"] = value
    return value


def normalize_map(role_map: dict) -> dict:
    out = {}
    if not isinstance(role_map, dict):
        return out
    for key, value in role_map.items():
        name = str(key or "").strip()
        if not name or len(name) > 40:
            continue
        out[name] = 1 if value in (1, True, "1") else 0
    return out


def _confirm(client, reader, role: str, expected: dict) -> dict:
    stored = reader(client)
    role_saved = stored.get(role) if isinstance(stored, dict) else None
    if not isinstance(role_saved, dict):
        raise RuntimeError("saved row was not readable")
    for key, value in expected.items():
        if (1 if role_saved.get(key) in (1, True, "1") else 0) != value:
            raise RuntimeError("saved permissions did not match")
    return stored


def _write_primary(client, value: dict) -> None:
    existing = client.table("app_settings").select("id").eq("id", _ROW_ID).limit(1).execute()
    if existing.data:
        client.table("app_settings").update({"value": value}).eq("id", _ROW_ID).execute()
        return
    client.table("app_settings").insert({"id": _ROW_ID, "value": value}).execute()


def _write_fallback(client, value: dict) -> None:
    row = {
        "id": _FALLBACK_ID,
        "title": "System permissions",
        "message": "Do not edit",
        "audience": "system",
        "status": "draft",
        "details": {"permissions": value},
    }
    existing = client.table("announcements").select("id").eq("id", _FALLBACK_ID).limit(1).execute()
    if existing.data:
        client.table("announcements").update({"details": row["details"], "status": "draft"}).eq("id", _FALLBACK_ID).execute()
        return
    client.table("announcements").insert(row).execute()


def save_role_map(role: str, role_map: dict) -> dict:
    """Merge one role's switches into the saved permissions and confirm the write."""
    role = str(role or "").strip().lower()
    if not role or len(role) > 40:
        raise ValueError("role required")
    cleaned = normalize_map(role_map)
    if role == "admin":
        cleaned["roles"] = 1
    client = get_client()
    if client is None:
        raise RuntimeError("Supabase is not configured")
    current = load_saved(force=True)
    if not isinstance(current, dict):
        current = {}
    current = dict(current)
    current[role] = cleaned
    primary_error = None
    try:
        _write_primary(client, current)
        stored = _confirm(client, _read_primary, role, cleaned)
    except Exception as exc:  # noqa: BLE001
        primary_error = exc
        log.warning("app_settings permission save failed: %s", type(exc).__name__)
        try:
            _write_fallback(client, current)
            stored = _confirm(client, _read_fallback, role, cleaned)
        except Exception as fallback_exc:  # noqa: BLE001
            log.warning("permission fallback save failed: %s", type(fallback_exc).__name__)
            raise RuntimeError("Could not save permissions") from primary_error
    _cache["at"] = time.monotonic()
    _cache["value"] = stored
    return stored


def granted(role: str, key: str, saved: dict | None = None) -> bool:
    if role == "admin" and key == "roles":
        return True
    saved = load_saved() if saved is None else saved
    role_saved = saved.get(role) if isinstance(saved, dict) else None
    if isinstance(role_saved, dict) and key in role_saved:
        return _on(role_saved[key])
    return DEFAULTS.get(role, {}).get(key) == 1


def resource_allowed(role: str, resource: str, saved: dict | None = None) -> bool:
    if resource in {"app_settings", "notifications"}:
        return True
    saved = load_saved() if saved is None else saved
    role_saved = saved.get(role) if isinstance(saved, dict) else None
    known = set(DEFAULTS.get(role, {}))
    if isinstance(role_saved, dict):
        known.update(role_saved)
    governors = [key for key in known if resource in UNLOCKS.get(key, ())]
    if not governors:
        return True
    return any(granted(role, key, saved) for key in governors)


def assert_key(user: dict, key: str) -> None:
    if not granted(str(user.get("role") or ""), key):
        raise HTTPException(status_code=403, detail=DENIED)


def assert_resource(user: dict, resource: str) -> None:
    if not resource_allowed(str(user.get("role") or ""), resource):
        raise HTTPException(status_code=403, detail=DENIED)


def require_permission(key: str):
    def dependency(user=Depends(current_user)):
        assert_key(user, key)
        return user
    return dependency

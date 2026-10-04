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

_cache: Dict[str, object] = {"at": 0.0, "value": {}}


def _on(value) -> bool:
    return value in (1, True, "1")


def load_saved(force: bool = False) -> dict:
    now = time.monotonic()
    if not force and now - float(_cache["at"] or 0) < 5:
        saved = _cache["value"]
        return saved if isinstance(saved, dict) else {}
    value: dict = {}
    client = get_client()
    if client is not None:
        try:
            resp = client.table("app_settings").select("id,value").eq("id", "permissions").limit(1).execute()
            rows = resp.data or []
            if rows:
                raw = rows[0].get("value")
                if isinstance(raw, str):
                    raw = json.loads(raw)
                if isinstance(raw, dict):
                    value = raw
        except Exception as exc:  # noqa: BLE001
            log.warning("permission load failed: %s", type(exc).__name__)
            value = {}
    _cache["at"] = now
    _cache["value"] = value
    return value


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

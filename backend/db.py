# =============================================================================
# Wolaita Sodo Hospital — backend/db.py
# Supabase (PostgreSQL) data layer. Every core-data endpoint reads/writes a
# Supabase table. If Supabase is not configured, it uses built-in demo data. A configured
# database never falls back to demo rows, so a schema error stays visible.
# =============================================================================
import logging
from typing import Any, Dict, List, Optional

from config import supabase_configured, SUPABASE_KEY, SUPABASE_SERVICE_KEY, SUPABASE_URL

log = logging.getLogger("mediq.db")

_client = None


def get_client():
    """Lazy Supabase client (anon key; service key preferred when provided)."""
    global _client
    if _client is None and supabase_configured():
        from supabase import create_client
        key = SUPABASE_SERVICE_KEY or SUPABASE_KEY
        _client = create_client(SUPABASE_URL, key)
    return _client


# Records are stored only in Supabase. There is no in-memory demo copy.

# endpoint path -> table name (Supabase) and demo key
TABLES = {
    "users": "users", "patients": "patients", "appointments": "appointments",
    "prescriptions": "prescriptions", "inventory": "inventory",
    "lab_requests": "lab_requests", "lab_results": "lab_results",
    "medications": "medications", "care_plans": "care_plans", "bills": "bills",
    "audit_logs": "audit_logs", "queue": "queue", "announcements": "announcements",
    "departments": "departments", "staff": "staff", "insurance": "insurance",
    "samples": "samples", "documents": "documents", "complaints": "complaints",
    "messages": "messages", "shifts": "shifts", "roster": "roster",
    "attendance": "attendance", "observations": "observations",
    "referrals": "referrals", "suppliers": "suppliers",
    "purchase_orders": "purchase_orders",
    "notifications": "notifications", "fingerprint_devices": "fingerprint_devices",
    "videos": "videos", "vitals": "vitals", "finance": "finance",
    "beds": "beds", "bed_requests": "bed_requests", "blood_units": "blood_units",
    "ambulances": "ambulances", "ambulance_missions": "ambulance_missions",
    "theatre_cases": "theatre_cases", "imaging_studies": "imaging_studies",
    "cashier_invoices": "cashier_invoices",
    "app_settings": "app_settings",
}

# Columns the SQL files create. Anything else is stored in details so a new
# form field does not make the whole insert fail.
COLUMNS = {
    "users": {"id", "email", "password_hash", "name", "role", "phone", "dob", "gender", "blood", "emergency_contact", "status", "department", "last_login", "details"},
    "patients": {"id", "first_name", "last_name", "age", "gender", "phone", "email", "blood", "address", "emergency", "condition", "last_visit", "status", "details"},
    "appointments": {"id", "patient", "doctor", "dept", "date", "time", "type", "status", "no_show", "details"},
    "prescriptions": {"id", "patient", "doctor", "date", "status", "drugs", "details"},
    "inventory": {"id", "name", "category", "stock", "unit", "expiry", "status", "details"},
    "lab_requests": {"id", "patient", "test", "doctor", "date", "priority", "status", "details"},
    "lab_results": {"id", "patient", "test", "date", "status", "ai_flag", "values", "details"},
    "medications": {"id", "patient", "drug", "dose", "due", "status", "time", "details"},
    "care_plans": {"id", "patient", "plan", "created", "updated", "status", "steps", "details"},
    "bills": {"id", "date", "description", "amount", "status", "patient", "service", "method", "paid", "details"},
    "complaints": {"id", "reporter", "reporter_role", "category", "subject", "description", "priority", "date", "status", "solution", "resolved_by", "resolved_date", "details"},
    "messages": {"id", "from", "from_role", "subject", "body", "date", "read", "priority", "replies", "details"},
    "announcements": {"id", "title", "message", "audience", "author", "publish_date", "priority", "status", "views", "details"},
    "shifts": {"id", "name", "start", "end", "color", "css", "workers", "details"},
    "roster": {"id", "staff", "dept", "date", "shift", "start", "end", "details"},
    "attendance": {"id", "staff", "dept", "date", "shift", "check_in", "check_out", "status", "source", "device", "details"},
    "documents": {"id", "patient", "patient_id", "type", "title", "date", "size", "uploaded_by", "summary", "details"},
    "audit_logs": {"id", "ts", "user", "role", "action", "detail", "ip", "status", "details"},
    "insurance": {"id", "patient", "provider", "policy", "coverage", "valid_until", "status", "details"},
    "samples": {"id", "patient", "test", "type", "collected", "stage", "tat", "details"},
    "queue": {"id", "name", "dept", "arrived", "status", "details"},
    "departments": {"id", "name", "head", "staff", "beds", "occupied", "status", "details"},
    "staff": {"id", "name", "role", "dept", "shift", "status", "contact", "details"},
    "observations": {"id", "time", "patient", "pain", "intake", "output", "temp", "nurse", "notes", "details"},
    "referrals": {"id", "patient", "to", "specialty", "reason", "priority", "date", "status", "details"},
    "suppliers": {"id", "name", "contact", "phone", "categories", "lead_time", "rating", "details"},
    "purchase_orders": {"id", "supplier", "items", "total", "date", "status", "details"},
    "notifications": {"id", "title", "body", "audience", "read", "details"},
    "fingerprint_devices": {"id", "name", "location", "status", "details"},
    "videos": {"id", "title", "url", "topic", "audience", "details"},
    "vitals": {"id", "patient", "t", "hr", "sys", "dia", "temp", "spo2", "rr", "nurse", "details"},
    "finance": {"id", "date", "category", "description", "amount", "status", "details"},
    "beds": {"id", "ward", "status", "patient", "dx", "since", "doctor", "mrn", "details"},
    "bed_requests": {"id", "name", "mrn", "sex", "age", "dx", "ward", "priority", "note", "doctor", "status", "bed_id", "at", "approved_at", "details"},
    "blood_units": {"id", "type", "donor", "collected", "expires", "status", "for", "details"},
    "ambulances": {"id", "crew", "status", "place", "eta", "case", "details"},
    "ambulance_missions": {"id", "unit_id", "time", "text", "place", "status", "details"},
    "theatre_cases": {"id", "theatre", "time", "patient", "proc", "surgeon", "anaesth", "status", "details"},
    "imaging_studies": {"id", "patient", "study", "priority", "status", "note", "details"},
    "cashier_invoices": {"id", "patient", "service", "amount", "paid", "method", "status", "details"},
    "app_settings": {"id", "value"},
}


def _hide_secrets(row):
    if isinstance(row, dict):
        row.pop("password_hash", None)
    return row


def prepare_write(endpoint: str, data: dict) -> dict:
    """Keep known columns. Hash a plaintext password. Stash unknown fields."""
    data = dict(data or {})
    data.pop("password_hash", None)
    if endpoint == "users":
        password = data.pop("password", None)
        if password:
            from security import hash_password
            data["password_hash"] = hash_password(str(password))
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()
    # Frontend bed form uses camelCase; the columns are snake_case.
    if "bedId" in data and "bed_id" not in data:
        data["bed_id"] = data.pop("bedId")
    if "approvedAt" in data and "approved_at" not in data:
        data["approved_at"] = data.pop("approvedAt")
    allowed = COLUMNS.get(endpoint)
    if not allowed:
        return data
    clean, extra = {}, {}
    for key, value in data.items():
        if key in allowed:
            clean[key] = value
        elif key != "details":
            extra[key] = value
    if extra:
        details = clean.get("details") if isinstance(clean.get("details"), dict) else {}
        details.update(extra)
        clean["details"] = details
    return clean


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def _db_error(action: str, endpoint: str, exc: Exception) -> Dict[str, Any]:
    # Do not fall back to demo data when a real database is configured.
    # That used to hide schema errors and, on login, exposed demo passwords.
    log.error("supabase %s %s failed: %s", action, endpoint, type(exc).__name__)
    return {"ok": False, "error": "database unavailable", "source": "supabase"}


def _present(endpoint: str, row: dict) -> dict:
    if endpoint == "bed_requests":
        if row.get("bed_id") and "bedId" not in row:
            row["bedId"] = row["bed_id"]
        if row.get("approved_at") and "approvedAt" not in row:
            row["approvedAt"] = row["approved_at"]
    return row


def list_rows(endpoint: str, limit: int = 500) -> Dict[str, Any]:
    """GET /<endpoint> → {items:[...], total:n} from Supabase only."""
    limit = max(1, min(int(limit or 500), 500))
    table = TABLES.get(endpoint, endpoint)
    client = get_client()
    if client is None:
        return {"ok": False, "error": "Supabase is not configured", "source": "none", "items": [], "total": 0}
    try:
        resp = client.table(table).select("*").limit(limit).execute()
        items = [_present(endpoint, _hide_secrets(dict(item))) for item in (resp.data or [])]
        return {"ok": True, "items": items, "total": len(items), "source": "supabase"}
    except Exception as exc:  # noqa: BLE001
        return _db_error("read", endpoint, exc)


def insert_row(endpoint: str, data: dict) -> Dict[str, Any]:
    table = TABLES.get(endpoint, endpoint)
    payload = prepare_write(endpoint, data)
    client = get_client()
    if client is not None:
        try:
            resp = client.table(table).insert(payload).execute()
            row = _hide_secrets(dict((resp.data or [payload])[0]))
            return {"ok": True, "row": row, "source": "supabase"}
        except Exception as exc:  # noqa: BLE001
            return _db_error("insert", endpoint, exc)
    return {"ok": False, "error": "Supabase is not configured", "source": "none"}


def update_row(endpoint: str, row_id: str, data: dict) -> Dict[str, Any]:
    table = TABLES.get(endpoint, endpoint)
    payload = prepare_write(endpoint, data)
    payload.pop("id", None)
    client = get_client()
    if client is not None:
        try:
            resp = client.table(table).update(payload).eq("id", row_id).execute()
            row = _hide_secrets(dict((resp.data or [payload])[0]))
            return {"ok": True, "row": row, "source": "supabase"}
        except Exception as exc:  # noqa: BLE001
            return _db_error("update", endpoint, exc)
    return {"ok": False, "error": "Supabase is not configured", "source": "none"}


def delete_row(endpoint: str, row_id: str) -> Dict[str, Any]:
    table = TABLES.get(endpoint, endpoint)
    client = get_client()
    if client is not None:
        try:
            client.table(table).delete().eq("id", row_id).execute()
            return {"ok": True, "source": "supabase"}
        except Exception as exc:  # noqa: BLE001
            return _db_error("delete", endpoint, exc)
    return {"ok": False, "error": "Supabase is not configured", "source": "none"}

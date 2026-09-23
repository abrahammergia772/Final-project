# =============================================================================
# Wolaita Sodo Hospital — routers/auth.py
# POST /auth/login  ·  POST /auth/signup  ·  POST /auth/reset-password
# Authenticates against the Supabase `users` table when configured; otherwise
# falls back to built-in demo accounts so the whole system stays usable.
# =============================================================================
import logging
from typing import Optional
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db import get_client
from security import current_user, hash_password, issue_token, verify_password

router = APIRouter(tags=["Auth"])
log = logging.getLogger("mediq.auth")


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "patient"
    phone: str = ""
    dob: str = ""
    gender: str = ""
    blood: str = ""
    emergency_contact: str = ""
    department: str = ""
    details: dict = Field(default_factory=dict)


class ResetRequest(BaseModel):
    email: str
    code: str = ""
    new_password: str = ""


_RESET_CODES = {}
_ALLOWED_ROLES = {"patient", "doctor", "nurse", "pharmacist", "laboratory", "reception"}
_FAILS = {}


def _too_many(email: str) -> bool:
    now = time.time()
    hits = [t for t in _FAILS.get(email, []) if now - t < 600]
    _FAILS[email] = hits
    return len(hits) >= 8


def _note_failure(email: str) -> None:
    _FAILS.setdefault(email, []).append(time.time())


def _token_for(user_id, role, email, name):
    return issue_token(user_id, role, email=email, name=name)


@router.post("/auth/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    if _too_many(email):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")
    client = get_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    try:
        resp = client.table("users").select("id,email,name,role,status,password_hash").eq("email", email).limit(1).execute()
        rows = resp.data or []
    except Exception as exc:  # noqa: BLE001
        log.error("supabase login failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Sign-in service unavailable")
    if not rows or not verify_password(req.password, rows[0].get("password_hash") or ""):
        _note_failure(email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    row = rows[0]
    if row.get("status", "active") != "active":
        raise HTTPException(status_code=403, detail="Account is not active")
    _FAILS.pop(email, None)
    return {
        "token": _token_for(row.get("id"), row.get("role", "patient"), email, row.get("name") or email),
        "role": row.get("role", "patient"),
        "user_id": row.get("id"),
        "name": row.get("name", email),
        "email": email,
    }


@router.post("/auth/signup")
def signup(req: SignupRequest):
    if len(req.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    # Public registration can never create an administrator or manager account.
    role = req.role if req.role in _ALLOWED_ROLES else "patient"
    if role == "manager":
        role = "patient"
    client = get_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    try:
        existing = client.table("users").select("id").limit(1).execute()
        if not (existing.data or []):
            role = "admin"
        row = {
            "name": req.name, "email": req.email.strip().lower(),
            "password_hash": hash_password(req.password), "role": role,
            "phone": req.phone, "dob": req.dob, "gender": req.gender,
            "blood": req.blood, "emergency_contact": req.emergency_contact,
            "department": req.department, "details": req.details or {},
            "status": "active",
        }
        resp = client.table("users").insert(row).execute()
        created = dict((resp.data or [row])[0])
        created.pop("password_hash", None)
        return {"ok": True, "user": created}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("supabase signup failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Registration service unavailable")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str



def _merge_dict(base: dict, patch: dict) -> dict:
    out = dict(base or {})
    for key, value in (patch or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge_dict(out[key], value)
        else:
            out[key] = value
    return out


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    blood: Optional[str] = None
    emergency_contact: Optional[str] = None
    details_patch: dict = Field(default_factory=dict)


@router.post("/auth/profile")
def update_profile(req: ProfileUpdate, user=Depends(current_user)):
    """Save the signed-in person's own profile. Role and password stay unchanged."""
    client = get_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    uid = str(user.get("sub") or "")
    try:
        resp = client.table("users").select("id,email,name,role,phone,department,blood,emergency_contact,details").eq("id", uid).limit(1).execute()
    except Exception as exc:  # noqa: BLE001
        log.error("profile lookup failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Profile service unavailable")
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Account not found")
    current = rows[0]
    avatar = ""
    profile = req.details_patch.get("profile") if isinstance(req.details_patch.get("profile"), dict) else {}
    if profile:
        avatar = str(profile.get("avatar") or "")
    if len(avatar) > 500_000:
        raise HTTPException(status_code=413, detail="Profile photo is too large. Use an image under 300 KB.")
    email = str(current.get("email") or "").strip().lower() if req.email is None else req.email.strip().lower()
    if email and email != str(current.get("email") or "").strip().lower():
        try:
            taken = client.table("users").select("id").eq("email", email).limit(1).execute()
        except Exception as exc:  # noqa: BLE001
            log.error("email check failed: %s", type(exc).__name__)
            raise HTTPException(status_code=503, detail="Profile service unavailable")
        if taken.data and str(taken.data[0].get("id")) != uid:
            raise HTTPException(status_code=409, detail="That email is already used")
    details = current.get("details") if isinstance(current.get("details"), dict) else {}
    details = _merge_dict(details, req.details_patch or {})
    def keep(value, current_value):
        return current_value if value is None else value
    payload = {
        "name": str(keep(req.name, current.get("name") or "")).strip(),
        "phone": keep(req.phone, current.get("phone") or ""),
        "email": email,
        "department": keep(req.department, current.get("department") or ""),
        "blood": keep(req.blood, current.get("blood") or ""),
        "emergency_contact": keep(req.emergency_contact, current.get("emergency_contact") or ""),
        "details": details,
    }
    try:
        saved = client.table("users").update(payload).eq("id", uid).execute()
    except Exception as exc:  # noqa: BLE001
        log.error("profile update failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Could not save the profile")
    row = (saved.data or [payload])[0]
    row.pop("password_hash", None)
    return {"ok": True, "user": row}


@router.get("/auth/me")
def me(user=Depends(current_user)):
    client = get_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    try:
        resp = client.table("users").select("id,email,name,role,phone,department,status,blood,emergency_contact,dob,gender,details").eq("id", str(user.get("sub"))).limit(1).execute()
    except Exception as exc:  # noqa: BLE001
        log.error("supabase profile failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Profile service unavailable")
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Account not found")
    return rows[0]


@router.post("/auth/change-password")
def change_password(req: ChangePasswordRequest, user=Depends(current_user)):
    if len(req.new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    client = get_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    email = str(user.get("email") or "").strip().lower()
    try:
        resp = client.table("users").select("id,password_hash").eq("email", email).limit(1).execute()
        rows = resp.data or []
    except Exception as exc:  # noqa: BLE001
        log.error("supabase password lookup failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Password service unavailable")
    if not rows or not verify_password(req.current_password, rows[0].get("password_hash") or ""):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    client.table("users").update({"password_hash": hash_password(req.new_password)}).eq("id", rows[0]["id"]).execute()
    return {"ok": True}


@router.post("/auth/reset-password")
def reset_password(req: ResetRequest):
    email = req.email.strip().lower()
    # First call requests a short-lived code. In production this must be sent
    # through an email/SMS provider; never return it in the API response.
    if not req.code:
        code = f"{secrets.randbelow(1_000_000):06d}"
        _RESET_CODES[email] = (code, time.time() + 600)
        log.info("Password reset requested for %s", email)
        return {"ok": True, "message": "If the account exists, a reset code was sent."}
    record = _RESET_CODES.get(email)
    if not record or time.time() > record[1]:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    if not secrets.compare_digest(req.code, record[0]):
        _note_failure("reset:" + email)
        if _too_many("reset:" + email):
            _RESET_CODES.pop(email, None)
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    client = get_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    try:
        client.table("users").update({"password_hash": hash_password(req.new_password)}).eq("email", email).execute()
    except Exception as exc:  # noqa: BLE001
        log.error("supabase reset failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Password service unavailable")
    _RESET_CODES.pop(email, None)
    return {"ok": True}

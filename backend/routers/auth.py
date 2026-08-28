# =============================================================================
# Wolaita Sodo Hospital — routers/auth.py
# POST /auth/login  ·  POST /auth/signup  ·  POST /auth/reset-password
# Authenticates against the Supabase `users` table when configured; otherwise
# falls back to built-in demo accounts so the whole system stays usable.
# =============================================================================
import hashlib
import logging
import secrets
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_client, DEMO
from security import issue_token

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


class ResetRequest(BaseModel):
    email: str
    code: str = ""
    new_password: str = ""


_RESET_CODES = {}
_ALLOWED_ROLES = {"patient", "doctor", "nurse", "pharmacist", "laboratory", "reception", "manager"}


DEMO_USERS = {
    u["email"]: {"password": "password123", "role": u["role"], "name": u["name"]}
    for u in DEMO["users"]
}
# actual demo passwords (matching the frontend)
DEMO_PASSWORDS = {
    "admin@wsh.et": "admin123", "manager@wsh.et": "manager123",
    "doctor@wsh.et": "doctor123", "nurse@wsh.et": "nurse123",
    "pharmacist@wsh.et": "pharmacist123", "lab@wsh.et": "lab123",
    "reception@wsh.et": "reception123", "patient@wsh.et": "patient123",
}


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


@router.post("/auth/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()
    client = get_client()
    if client is not None:
        try:
            resp = client.table("users").select("*").eq("email", email).limit(1).execute()
            rows = resp.data or []
            if rows:
                row = rows[0]
                if row.get("password_hash") != _hash(req.password):
                    raise HTTPException(status_code=401, detail="Invalid email or password")
                if row.get("status", "active") != "active":
                    raise HTTPException(status_code=403, detail="Account is not active")
                return {"token": issue_token(row.get("id"), row.get("role", "patient")), "role": row.get("role", "patient"),
                        "user_id": row.get("id"), "name": row.get("name", email)}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase login failed: %s → demo", exc)
    # demo fallback
    if email in DEMO_PASSWORDS:
        if DEMO_PASSWORDS[email] == req.password:
            user = next(u for u in DEMO["users"] if u["email"] == email)
            return {"token": issue_token(user["id"], user["role"]), "role": user["role"],
                    "user_id": user["id"], "name": user["name"]}
    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/auth/signup")
def signup(req: SignupRequest):
    if len(req.password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    # Public registration can never create an administrator or manager account.
    role = req.role if req.role in _ALLOWED_ROLES else "patient"
    if role in {"manager"}:
        role = "patient"
    client = get_client()
    if client is not None:
        try:
            row = {
                "name": req.name, "email": req.email.strip().lower(),
                "password_hash": _hash(req.password), "role": role,
                "phone": req.phone, "dob": req.dob, "gender": req.gender,
                "blood": req.blood, "emergency_contact": req.emergency_contact,
                "status": "active" if role == "patient" else "pending",
            }
            resp = client.table("users").insert(row).execute()
            return {"ok": True, "user": (resp.data or [row])[0]}
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase signup failed: %s → demo", exc)
    return {"ok": True, "user": {"email": req.email.strip().lower(), "name": req.name, "role": role, "status": "demo"}}


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
    if not record or not secrets.compare_digest(req.code, record[0]) or time.time() > record[1]:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    client = get_client()
    if client is not None:
        try:
            client.table("users").update({"password_hash": _hash(req.new_password)}).eq("email", email).execute()
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase reset failed: %s", exc)
            raise HTTPException(status_code=503, detail="Password service unavailable")
    _RESET_CODES.pop(email, None)
    return {"ok": True}

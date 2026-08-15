# =============================================================================
# MedIQ Pro — routers/auth.py
# POST /auth/login  ·  POST /auth/signup  ·  POST /auth/reset-password
# Authenticates against the Supabase `users` table when configured; otherwise
# falls back to built-in demo accounts so the whole system stays usable.
# =============================================================================
import hashlib
import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_client, DEMO

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


DEMO_USERS = {
    u["email"]: {"password": "password123", "role": u["role"], "name": u["name"]}
    for u in DEMO["users"]
}
# actual demo passwords (matching the frontend)
DEMO_PASSWORDS = {
    "admin@mediq.pro": "admin123", "manager@mediq.pro": "manager123",
    "doctor@mediq.pro": "doctor123", "nurse@mediq.pro": "nurse123",
    "pharmacist@mediq.pro": "pharmacist123", "lab@mediq.pro": "lab123",
    "reception@mediq.pro": "reception123", "patient@mediq.pro": "patient123",
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
                return {"token": str(uuid.uuid4()), "role": row.get("role", "patient"),
                        "user_id": row.get("id"), "name": row.get("name", email)}
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase login failed: %s → demo", exc)
    # demo fallback
    if email in DEMO_PASSWORDS:
        if DEMO_PASSWORDS[email] == req.password:
            user = next(u for u in DEMO["users"] if u["email"] == email)
            return {"token": "demo-" + str(uuid.uuid4()), "role": user["role"],
                    "user_id": user["id"], "name": user["name"]}
    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/auth/signup")
def signup(req: SignupRequest):
    client = get_client()
    if client is not None:
        try:
            row = {
                "name": req.name, "email": req.email.strip().lower(),
                "password_hash": _hash(req.password), "role": req.role,
                "phone": req.phone, "dob": req.dob, "gender": req.gender,
                "blood": req.blood, "emergency_contact": req.emergency_contact,
                "status": "active" if req.role == "patient" else "pending",
            }
            resp = client.table("users").insert(row).execute()
            return {"ok": True, "user": (resp.data or [row])[0]}
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase signup failed: %s → demo", exc)
    return {"ok": True, "user": {"email": req.email.strip().lower(), "name": req.name, "role": req.role, "status": "demo"}}


@router.post("/auth/reset-password")
def reset_password(req: ResetRequest):
    client = get_client()
    if client is not None:
        try:
            client.table("users").update({"password_hash": _hash(req.new_password)}).eq("email", req.email.strip().lower()).execute()
            return {"ok": True}
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase reset failed: %s → demo", exc)
    return {"ok": True, "demo": True}

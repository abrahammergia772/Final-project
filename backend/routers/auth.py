"""Authentication endpoints.

Supabase is the source of truth when configured. The built-in accounts are
available only when the application is explicitly running without Supabase;
this prevents a database outage from silently turning production into demo
mode.
"""
from __future__ import annotations

import logging
import re
import secrets
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from config import supabase_configured
from db import DEMO, get_client
from security import hash_password, issue_token, verify_password


router = APIRouter(tags=["Auth"])
log = logging.getLogger("mediq.auth")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address")
        return value


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    role: str = "patient"
    phone: str = Field(default="", max_length=32)
    dob: str = Field(default="", max_length=32)
    gender: str = Field(default="", max_length=32)
    blood: str = Field(default="", max_length=16)
    emergency_contact: str = Field(default="", max_length=160)

    @field_validator("name", "phone", "dob", "gender", "blood", "emergency_contact")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address")
        return value


class ResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    code: str = Field(default="", max_length=6)
    new_password: str = Field(default="", max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.fullmatch(value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        value = value.strip()
        if value and (len(value) != 6 or not value.isdigit()):
            raise ValueError("Reset code must be six digits")
        return value


_RESET_CODES: dict[str, dict[str, Any]] = {}
_ALLOWED_SIGNUP_ROLES = {"patient", "doctor", "nurse", "pharmacist", "laboratory", "reception"}

DEMO_PASSWORDS = {
    "admin@mediq.pro": "admin123",
    "manager@mediq.pro": "manager123",
    "doctor@mediq.pro": "doctor123",
    "nurse@mediq.pro": "nurse123",
    "pharmacist@mediq.pro": "pharmacist123",
    "lab@mediq.pro": "lab123",
    "reception@mediq.pro": "reception123",
    "patient@mediq.pro": "patient123",
}


def _public_user(row: dict) -> dict:
    """Return a user response without password hashes or other secrets."""
    return {key: value for key, value in row.items() if key not in {"password_hash", "password"}}


def _demo_user(email: str) -> dict | None:
    return next((user for user in DEMO["users"] if user.get("email") == email), None)


@router.post("/auth/login")
def login(req: LoginRequest):
    email = req.email
    if supabase_configured():
        try:
            client = get_client()
            rows = client.table("users").select("*").eq("email", email).limit(1).execute().data or []
        except Exception as exc:  # noqa: BLE001
            log.exception("Supabase login failed")
            raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc

        if not rows or not verify_password(req.password, rows[0].get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        row = rows[0]
        if row.get("status", "active") != "active":
            raise HTTPException(status_code=403, detail="Account is not active")
        return {
            "token": issue_token(str(row.get("id")), row.get("role", "patient"), name=row.get("name", "")),
            "role": row.get("role", "patient"),
            "user_id": row.get("id"),
            "name": row.get("name", email),
        }

    # Demo accounts are intentionally disabled as soon as a real database is
    # configured. This is safe for local development and predictable in tests.
    if email in DEMO_PASSWORDS and secrets.compare_digest(DEMO_PASSWORDS[email], req.password):
        user = _demo_user(email)
        if user:
            return {
                "token": issue_token(user["id"], user["role"], name=user["name"]),
                "role": user["role"],
                "user_id": user["id"],
                "name": user["name"],
            }
    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/auth/signup")
def signup(req: SignupRequest):
    role = req.role.strip().lower()
    if role not in _ALLOWED_SIGNUP_ROLES:
        raise HTTPException(
            status_code=422,
            detail="Public registration is available for patients and approved staff roles only",
        )
    row = {
        "name": req.name.strip(),
        "email": req.email,
        "password_hash": hash_password(req.password),
        "role": role,
        "phone": req.phone,
        "dob": req.dob,
        "gender": req.gender,
        "blood": req.blood,
        "emergency_contact": req.emergency_contact,
        "status": "active" if role == "patient" else "pending",
    }

    if supabase_configured():
        try:
            client = get_client()
            response = client.table("users").insert(row).execute()
            saved = (response.data or [row])[0]
            return {"ok": True, "user": _public_user(saved)}
        except Exception as exc:  # noqa: BLE001
            log.exception("Supabase signup failed")
            duplicate = any(term in str(exc).lower() for term in ("duplicate", "unique", "already exists"))
            message = "An account with this email may already exist" if duplicate else "Registration service unavailable"
            raise HTTPException(status_code=409 if duplicate else 503, detail=message) from exc

    return {"ok": True, "user": {"email": req.email, "name": req.name, "role": role, "status": "demo"}}


@router.post("/auth/reset-password")
def reset_password(req: ResetRequest):
    email = req.email
    if not req.code:
        code = f"{secrets.randbelow(1_000_000):06d}"
        _RESET_CODES[email] = {"code": code, "expires": time.time() + 600, "attempts": 0}
        # Delivery is intentionally not implemented in this repository. Do not
        # put the code in the response or logs; wire this to an email provider
        # before exposing the endpoint publicly.
        log.info("Password reset requested")
        return {"ok": True, "message": "If the account exists, a reset code was sent."}

    record = _RESET_CODES.get(email)
    if not record or record["attempts"] >= 5 or time.time() > record["expires"]:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    record["attempts"] += 1
    if not secrets.compare_digest(req.code, record["code"]):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    if len(req.new_password) < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")

    if supabase_configured():
        try:
            client = get_client()
            response = client.table("users").update({"password_hash": hash_password(req.new_password)}).eq("email", email).execute()
            if not response.data:
                raise HTTPException(status_code=400, detail="Invalid or expired reset code")
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            log.exception("Supabase password reset failed")
            raise HTTPException(status_code=503, detail="Password service unavailable") from exc

    _RESET_CODES.pop(email, None)
    return {"ok": True}

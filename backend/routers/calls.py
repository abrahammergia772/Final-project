"""Authenticated call invitations and short-lived Jitsi room tokens.

The Jitsi deployment must itself require and validate these JWTs. This API
cannot enforce who enters a meeting on an anonymously accessible Jitsi server.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config import SUPABASE_SERVICE_KEY
from db import get_client
from security import current_user

router = APIRouter(prefix="/calls", tags=["Calls"])
ROLES = {"admin", "manager", "doctor", "nurse", "pharmacist", "laboratory", "reception", "patient"}


def _client():
    client = get_client()
    if not client or not SUPABASE_SERVICE_KEY:
        raise HTTPException(503, "Calls require a configured Supabase service-role key and call_invites table.")
    return client


def _jitsi():
    domain = os.getenv("JITSI_DOMAIN", "").strip().lower()
    app_id = os.getenv("JITSI_APP_ID", "").strip()
    secret = os.getenv("JITSI_APP_SECRET", "").strip()
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]{1,5})?", domain) or not app_id or not secret:
        raise HTTPException(503, "Calling is not configured. Configure a private JWT-authenticated Jitsi server first.")
    return domain, app_id, secret


def _now():
    return datetime.now(timezone.utc)


def _db(fn):
    try:
        return fn()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "Call service unavailable. Check the database configuration and migration.") from exc


def _active_user(client, user):
    rows = _db(lambda: client.table("users").select("id,name,role,status").eq("id", str(user["sub"])).limit(1).execute().data) or []
    if not rows or rows[0].get("status") != "active" or rows[0].get("role") not in ROLES:
        raise HTTPException(403, "An active account is required for calls.")
    return rows[0]


def _row(client, call_id, user_id):
    rows = _db(lambda: client.table("call_invites").select("*").eq("call_id", call_id).eq("user_id", str(user_id)).limit(1).execute().data) or []
    if not rows:
        raise HTTPException(404, "Call not found")
    row = rows[0]
    try:
        expired = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) <= _now()
    except (KeyError, ValueError, TypeError):
        expired = True
    if expired or row.get("status") in {"ended", "declined", "left"}:
        raise HTTPException(410, "This call has ended or expired.")
    return row


def _jwt(domain, app_id, secret, room, person, expires_at):
    def b64(obj):
        return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).rstrip(b"=").decode()
    now = int(time.time())
    exp = min(now + 1800, int(datetime.fromisoformat(expires_at.replace("Z", "+00:00")).timestamp()))
    payload = {"aud": "jitsi", "iss": app_id, "sub": domain.split(":")[0], "room": room,
               "iat": now, "nbf": now - 10, "exp": exp,
               "context": {"user": {"id": str(person["id"]), "name": person.get("name") or "Hospital user"}}}
    unsigned = b64({"alg": "HS256", "typ": "JWT"}) + "." + b64(payload)
    sig = base64.urlsafe_b64encode(hmac.new(secret.encode(), unsigned.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    return unsigned + "." + sig


class NewCall(BaseModel):
    recipients: list[str] = Field(min_length=1, max_length=20)
    mode: str = Field(pattern="^(audio|video)$")


class DirectorySearch(BaseModel):
    email: str = Field(max_length=254)


@router.post("/directory")
def directory(req: DirectorySearch, user=Depends(current_user)):
    client = _client()
    _active_user(client, user)
    email = req.email.strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise HTTPException(422, "Enter a complete email address to find a participant.")
    rows = _db(lambda: client.table("users").select("id,name,role,status").eq("email", email).eq("status", "active").limit(1).execute().data) or []
    return {"items": [{"id": str(r["id"]), "name": r.get("name") or "Hospital user", "role": r.get("role") or ""}
                      for r in rows if str(r.get("id")) != str(user["sub"]) and r.get("role") in ROLES]}


@router.get("")
def list_calls(user=Depends(current_user)):
    client = _client()
    _active_user(client, user)
    rows = _db(lambda: client.table("call_invites").select("call_id,caller_name,caller_id,mode,status,expires_at,created_at")
               .eq("user_id", str(user["sub"])).in_("status", ["pending", "accepted"]).gt("expires_at", _now().isoformat())
               .order("created_at", desc=True).limit(30).execute().data) or []
    return {"items": rows}


@router.post("")
def create_call(req: NewCall, user=Depends(current_user)):
    _jitsi()  # Do not create invitations when the meeting service is unavailable.
    client = _client()
    person = _active_user(client, user)
    ids = list(dict.fromkeys(str(x).strip() for x in req.recipients if str(x).strip() and str(x).strip() != str(user["sub"])))
    if not ids:
        raise HTTPException(422, "Select at least one other participant.")
    recipients = _db(lambda: client.table("users").select("id,status,role").in_("id", ids).execute().data) or []
    if len(recipients) != len(ids) or any(r.get("status") != "active" or r.get("role") not in ROLES for r in recipients):
        raise HTTPException(422, "One or more participants are unavailable.")
    call_id = secrets.token_urlsafe(24)
    room = "wsh-" + secrets.token_hex(24)
    expiry = (_now() + timedelta(hours=1)).isoformat()
    base = {"call_id": call_id, "caller_id": str(person["id"]), "caller_name": person.get("name") or "Hospital user",
            "mode": req.mode, "room": room, "expires_at": expiry}
    rows = [{**base, "user_id": str(person["id"]), "status": "accepted"}]
    rows += [{**base, "user_id": uid, "status": "pending"} for uid in ids]
    _db(lambda: client.table("call_invites").insert(rows).execute())
    return {"call_id": call_id}


@router.post("/{call_id}/join")
def join_call(call_id: str, user=Depends(current_user)):
    domain, app_id, secret = _jitsi()
    client = _client()
    person = _active_user(client, user)
    row = _row(client, call_id, user["sub"])
    host = _row(client, call_id, row["caller_id"])
    if host["status"] != "accepted":
        raise HTTPException(410, "This call has ended.")
    if row["status"] == "pending":
        changed = _db(lambda: client.table("call_invites").update({"status": "accepted"}).eq("call_id", call_id)
                      .eq("user_id", str(user["sub"])).eq("status", "pending").execute().data) or []
        if not changed:
            raise HTTPException(409, "This invitation is no longer available.")
    # Recheck host after acceptance to reduce races with ending a call.
    _row(client, call_id, row["caller_id"])
    return {"domain": domain, "room": row["room"], "mode": row["mode"],
            "token": _jwt(domain, app_id, secret, row["room"], person, row["expires_at"]),
            "name": person.get("name") or "Hospital user"}


@router.post("/{call_id}/decline")
def decline_call(call_id: str, user=Depends(current_user)):
    client = _client()
    _active_user(client, user)
    row = _row(client, call_id, user["sub"])
    if row["caller_id"] == str(user["sub"]) or row["status"] != "pending":
        raise HTTPException(409, "Only pending invitations can be declined.")
    _db(lambda: client.table("call_invites").update({"status": "declined"}).eq("call_id", call_id).eq("user_id", str(user["sub"])).eq("status", "pending").execute())
    return {"ok": True}


@router.post("/{call_id}/leave")
def leave_call(call_id: str, user=Depends(current_user)):
    client = _client()
    _active_user(client, user)
    row = _row(client, call_id, user["sub"])
    if row["caller_id"] == str(user["sub"]):
        _db(lambda: client.table("call_invites").update({"status": "ended"}).eq("call_id", call_id).execute())
    else:
        _db(lambda: client.table("call_invites").update({"status": "left"}).eq("call_id", call_id).eq("user_id", str(user["sub"])).execute())
    return {"ok": True}

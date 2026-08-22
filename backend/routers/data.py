"""Authenticated, role-aware CRUD endpoints for application data.

The original generic CRUD route made every authorized role able to mutate every
row in a resource. This module keeps the convenient resource API but adds
operation permissions, patient ownership checks, bounded queries, and safe
handling of database failures.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from db import DataStoreError, insert_row, list_rows, update_row, delete_row
from security import current_user


router = APIRouter(tags=["Data"])

RESOURCES = [
    "users", "patients", "appointments", "prescriptions", "inventory",
    "lab_requests", "lab_results", "medications", "care_plans", "bills",
    "audit_logs", "queue", "announcements", "departments", "staff",
    "insurance", "samples", "documents", "complaints", "messages",
    "notifications", "shifts", "roster", "attendance", "observations",
    "referrals", "suppliers", "purchase_orders", "fingerprint_devices",
    "videos", "finance",
]

ROLE_RESOURCES = {
    "admin": set(RESOURCES),
    "manager": set(RESOURCES) - {"users", "audit_logs"},
    "doctor": {"patients", "appointments", "prescriptions", "lab_requests", "lab_results", "documents", "messages", "referrals", "care_plans", "attendance", "roster", "shifts", "videos"},
    "nurse": {"patients", "medications", "care_plans", "lab_results", "documents", "messages", "observations", "attendance", "roster", "shifts"},
    "pharmacist": {"patients", "prescriptions", "inventory", "suppliers", "purchase_orders", "documents", "messages", "attendance", "roster", "shifts"},
    "laboratory": {"patients", "lab_requests", "lab_results", "samples", "documents", "messages", "attendance", "roster", "shifts"},
    "reception": {"patients", "appointments", "queue", "insurance", "documents", "messages", "attendance", "roster", "shifts"},
    "patient": {"patients", "appointments", "prescriptions", "lab_results", "medications", "care_plans", "bills", "complaints", "messages", "videos"},
}

# The mutation matrix is intentionally narrower than the read matrix. It is
# still data-driven, so adding a page does not require duplicating endpoints.
MUTABLE = {
    "admin": set(RESOURCES),
    "manager": {"appointments", "announcements", "complaints", "departments", "documents", "finance", "insurance", "messages", "patients", "queue", "roster", "shifts", "staff", "attendance"},
    "doctor": {"appointments", "care_plans", "documents", "lab_requests", "messages", "prescriptions", "referrals"},
    "nurse": {"care_plans", "documents", "messages", "observations"},
    "pharmacist": {"documents", "inventory", "messages", "purchase_orders", "suppliers"},
    "laboratory": {"documents", "lab_requests", "lab_results", "messages", "samples"},
    "reception": {"appointments", "documents", "insurance", "messages", "patients", "queue"},
    "patient": {"appointments", "complaints", "messages"},
}

# Rows that represent a person's own record. Patient sessions may only see or
# modify their own rows; staff sessions retain their role-scoped access.
PATIENT_SCOPED = {
    "patients", "appointments", "prescriptions", "lab_requests", "lab_results",
    "medications", "care_plans", "bills", "complaints", "documents", "insurance",
}


def _check_resource(resource: str, user: dict) -> None:
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown resource")
    if resource not in ROLE_RESOURCES.get(user.get("role"), set()):
        raise HTTPException(status_code=403, detail="You do not have access to this resource")


def _can_mutate(resource: str, user: dict) -> None:
    _check_resource(resource, user)
    if resource not in MUTABLE.get(user.get("role"), set()):
        raise HTTPException(status_code=403, detail="You do not have permission to change this resource")


def _user_name(user: dict) -> str:
    return str(user.get("name", "")).strip().casefold()


def _belongs_to_user(resource: str, row: dict, user: dict) -> bool:
    if user.get("role") != "patient" or (resource not in PATIENT_SCOPED and resource != "messages"):
        return True
    owner = _user_name(user)
    if resource == "messages":
        return str(row.get("from", "")).strip().casefold() == owner
    values = [
        row.get("patient"), row.get("reporter"), row.get("name"), row.get("email"),
        row.get("patient_id"), row.get("user_id"), row.get("to"),
    ]
    full_name = f'{row.get("first_name", "")} {row.get("last_name", "")}'.strip()
    values.append(full_name)
    return bool(owner) and any(str(value or "").strip().casefold() == owner for value in values)


def _filter_rows(resource: str, result: dict, user: dict) -> dict:
    if user.get("role") != "patient":
        return result
    if resource == "messages":
        owner = _user_name(user)
        # Legacy messages without recipients remain visible for compatibility;
        # newly addressed messages are visible only to their recipient.
        items = [row for row in result.get("items", []) if not row.get("to") or str(row.get("to")).strip().casefold() == owner]
        return {**result, "items": items, "total": len(items)}
    if resource not in PATIENT_SCOPED:
        return result
    items = [row for row in result.get("items", []) if _belongs_to_user(resource, row, user)]
    return {**result, "items": items, "total": len(items)}


def _enforce_patient_body(resource: str, body: dict, user: dict) -> dict:
    if user.get("role") != "patient":
        return body
    if resource == "complaints":
        body["reporter"] = user.get("name", "")
        body["reporter_role"] = "patient"
    elif resource == "messages":
        body["from"] = user.get("name", "")
        body["from_role"] = "patient"
    elif resource in PATIENT_SCOPED:
        requested = str(body.get("patient", "")).strip()
        if requested and requested.casefold() != _user_name(user):
            raise HTTPException(status_code=403, detail="You can only submit records for your own account")
        body["patient"] = user.get("name", "")
    return body


def _owned_row_or_404(resource: str, row_id: str, user: dict) -> None:
    if user.get("role") != "patient" or (resource not in PATIENT_SCOPED and resource != "messages"):
        return
    result = list_rows(resource, 500)
    row = next((item for item in result.get("items", []) if str(item.get("id")) == row_id), None)
    if row is None or not _belongs_to_user(resource, row, user):
        raise HTTPException(status_code=404, detail="Record not found")


def _handle_store_error(exc: DataStoreError) -> None:
    raise HTTPException(status_code=503, detail="The data store is temporarily unavailable") from exc


@router.get("/messages/sent")
def sent_messages(user=Depends(current_user)):
    _check_resource("messages", user)
    try:
        result = list_rows("messages")
    except DataStoreError as exc:
        _handle_store_error(exc)
    # Older rows do not carry a sender/recipient field. Only filter when the
    # schema has enough information to do so; this preserves existing data.
    sender = _user_name(user)
    items = [row for row in result["items"] if not row.get("from") or str(row.get("from")).casefold() == sender]
    return {**result, "items": items, "total": len(items)}


@router.get("/{resource}")
def read_all(
    resource: str,
    limit: int = Query(default=500, ge=1, le=500),
    user=Depends(current_user),
):
    _check_resource(resource, user)
    try:
        return _filter_rows(resource, list_rows(resource, limit), user)
    except DataStoreError as exc:
        _handle_store_error(exc)


@router.post("/{resource}")
async def create(resource: str, request: Request, user=Depends(current_user)):
    _can_mutate(resource, user)
    try:
        body: Any = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")
    body = _enforce_patient_body(resource, body, user)
    body.pop("id", None)
    try:
        return insert_row(resource, body)
    except DataStoreError as exc:
        _handle_store_error(exc)


@router.put("/{resource}/{row_id}")
async def update(resource: str, row_id: str, request: Request, user=Depends(current_user)):
    _can_mutate(resource, user)
    _owned_row_or_404(resource, row_id, user)
    try:
        body: Any = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")
    body = _enforce_patient_body(resource, body, user)
    body.pop("id", None)
    try:
        result = update_row(resource, row_id, body)
    except DataStoreError as exc:
        _handle_store_error(exc)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail="Record not found")
    return result


@router.delete("/{resource}/{row_id}")
def delete(resource: str, row_id: str, user=Depends(current_user)):
    _can_mutate(resource, user)
    _owned_row_or_404(resource, row_id, user)
    try:
        result = delete_row(resource, row_id)
    except DataStoreError as exc:
        _handle_store_error(exc)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail="Record not found")
    return result

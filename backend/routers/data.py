# =============================================================================
# Wolaita Sodo Hospital — routers/data.py
# Generic CRUD for every core-data table the frontend uses. Reads/writes the
# matching Supabase table when configured, otherwise the in-memory demo store.
#   GET    /<resource>           → {items, total, source}
#   POST   /<resource>           → create
#   PUT    /<resource>/{id}      → update
#   DELETE /<resource>/{id}      → delete
# =============================================================================
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel

from db import list_rows, insert_row, update_row, delete_row
from security import current_user

router = APIRouter(tags=["Data"])

RESOURCES = [
    "users", "patients", "appointments", "prescriptions", "inventory",
    "lab_requests", "lab_results", "medications", "care_plans", "bills",
    "audit_logs", "queue", "announcements", "departments", "staff",
    "insurance", "samples", "documents", "complaints", "messages",
    "notifications", "shifts", "roster", "attendance",
    "observations", "referrals", "suppliers", "purchase_orders",
    "fingerprint_devices", "videos",
]


class GenericBody(BaseModel):
    # arbitrary JSON accepted
    class Config:
        extra = "allow"


ROLE_RESOURCES = {
    "admin": set(RESOURCES),
    "manager": set(RESOURCES) - {"users", "audit_logs"},
    "doctor": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "fingerprint_devices"},
    "nurse": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "fingerprint_devices"},
    "pharmacist": set(RESOURCES) - {"users", "audit_logs", "fingerprint_devices"},
    "laboratory": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "inventory", "fingerprint_devices"},
    "reception": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "fingerprint_devices"},
    "patient": {"patients", "appointments", "prescriptions", "lab_results", "medications", "care_plans", "bills", "complaints", "messages", "documents", "videos", "announcements"},
}


def _authorize(resource: str, user):
    if resource not in RESOURCES or resource not in ROLE_RESOURCES.get(user["role"], set()):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="You do not have access to this resource")


@router.get("/messages/sent")
def sent_messages(user=Depends(current_user)):
    _authorize("messages", user)
    return list_rows("messages")


@router.get("/{resource}")
def read_all(resource: str, limit: int = 500, user=Depends(current_user)):
    _authorize(resource, user)
    if resource not in RESOURCES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unknown resource")
    return list_rows(resource, limit)


@router.post("/{resource}")
async def create(resource: str, request: Request, user=Depends(current_user)):
    _authorize(resource, user)
    body = await request.json()
    return insert_row(resource, body)


@router.put("/{resource}/{row_id}")
async def update(resource: str, row_id: str, request: Request, user=Depends(current_user)):
    _authorize(resource, user)
    body = await request.json()
    return update_row(resource, row_id, body)


@router.delete("/{resource}/{row_id}")
def delete(resource: str, row_id: str, user=Depends(current_user)):
    _authorize(resource, user)
    return delete_row(resource, row_id)

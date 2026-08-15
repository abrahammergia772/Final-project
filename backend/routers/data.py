# =============================================================================
# MedIQ Pro — routers/data.py
# Generic CRUD for every core-data table the frontend uses. Reads/writes the
# matching Supabase table when configured, otherwise the in-memory demo store.
#   GET    /<resource>           → {items, total, source}
#   POST   /<resource>           → create
#   PUT    /<resource>/{id}      → update
#   DELETE /<resource>/{id}      → delete
# =============================================================================
from fastapi import APIRouter, Request
from pydantic import BaseModel

from db import list_rows, insert_row, update_row, delete_row

router = APIRouter(tags=["Data"])

RESOURCES = [
    "users", "patients", "appointments", "prescriptions", "inventory",
    "lab_requests", "lab_results", "medications", "care_plans", "bills",
    "audit_logs", "queue", "announcements", "departments", "staff",
    "insurance", "samples", "documents", "complaints", "messages",
    "messages/sent", "notifications", "shifts", "roster", "attendance",
    "observations", "referrals", "suppliers", "purchase_orders",
]


class GenericBody(BaseModel):
    # arbitrary JSON accepted
    class Config:
        extra = "allow"


@router.get("/{resource}")
def read_all(resource: str, limit: int = 500):
    if resource not in RESOURCES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unknown resource")
    return list_rows(resource, limit)


@router.post("/{resource}")
async def create(resource: str, request: Request):
    from fastapi import HTTPException
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown resource")
    body = await request.json()
    return insert_row(resource, body)


@router.put("/{resource}/{row_id}")
async def update(resource: str, row_id: str, request: Request):
    from fastapi import HTTPException
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown resource")
    body = await request.json()
    return update_row(resource, row_id, body)


@router.delete("/{resource}/{row_id}")
def delete(resource: str, row_id: str):
    from fastapi import HTTPException
    if resource not in RESOURCES:
        raise HTTPException(status_code=404, detail="Unknown resource")
    return delete_row(resource, row_id)

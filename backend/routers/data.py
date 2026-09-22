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
    "fingerprint_devices", "videos", "vitals", "finance",
    "beds", "bed_requests", "blood_units", "ambulances", "ambulance_missions",
    "theatre_cases", "imaging_studies", "cashier_invoices",
]


class GenericBody(BaseModel):
    # arbitrary JSON accepted
    class Config:
        extra = "allow"


ROLE_RESOURCES = {
    "admin": set(RESOURCES),
    "manager": set(RESOURCES) - {"users", "audit_logs", "fingerprint_devices"},
    "doctor": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "fingerprint_devices", "finance"},
    "nurse": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "fingerprint_devices", "finance", "cashier_invoices"},
    "pharmacist": set(RESOURCES) - {"users", "audit_logs", "fingerprint_devices", "beds", "bed_requests", "blood_units", "ambulances", "ambulance_missions", "theatre_cases", "imaging_studies", "finance"},
    "laboratory": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "inventory", "fingerprint_devices", "finance", "cashier_invoices", "ambulances", "ambulance_missions"},
    "reception": set(RESOURCES) - {"users", "audit_logs", "suppliers", "purchase_orders", "fingerprint_devices", "finance", "blood_units", "theatre_cases"},
    "patient": {"patients", "appointments", "prescriptions", "lab_results", "medications", "care_plans", "bills", "cashier_invoices", "complaints", "messages", "documents", "videos", "announcements"},
}

# Write access is narrower than read access for clinical actions.
WRITE_ROLES = {
    "users": {"admin"},
    "audit_logs": {"admin"},
    "fingerprint_devices": {"admin"},
    "bed_requests": {"doctor", "admin"},
    "beds": {"doctor", "admin"},
    "blood_units": {"laboratory", "admin"},
    "theatre_cases": {"doctor", "admin"},
    "imaging_studies": {"doctor", "laboratory", "admin"},
    "ambulances": {"reception", "admin"},
    "ambulance_missions": {"reception", "admin"},
    "cashier_invoices": {"reception", "admin", "manager"},
    "finance": {"manager", "admin"},
}
PATIENT_WRITE = {"complaints", "messages"}


def _authorize(resource: str, user, write: bool = False):
    from fastapi import HTTPException
    if resource not in RESOURCES or resource not in ROLE_RESOURCES.get(user["role"], set()):
        raise HTTPException(status_code=403, detail="You do not have access to this resource")
    if write and resource in WRITE_ROLES and user["role"] not in WRITE_ROLES[resource]:
        raise HTTPException(status_code=403, detail="You cannot change this resource")
    if write and user["role"] == "patient" and resource not in PATIENT_WRITE:
        raise HTTPException(status_code=403, detail="You cannot change this resource")


def _owns(row: dict, user) -> bool:
    email = str(user.get("email") or "").strip().lower()
    name = str(user.get("name") or "").strip().lower()
    fields = ("email", "patient", "reporter", "name", "from", "uploaded_by")
    values = {str(row.get(key) or "").strip().lower() for key in fields}
    if email and email in values:
        return True
    if name and name in values:
        return True
    patient = str(row.get("patient") or "").strip().lower()
    return bool(patient and ((name and name in patient) or (email and email in patient)))


def _scope(resource: str, result: dict, user) -> dict:
    if user["role"] != "patient" or resource in {"announcements", "videos"}:
        return result
    items = [row for row in result.get("items", []) if _owns(row, user)]
    return {**result, "items": items, "total": len(items)}


def _fail_if_down(result: dict):
    from fastapi import HTTPException
    if result.get("ok") is False and result.get("source") == "supabase":
        raise HTTPException(status_code=503, detail="Database unavailable")
    return result


@router.get("/messages/sent")
def sent_messages(user=Depends(current_user)):
    _authorize("messages", user)
    return _scope("messages", _fail_if_down(list_rows("messages")), user)


@router.get("/{resource}")
def read_all(resource: str, limit: int = 500, user=Depends(current_user)):
    _authorize(resource, user)
    if resource not in RESOURCES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unknown resource")
    return _scope(resource, _fail_if_down(list_rows(resource, limit)), user)


@router.post("/{resource}")
async def create(resource: str, request: Request, user=Depends(current_user)):
    _authorize(resource, user, write=True)
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    return _fail_if_down(insert_row(resource, _stamp_patient(resource, body, user)))


def _stamp_patient(resource: str, body: dict, user) -> dict:
    if user.get("role") != "patient":
        return body
    who = user.get("name") or user.get("email") or ""
    if resource == "complaints":
        body["reporter"] = who
        body["reporter_role"] = "patient"
    if resource == "messages":
        body["from"] = who
        body["from_role"] = "patient"
    return body


def _assert_patient_owns(resource: str, row_id: str, user):
    from fastapi import HTTPException
    if user.get("role") != "patient":
        return
    result = _fail_if_down(list_rows(resource))
    row = next((item for item in result.get("items", []) if str(item.get("id")) == str(row_id)), None)
    if not row or not _owns(row, user):
        raise HTTPException(status_code=403, detail="You can only change your own records")


@router.put("/{resource}/{row_id}")
async def update(resource: str, row_id: str, request: Request, user=Depends(current_user)):
    _authorize(resource, user, write=True)
    _assert_patient_owns(resource, row_id, user)
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    return _fail_if_down(update_row(resource, row_id, _stamp_patient(resource, body, user)))


@router.delete("/{resource}/{row_id}")
def delete(resource: str, row_id: str, user=Depends(current_user)):
    _authorize(resource, user, write=True)
    if user["role"] == "patient":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="You cannot delete records")
    return _fail_if_down(delete_row(resource, row_id))

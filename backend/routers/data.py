# =============================================================================
# Wolaita Sodo Hospital — routers/data.py
# Generic CRUD for every core-data table the frontend uses. Reads/writes the
# matching Supabase table when configured, otherwise the in-memory demo store.
#   GET    /<resource>           → {items, total, source}
#   POST   /<resource>           → create
#   PUT    /<resource>/{id}      → update
#   DELETE /<resource>/{id}      → delete
# =============================================================================
import logging

import base64
import secrets
from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, Request, Depends, UploadFile
from pydantic import BaseModel, Field

from youtube_search import search_youtube

from db import list_rows, insert_row, update_row, delete_row, get_row, get_client
from permissions import assert_resource
from security import current_user

router = APIRouter(tags=["Data"])
log = logging.getLogger("mediq.videos")

RESOURCES = [
    "users", "patients", "appointments", "prescriptions", "inventory",
    "lab_requests", "lab_results", "medications", "care_plans", "bills",
    "audit_logs", "queue", "announcements", "departments", "staff",
    "insurance", "samples", "documents", "complaints", "messages",
    "notifications", "shifts", "roster", "attendance",
    "observations", "referrals", "suppliers", "purchase_orders",
    "fingerprint_devices", "videos", "vitals", "finance",
    "beds", "bed_requests", "blood_units", "ambulances", "ambulance_missions",
    "theatre_cases", "imaging_studies", "cashier_invoices", "app_settings",
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
    "patient": {"patients", "appointments", "prescriptions", "lab_results", "medications", "care_plans", "bills", "cashier_invoices", "complaints", "messages", "documents", "videos", "announcements", "app_settings"},
}

# Write access is narrower than read access for clinical actions.
WRITE_ROLES = {
    "users": {"admin"},
    "audit_logs": {"admin"},
    "fingerprint_devices": {"admin"},
    "bed_requests": {"doctor", "admin"},
    "beds": {"doctor", "nurse", "reception", "manager", "admin"},
    "blood_units": {"laboratory", "admin"},
    "theatre_cases": {"doctor", "admin"},
    "imaging_studies": {"doctor", "laboratory", "admin"},
    "ambulances": {"reception", "admin"},
    "ambulance_missions": {"reception", "admin"},
    "cashier_invoices": {"reception", "admin", "manager"},
    "finance": {"manager", "admin"},
    "app_settings": {"admin"},
}
PATIENT_WRITE = {"complaints", "messages", "appointments"}


def _authorize(resource: str, user, write: bool = False):
    from fastapi import HTTPException
    if resource not in RESOURCES or resource not in ROLE_RESOURCES.get(user["role"], set()):
        raise HTTPException(status_code=403, detail="You do not have access to this resource")
    if write and resource in WRITE_ROLES and user["role"] not in WRITE_ROLES[resource]:
        raise HTTPException(status_code=403, detail="You cannot change this resource")
    if write and user["role"] == "patient" and resource not in PATIENT_WRITE:
        raise HTTPException(status_code=403, detail="You cannot change this resource")
    assert_resource(user, resource)


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
    if result.get("ok") is False:
        detail = "Supabase is not configured" if result.get("source") == "none" else "Database unavailable"
        raise HTTPException(status_code=503, detail=result.get("error") or detail)
    return result



class VideoSearchBody(BaseModel):
    query: str = ""
    conditions: list[str] = Field(default_factory=list)
    max_results: int = 12


@router.post("/videos/search")
def search_health_videos(body: VideoSearchBody, user=Depends(current_user)):
    """Search YouTube for health-education videos. Does not write a hospital record."""
    if "videos" not in ROLE_RESOURCES.get(user.get("role"), set()):
        raise HTTPException(status_code=403, detail="You do not have access to health videos")
    from permissions import assert_key
    assert_key(user, "videos")
    query = " ".join((body.query or "").split())
    if not query and body.conditions:
        query = " ".join(str(item).strip() for item in body.conditions if str(item).strip())
    if not query:
        raise HTTPException(status_code=400, detail="Type a health topic to search")
    try:
        items = search_youtube(query, body.max_results)
    except Exception as exc:  # noqa: BLE001
        log.warning("health video search failed: %s", exc)
        raise HTTPException(status_code=502, detail="YouTube search is unavailable right now") from exc
    return {"items": items, "total": len(items), "source": "youtube"}



_GROUP_ROLES = {
    "all staff": {"admin", "manager", "doctor", "nurse", "pharmacist", "laboratory", "reception"},
    "all doctors": {"doctor"},
    "all nurses": {"nurse"},
    "all pharmacists": {"pharmacist"},
    "all laboratory": {"laboratory"},
    "all reception": {"reception"},
    "all patients": {"patient"},
    "all managers": {"manager"},
    "all admins": {"admin"},
}


def _message_box(row: dict, user, box: str) -> bool:
    name = str(user.get("name") or "").strip().lower()
    email = str(user.get("email") or "").strip().lower()
    uid = str(user.get("sub") or "")
    role = str(user.get("role") or "")
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    to_name = str(row.get("to") or details.get("to") or "").strip().lower()
    to_email = str(row.get("to_email") or details.get("to_email") or "").strip().lower()
    to_id = str(row.get("to_id") or details.get("to_id") or "")
    from_name = str(row.get("from") or "").strip().lower()
    from_email = str(row.get("from_email") or details.get("from_email") or "").strip().lower()
    sent_by_me = bool((name and from_name == name) or (email and from_email == email))
    if box == "sent":
        return sent_by_me
    patient = str(row.get("patient") or details.get("patient") or "").strip().lower()
    addressed = bool(
        (email and to_email == email)
        or (uid and to_id == uid)
        or (name and to_name == name)
        or (name and patient and name in patient)
        or (role and role in _GROUP_ROLES.get(to_name, set()))
    )
    return addressed


def _message_view(user, box: str) -> dict:
    result = _fail_if_down(list_rows("messages"))
    items = [row for row in result.get("items", []) if _message_box(row, user, box)]
    items.sort(key=lambda row: str(row.get("date") or ""), reverse=True)
    return {**result, "items": items, "total": len(items)}



@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    patient: str = Form(""),
    patient_id: str = Form(""),
    doc_type: str = Form("Other"),
    summary: str = Form(""),
    user=Depends(current_user),
):
    """Store an uploaded file on the document row in Supabase."""
    _authorize("documents", user, write=True)
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Choose a file to upload")
    if len(raw) > 1_200_000:
        raise HTTPException(status_code=413, detail="File is too large. Use a file under 1.2 MB.")
    mime = file.content_type or "application/octet-stream"
    data_url = "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii")
    row = {
        "id": "DOC-" + secrets.token_hex(4).upper(),
        "patient": patient.strip() or "Patient",
        "patient_id": patient_id.strip(),
        "type": doc_type.strip() or "Other",
        "title": title.strip() or (file.filename or "Uploaded document"),
        "date": date.today().isoformat(),
        "size": str(max(1, round(len(raw) / 1024))) + " KB",
        "uploaded_by": user.get("name") or user.get("email") or "",
        "summary": summary.strip() or "Uploaded file.",
        "file_name": file.filename or "upload",
        "file_mime": mime,
        "file_data": data_url,
    }
    result = insert_row("documents", row)
    if result.get("ok") is False:
        raise HTTPException(status_code=503, detail=result.get("error") or "Could not save the file")
    saved = result.get("row") or {}
    saved.pop("file_data", None)
    return {"ok": True, "row": saved}


@router.get("/messages/directory")
def message_directory(user=Depends(current_user)):
    _authorize("messages", user)
    result = _fail_if_down(list_rows("users", 500))
    items = []
    for row in result.get("items", []):
        if row.get("status") == "inactive":
            continue
        items.append({
            "id": row.get("id") or "",
            "name": row.get("name") or "",
            "email": row.get("email") or "",
            "role": row.get("role") or "",
            "department": row.get("department") or "",
            "phone": row.get("phone") or "",
        })
    items.sort(key=lambda item: item["name"].lower())
    return {"items": items, "total": len(items)}


@router.get("/documents/{doc_id}/file")
def document_file(doc_id: str, user=Depends(current_user)):
    _authorize("documents", user)
    row = get_row("documents", doc_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    if user.get("role") == "patient" and not _owns(row, user):
        raise HTTPException(status_code=403, detail="You can only open your own documents")
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    data = details.get("file_data") or ""
    if not data:
        raise HTTPException(status_code=404, detail="No file is stored for this document")
    return {
        "id": row.get("id"),
        "file_name": details.get("file_name") or row.get("title") or "document",
        "file_mime": details.get("file_mime") or "application/octet-stream",
        "file_data": data,
    }


@router.get("/messages/sent")
def sent_messages(user=Depends(current_user)):
    _authorize("messages", user)
    return _message_view(user, "sent")


def _clean_name(*parts) -> str:
    return " ".join(str(part or "").split())


def _remember_person(people: dict, row_id, name, phone, email) -> None:
    full = _clean_name(name)
    if not full:
        return
    mail = str(email or "").strip().lower()
    key = full.lower()
    first, _, last = full.partition(" ")
    current = people.get(key) or {}
    kept_id = str(current.get("id") or "")
    new_id = str(row_id or "")
    if kept_id.startswith("HC-") and new_id and not new_id.startswith("HC-"):
        new_id = kept_id
    people[key] = {
        "id": new_id or kept_id,
        "name": full,
        "first_name": first,
        "last_name": last,
        "phone": str(phone or current.get("phone") or ""),
        "email": mail or str(current.get("email") or ""),
    }


def _row_name(row: dict) -> str:
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    named = _clean_name(row.get("first_name"), row.get("last_name"))
    if named:
        return named
    for value in (row.get("name"), row.get("patient"), details.get("patient_name"), details.get("name")):
        cleaned = _clean_name(value)
        if cleaned:
            return cleaned
    return ""


def _absorb_saved_row(people: dict, row: dict, prefer_row_id: bool = False) -> None:
    if not isinstance(row, dict):
        return
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    name = _row_name(row)
    if not name:
        return
    linked = details.get("patient_id") or details.get("patientId") or row.get("patient_id") or ""
    row_id = row.get("id") if prefer_row_id else linked
    _remember_person(
        people,
        row_id,
        name,
        row.get("phone") or details.get("phone"),
        row.get("email") or details.get("email"),
    )


def _saved_name_rows(endpoint: str) -> list:
    """Same Supabase read the rest of the hospital uses. Never raises."""
    try:
        result = list_rows(endpoint, 500)
    except Exception as exc:  # noqa: BLE001
        log.error("name source %s failed: %s", endpoint, type(exc).__name__)
        return []
    if not isinstance(result, dict) or result.get("ok") is False:
        log.error("name source %s unavailable", endpoint)
        return []
    items = result.get("items") or []
    return items if isinstance(items, list) else []


@router.get("/patients/lookup")
def patient_lookup(user=Depends(current_user)):
    """Names already saved in Supabase, for invoice and form suggestions."""
    role = str(user.get("role") or "")
    if role not in {"admin", "manager", "doctor", "nurse", "pharmacist", "laboratory", "reception"}:
        raise HTTPException(status_code=403, detail="You do not have access to patient names")
    if get_client() is None:
        raise HTTPException(status_code=503, detail="Supabase is not configured")
    try:
        people = {}
        for row in _saved_name_rows("patients"):
            _absorb_saved_row(people, row, prefer_row_id=True)
        for row in _saved_name_rows("users"):
            if str(row.get("role") or "").lower() != "patient":
                continue
            _absorb_saved_row(people, row, prefer_row_id=not people)
        for endpoint in ("appointments", "cashier_invoices", "bills", "insurance"):
            for row in _saved_name_rows(endpoint):
                _absorb_saved_row(people, row, prefer_row_id=False)
        items = sorted(people.values(), key=lambda person: str(person.get("name") or "").lower())
        return {"ok": True, "items": items, "total": len(items), "source": "supabase"}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("patient lookup failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Could not read names from the hospital database") from exc


@router.get("/{resource}")
def read_all(resource: str, limit: int = 500, user=Depends(current_user)):
    _authorize(resource, user)
    if resource not in RESOURCES:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unknown resource")
    if resource == "messages":
        return _message_view(user, "inbox")
    result = _scope(resource, _fail_if_down(list_rows(resource, limit)), user)
    if resource == "announcements":
        items = [row for row in result.get("items", []) if str(row.get("id") or "") != "__permissions"]
        result = {**result, "items": items, "total": len(items)}
    return result


@router.post("/{resource}")
async def create(resource: str, request: Request, user=Depends(current_user)):
    _authorize(resource, user, write=True)
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    if resource == "documents" and len(str(body.get("file_data") or "")) > 1_800_000:
        raise HTTPException(status_code=413, detail="File is too large. Use a file under 1.2 MB.")
    if resource == "messages":
        body["from"] = user.get("name") or user.get("email") or ""
        body["from_role"] = user.get("role") or ""
        body["from_email"] = user.get("email") or ""
        body["read"] = False
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
    if resource == "appointments":
        body["patient"] = who
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
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    if resource == "users" and str(row_id) == str(user.get("sub")):
        body = {k: body[k] for k in ("name", "phone", "department", "details") if k in body}
        return _fail_if_down(update_row(resource, row_id, body))
    _authorize(resource, user, write=True)
    _assert_patient_owns(resource, row_id, user)
    return _fail_if_down(update_row(resource, row_id, _stamp_patient(resource, body, user)))


@router.delete("/{resource}/{row_id}")
def delete(resource: str, row_id: str, user=Depends(current_user)):
    _authorize(resource, user, write=True)
    if user["role"] == "patient":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="You cannot delete records")
    return _fail_if_down(delete_row(resource, row_id))

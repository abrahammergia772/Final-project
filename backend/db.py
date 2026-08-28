# =============================================================================
# Wolaita Sodo Hospital — backend/db.py
# Supabase (PostgreSQL) data layer. Every core-data endpoint reads/writes a
# Supabase table. If Supabase env vars are not set (or a call fails), it falls
# back to built-in demo data so the whole app still works end-to-end.
# =============================================================================
import logging
from typing import Any, Dict, List, Optional

from config import supabase_configured, SUPABASE_KEY, SUPABASE_SERVICE_KEY, SUPABASE_URL

log = logging.getLogger("mediq.db")

_client = None


def get_client():
    """Lazy Supabase client (anon key; service key preferred when provided)."""
    global _client
    if _client is None and supabase_configured():
        from supabase import create_client
        key = SUPABASE_SERVICE_KEY or SUPABASE_KEY
        _client = create_client(SUPABASE_URL, key)
    return _client


# ---------------------------------------------------------------------------
# Demo fallback data (mirrors the frontend mock library)
# ---------------------------------------------------------------------------
DEMO = {
    "users": [
        {"id": "U-001", "name": "Solomon Tadesse", "email": "admin@wsh.et", "role": "admin", "department": "Administration", "status": "active", "last_login": "2026-08-11T08:12:00"},
        {"id": "U-002", "name": "Hanna Bekele", "email": "manager@wsh.et", "role": "manager", "department": "Management", "status": "active", "last_login": "2026-08-11T07:55:00"},
        {"id": "U-003", "name": "Dr. Daniel Alemu", "email": "doctor@wsh.et", "role": "doctor", "department": "Internal Medicine", "status": "active", "last_login": "2026-08-11T07:40:00"},
        {"id": "U-004", "name": "Marta Tesfaye", "email": "nurse@wsh.et", "role": "nurse", "department": "General Ward", "status": "active", "last_login": "2026-08-11T06:58:00"},
        {"id": "U-005", "name": "Yonas Girma", "email": "pharmacist@wsh.et", "role": "pharmacist", "department": "Pharmacy", "status": "active", "last_login": "2026-08-11T07:20:00"},
        {"id": "U-006", "name": "Sara Worku", "email": "lab@wsh.et", "role": "laboratory", "department": "Laboratory", "status": "active", "last_login": "2026-08-11T07:10:00"},
        {"id": "U-007", "name": "Liya Hailu", "email": "reception@wsh.et", "role": "reception", "department": "Front Desk", "status": "active", "last_login": "2026-08-11T06:45:00"},
        {"id": "U-008", "name": "Abel Mekonnen", "email": "patient@wsh.et", "role": "patient", "department": "—", "status": "active", "last_login": "2026-08-10T18:30:00"},
    ],
    "patients": [
        {"id": "P-1001", "first_name": "Abel", "last_name": "Mekonnen", "age": 34, "gender": "Male", "phone": "+251 911 223 344", "email": "abel.m@mail.com", "blood": "O+", "address": "Sodo, Wolaita", "emergency": "+251 911 223 355", "condition": "Hypertension", "last_visit": "2026-08-05", "status": "active"},
        {"id": "P-1002", "first_name": "Hana", "last_name": "Wolde", "age": 28, "gender": "Female", "phone": "+251 912 334 455", "email": "hana.w@mail.com", "blood": "A+", "address": "Sodo, Wolaita", "emergency": "+251 912 334 466", "condition": "Diabetes Type 2", "last_visit": "2026-08-02", "status": "active"},
        {"id": "P-1003", "first_name": "Dawit", "last_name": "Kebede", "age": 45, "gender": "Male", "phone": "+251 913 445 566", "email": "dawit.k@mail.com", "blood": "B+", "address": "Boditi", "emergency": "+251 913 445 577", "condition": "Asthma", "last_visit": "2026-07-28", "status": "active"},
        {"id": "P-1004", "first_name": "Selam", "last_name": "Tadesse", "age": 62, "gender": "Female", "phone": "+251 914 556 677", "email": "selam.t@mail.com", "blood": "AB+", "address": "Areka", "emergency": "+251 914 556 688", "condition": "Heart Disease", "last_visit": "2026-08-09", "status": "active"},
        {"id": "P-1005", "first_name": "Biruk", "last_name": "Ayele", "age": 8, "gender": "Male", "phone": "+251 915 667 788", "email": "—", "blood": "O-", "address": "Sodo, Wolaita", "emergency": "+251 915 667 799", "condition": "Pneumonia (recovering)", "last_visit": "2026-08-07", "status": "active"},
        {"id": "P-1006", "first_name": "Ruth", "last_name": "Gebre", "age": 51, "gender": "Female", "phone": "+251 916 778 899", "email": "ruth.g@mail.com", "blood": "A-", "address": "Humbo", "emergency": "+251 916 778 800", "condition": "Chronic Kidney Disease", "last_visit": "2026-08-08", "status": "active"},
        {"id": "P-1007", "first_name": "Tewodros", "last_name": "Haile", "age": 39, "gender": "Male", "phone": "+251 917 889 900", "email": "tewodros.h@mail.com", "blood": "B-", "address": "Sodo, Wolaita", "emergency": "+251 917 889 911", "condition": "Thyroid Disorder", "last_visit": "2026-08-01", "status": "active"},
        {"id": "P-1008", "first_name": "Mahlet", "last_name": "Shiferaw", "age": 22, "gender": "Female", "phone": "+251 918 990 011", "email": "mahlet.s@mail.com", "blood": "O+", "address": "Sodo, Wolaita", "emergency": "+251 918 990 022", "condition": "—", "last_visit": "2026-07-30", "status": "active"},
        {"id": "P-1009", "first_name": "Yohannes", "last_name": "Mamo", "age": 58, "gender": "Male", "phone": "+251 919 001 122", "email": "yohannes.m@mail.com", "blood": "A+", "address": "Bilate", "emergency": "+251 919 001 133", "condition": "Diabetes + Hypertension", "last_visit": "2026-08-10", "status": "active"},
        {"id": "P-1010", "first_name": "Kidist", "last_name": "Assefa", "age": 30, "gender": "Female", "phone": "+251 910 112 233", "email": "kidist.a@mail.com", "blood": "B+", "address": "Sodo, Wolaita", "emergency": "+251 910 112 244", "condition": "Malaria (treated)", "last_visit": "2026-08-06", "status": "active"},
    ],
    "appointments": [
        {"id": "A-501", "patient": "Abel Mekonnen", "doctor": "Dr. Daniel Alemu", "dept": "Internal Medicine", "date": "2026-08-11", "time": "09:00", "type": "Follow-up", "status": "confirmed", "no_show": 12},
        {"id": "A-502", "patient": "Hana Wolde", "doctor": "Dr. Daniel Alemu", "dept": "Internal Medicine", "date": "2026-08-11", "time": "09:30", "type": "Consultation", "status": "confirmed", "no_show": 22},
        {"id": "A-503", "patient": "Dawit Kebede", "doctor": "Dr. Fikru Debebe", "dept": "Pediatrics", "date": "2026-08-11", "time": "10:00", "type": "Consultation", "status": "checked-in", "no_show": 8},
        {"id": "A-504", "patient": "Selam Tadesse", "doctor": "Dr. Meron Assefa", "dept": "Cardiology", "date": "2026-08-11", "time": "10:30", "type": "Follow-up", "status": "confirmed", "no_show": 18},
        {"id": "A-505", "patient": "Biruk Ayele", "doctor": "Dr. Fikru Debebe", "dept": "Pediatrics", "date": "2026-08-11", "time": "11:00", "type": "Consultation", "status": "completed", "no_show": 5},
    ],
    "inventory": [
        {"id": "I-001", "name": "Paracetamol 500mg", "category": "Analgesic", "stock": 850, "unit": "tablets", "expiry": "2027-02-15", "status": "in-stock"},
        {"id": "I-002", "name": "Amlodipine 5mg", "category": "Cardiovascular", "stock": 210, "unit": "tablets", "expiry": "2026-11-20", "status": "in-stock"},
        {"id": "I-003", "name": "Metformin 500mg", "category": "Antidiabetic", "stock": 74, "unit": "tablets", "expiry": "2026-12-01", "status": "low-stock"},
        {"id": "I-004", "name": "Insulin Glargine", "category": "Antidiabetic", "stock": 22, "unit": "vials", "expiry": "2026-09-30", "status": "low-stock"},
        {"id": "I-005", "name": "Amoxicillin 250mg", "category": "Antibiotic", "stock": 0, "unit": "capsules", "expiry": "2026-10-10", "status": "out-of-stock"},
        {"id": "I-006", "name": "Salbutamol Inhaler", "category": "Respiratory", "stock": 48, "unit": "units", "expiry": "2026-12-18", "status": "in-stock"},
    ],
    "prescriptions": [
        {"id": "RX-2201", "patient": "Abel Mekonnen", "doctor": "Dr. Daniel Alemu", "date": "2026-08-11", "drugs": [{"name": "Amlodipine 5mg", "dose": "1 tablet", "freq": "Once daily", "duration": "30 days"}], "status": "active"},
        {"id": "RX-2202", "patient": "Hana Wolde", "doctor": "Dr. Daniel Alemu", "date": "2026-08-11", "drugs": [{"name": "Metformin 500mg", "dose": "1 tablet", "freq": "Twice daily", "duration": "60 days"}], "status": "active"},
    ],
    "lab_results": [
        {"id": "R-901", "patient": "Biruk Ayele", "test": "Malaria Test", "date": "2026-08-10", "status": "normal", "ai_flag": "normal", "values": [{"name": "Malaria Antigen", "range": "Negative", "value": "Negative", "status": "normal"}]},
        {"id": "R-902", "patient": "Yohannes Mamo", "test": "HbA1c", "date": "2026-08-10", "status": "abnormal", "ai_flag": "abnormal", "values": [{"name": "HbA1c", "range": "4.0 – 5.6 %", "value": "8.2 %", "status": "abnormal"}]},
    ],
    "bills": [
        {"id": "B-701", "date": "2026-08-05", "description": "Consultation — Internal Medicine", "amount": 350, "status": "paid"},
        {"id": "B-702", "date": "2026-08-06", "description": "Amlodipine 5mg ×30 tablets", "amount": 180, "status": "pending"},
        {"id": "B-703", "date": "2026-08-09", "description": "Inpatient ward — 2 nights (General)", "amount": 1600, "status": "overdue"},
    ],
    "complaints": [
        {"id": "CMP-101", "reporter": "Abel Mekonnen", "reporter_role": "patient", "category": "Billing", "subject": "Incorrect charge on my invoice", "description": "Charged 500 ETB for an ECG not performed.", "priority": "high", "date": "2026-08-10T09:30:00", "status": "resolved", "solution": "Refunded.", "resolved_by": "Hanna Bekele", "resolved_date": "2026-08-11T08:00:00"},
        {"id": "CMP-102", "reporter": "Abel Mekonnen", "reporter_role": "patient", "category": "Service Quality", "subject": "Long waiting time at OPD", "description": "Waited over 2 hours despite a confirmed appointment.", "priority": "normal", "date": "2026-08-09T14:00:00", "status": "in-review", "solution": ""},
    ],
    "messages": [
        {"id": "MSG-1001", "from": "Dr. Daniel Alemu", "from_role": "Doctor", "subject": "Lab result follow-up", "body": "HbA1c for Yohannes Mamo came back at 8.2%.", "date": "2026-08-11T08:40:00", "read": False, "priority": "high", "replies": []},
        {"id": "MSG-1002", "from": "Front Desk (Reception)", "from_role": "Reception", "subject": "Appointment reminder", "body": "3 patients are checked in and waiting.", "date": "2026-08-11T08:15:00", "read": False, "priority": "normal", "replies": []},
    ],
    "medications": [
        {"id": "M-01", "patient": "Selam Tadesse", "drug": "Atorvastatin 20mg", "dose": "1 tablet", "due": "08:00", "status": "administered", "time": "07:58"},
        {"id": "M-02", "patient": "Abel Mekonnen", "drug": "Amlodipine 5mg", "dose": "1 tablet", "due": "08:00", "status": "administered", "time": "08:05"},
        {"id": "M-03", "patient": "Yohannes Mamo", "drug": "Insulin Glargine", "dose": "20 units", "due": "09:00", "status": "pending", "time": ""},
    ],
    "announcements": [
        {"id": "AN-1", "title": "Emergency: Generator maintenance Friday 22:00", "message": "Generator serviced Friday 22:00–23:30.", "audience": "All staff", "author": "Solomon Tadesse", "publish_date": "2026-08-11T08:00:00", "priority": "urgent", "status": "published", "views": 132},
    ],
    "departments": [
        {"id": "D-01", "name": "Internal Medicine", "head": "Dr. Daniel Alemu", "staff": 18, "beds": 42, "occupied": 35, "status": "active"},
        {"id": "D-02", "name": "Pediatrics", "head": "Dr. Fikru Debebe", "staff": 14, "beds": 30, "occupied": 21, "status": "active"},
        {"id": "D-03", "name": "Cardiology", "head": "Dr. Meron Assefa", "staff": 10, "beds": 20, "occupied": 17, "status": "active"},
    ],
    "staff": [
        {"id": "S-001", "name": "Dr. Daniel Alemu", "role": "Doctor", "dept": "Internal Medicine", "shift": "Morning", "status": "present", "contact": "+251 911 100 001"},
        {"id": "S-002", "name": "Marta Tesfaye", "role": "Nurse", "dept": "General Ward", "shift": "Morning", "status": "present", "contact": "+251 911 100 004"},
        {"id": "S-003", "name": "Yonas Girma", "role": "Pharmacist", "dept": "Pharmacy", "shift": "Morning", "status": "present", "contact": "+251 911 100 006"},
    ],
    "audit_logs": [
        {"id": "AL-1", "ts": "2026-08-11T08:12:00", "user": "Solomon Tadesse", "role": "admin", "action": "login", "ip": "196.188.24.10", "status": "success"},
        {"id": "AL-2", "ts": "2026-08-11T08:05:00", "user": "Dr. Daniel Alemu", "role": "doctor", "action": "create", "ip": "196.188.24.45", "status": "success", "detail": "Created prescription RX-2201"},
    ],
    "insurance": [
        {"id": "IN-1", "patient": "Abel Mekonnen", "provider": "EHBPA", "policy": "EHB-2026-4412", "coverage": 80, "valid_until": "2027-03-15", "status": "verified"},
    ],
    "samples": [
        {"id": "S-801", "patient": "Abel Mekonnen", "test": "Complete Blood Count", "type": "Whole blood", "collected": "08:10", "stage": "completed", "tat": "2.8 h"},
        {"id": "S-802", "patient": "Hana Wolde", "test": "Fasting Blood Sugar", "type": "Serum", "collected": "08:25", "stage": "result-ready", "tat": "—"},
    ],
    "documents": [
        {"id": "DOC-1", "patient": "Abel Mekonnen", "patient_id": "P-1001", "type": "Lab Report", "title": "Complete Blood Count — 05/08", "date": "2026-08-05", "size": "214 KB", "uploaded_by": "Sara Worku", "summary": "All CBC parameters within normal limits."},
        {"id": "DOC-2", "patient": "Abel Mekonnen", "patient_id": "P-1001", "type": "Prescription", "title": "Prescription RX-2201 — Amlodipine", "date": "2026-08-11", "size": "86 KB", "uploaded_by": "Dr. Daniel Alemu", "summary": "Amlodipine 5mg once daily × 30 days."},
    ],
    "lab_requests": [
        {"id": "LR-331", "patient": "Abel Mekonnen", "test": "Complete Blood Count", "doctor": "Dr. Daniel Alemu", "date": "2026-08-11", "priority": "Routine", "status": "pending"},
    ],
    "care_plans": [
        {"id": "CP-1", "patient": "Selam Tadesse", "plan": "Post-MI cardiac rehab", "created": "2026-08-02", "updated": "2026-08-10", "status": "in-progress", "steps": ["Daily ECG monitoring", "Physiotherapy: 30 min/day"]},
    ],
    "queue": [
        {"id": "Q-1", "name": "Mahlet Shiferaw", "dept": "Internal Medicine", "arrived": "08:10", "status": "in-service"},
        {"id": "Q-2", "name": "Kidist Assefa", "dept": "Cardiology", "arrived": "08:15", "status": "waiting"},
    ],
    "shifts": [
        {"id": "SH-1", "name": "Morning", "start": "07:00", "end": "15:00", "color": "#1A56DB", "css": "morning", "workers": 34},
        {"id": "SH-2", "name": "Evening", "start": "15:00", "end": "23:00", "color": "#D97706", "css": "evening", "workers": 22},
    ],
    "roster": [
        {"id": "RO-1", "staff": "Dr. Daniel Alemu", "dept": "Internal Medicine", "date": "2026-08-11", "shift": "Morning", "start": "07:00", "end": "15:00"},
    ],
    "attendance": [
        {"id": "AT-1", "staff": "Dr. Daniel Alemu", "dept": "Internal Medicine", "date": "2026-08-11", "shift": "Morning", "check_in": "06:52", "check_out": None, "status": "present", "source": "fingerprint", "device": "FP-01"},
    ],
    "observations": [],
    "referrals": [],
    "suppliers": [],
    "purchase_orders": [],
    "videos": [],
    "notifications": [],
}

# endpoint path -> table name (Supabase) and demo key
TABLES = {
    "users": "users", "patients": "patients", "appointments": "appointments",
    "prescriptions": "prescriptions", "inventory": "inventory",
    "lab_requests": "lab_requests", "lab_results": "lab_results",
    "medications": "medications", "care_plans": "care_plans", "bills": "bills",
    "audit_logs": "audit_logs", "queue": "queue", "announcements": "announcements",
    "departments": "departments", "staff": "staff", "insurance": "insurance",
    "samples": "samples", "documents": "documents", "complaints": "complaints",
    "messages": "messages", "shifts": "shifts", "roster": "roster",
    "attendance": "attendance", "observations": "observations",
    "referrals": "referrals", "suppliers": "suppliers",
    "purchase_orders": "purchase_orders",
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def list_rows(endpoint: str, limit: int = 500) -> Dict[str, Any]:
    """GET /<endpoint> → {items:[...], total:n} — Supabase table or demo."""
    table = TABLES.get(endpoint, endpoint)
    client = get_client()
    if client is not None:
        try:
            resp = client.table(table).select("*").limit(limit).execute()
            items = resp.data or []
            if endpoint == "users":
                for item in items:
                    item.pop("password_hash", None)
            return {"items": items, "total": len(items), "source": "supabase"}
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase read %s failed: %s → demo", endpoint, exc)
    items = DEMO.get(endpoint, [])
    return {"items": items, "total": len(items), "source": "demo"}


def insert_row(endpoint: str, data: dict) -> Dict[str, Any]:
    table = TABLES.get(endpoint, endpoint)
    client = get_client()
    if client is not None:
        try:
            resp = client.table(table).insert(data).execute()
            return {"ok": True, "row": (resp.data or [{}])[0], "source": "supabase"}
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase insert %s failed: %s → demo", endpoint, exc)
    import uuid
    row = dict(data)
    row.setdefault("id", endpoint.upper() + "-" + str(uuid.uuid4())[:8])
    DEMO.setdefault(endpoint, []).insert(0, row)
    return {"ok": True, "row": row, "source": "demo"}


def update_row(endpoint: str, row_id: str, data: dict) -> Dict[str, Any]:
    table = TABLES.get(endpoint, endpoint)
    client = get_client()
    if client is not None:
        try:
            resp = client.table(table).update(data).eq("id", row_id).execute()
            return {"ok": True, "row": (resp.data or [{}])[0], "source": "supabase"}
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase update %s failed: %s → demo", endpoint, exc)
    rows = DEMO.setdefault(endpoint, [])
    for r in rows:
        if r.get("id") == row_id:
            r.update(data)
            return {"ok": True, "row": r, "source": "demo"}
    return {"ok": False, "error": "not found"}


def delete_row(endpoint: str, row_id: str) -> Dict[str, Any]:
    table = TABLES.get(endpoint, endpoint)
    client = get_client()
    if client is not None:
        try:
            client.table(table).delete().eq("id", row_id).execute()
            return {"ok": True, "source": "supabase"}
        except Exception as exc:  # noqa: BLE001
            log.warning("supabase delete %s failed: %s → demo", endpoint, exc)
    rows = DEMO.setdefault(endpoint, [])
    DEMO[endpoint] = [r for r in rows if r.get("id") != row_id]
    return {"ok": True, "source": "demo"}

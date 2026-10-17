# =============================================================================
# Wolaita Sodo Hospital — routers/appointment.py
# Appointment help uses Groq plus the hospital's saved rows.
# There is no trained appointment model.
# =============================================================================
import logging
import os
import secrets
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import insert_row, list_rows, update_row
from groq_client import ask_json, configured as groq_configured
from security import current_user
from sms import mask_phone, normalize_phone, send_sms

router = APIRouter(tags=["AI · Appointment"])
log = logging.getLogger("mediq.appointment")

STAFF = {"admin", "manager", "doctor", "reception", "nurse"}
DOCTORS = ["Dr. Daniel Alemu", "Dr. Fikru Debebe", "Dr. Meron Assefa", "Dr. Tsehay Mengistu"]
DEPARTMENTS = ["Internal Medicine", "Pediatrics", "Cardiology", "Maternity", "Orthopedics"]
HOURS = ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
         "14:00", "14:30", "15:00", "15:30"]


class ScheduleBody(BaseModel):
    patient: str = ""
    department: str = ""
    doctor: str = ""
    reason: str = ""
    urgency: str = "routine"
    book: bool = False
    slot_id: str = ""


class NamedBody(BaseModel):
    patient: str = ""
    reason: str = ""
    department: str = ""
    doctor: str = ""


class ReminderBody(BaseModel):
    days: int = 3
    appointment_id: str = ""
    all_upcoming: bool = False


class AppointmentRequest(BaseModel):
    patient: str = ""
    patient_age: int | None = None
    appointment_date: str = ""
    appointment_time: str = "09:00"
    department: str = ""
    doctor_id: str = ""
    appointment_type: str = ""
    prev_no_shows: int = 0
    prev_visits: int = 0


def _role(user) -> str:
    return str((user or {}).get("role") or "").lower()


def _staff(user) -> None:
    if _role(user) not in STAFF:
        raise HTTPException(status_code=403, detail="Only hospital staff can do that")


def _rows(resource: str) -> list:
    result = list_rows(resource, 500)
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail=result.get("error") or "Database unavailable")
    return result.get("items") or []


def _name(value) -> str:
    return " ".join(str(value or "").split()).strip()


def _same(left, right) -> bool:
    a = _name(left).lower()
    b = _name(right).lower()
    return bool(a and b and (a == b or a in b or b in a))


def _open(row) -> bool:
    return str(row.get("status") or "").lower() not in {"cancelled", "completed", "attended"}


def _clock(value) -> str:
    text = str(value or "")[:5]
    return text if len(text) == 5 else "09:00"


def _iso(day: date) -> str:
    return day.isoformat()


def open_slots(rows: list, doctor: str = "", department: str = "", start: date | None = None, days: int = 8) -> list:
    """Open weekday slots that are not already booked for that doctor."""
    start = start or date.today()
    doctor = _name(doctor)
    taken = set()
    for row in rows:
        if not _open(row):
            continue
        if doctor and not _same(row.get("doctor"), doctor):
            continue
        taken.add((str(row.get("date") or "")[:10], _clock(row.get("time")), _name(row.get("doctor")).lower()))
    found = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        who = doctor or DOCTORS[0]
        for hour in HOURS:
            if (day.isoformat(), hour, who.lower()) in taken:
                continue
            found.append({
                "id": day.isoformat() + "|" + hour + "|" + who,
                "date": day.isoformat(),
                "time": hour,
                "doctor": who,
                "department": department or "",
            })
            if len(found) >= 12:
                return found
    return found


def risk_from_history(rows: list, patient: str, today: date | None = None) -> dict:
    """No-show estimate from saved visits only. Unknown when there is no history."""
    today = today or date.today()
    mine = [row for row in rows if _same(row.get("patient"), patient)]
    past = []
    for row in mine:
        try:
            when = date.fromisoformat(str(row.get("date") or "")[:10])
        except ValueError:
            continue
        status = str(row.get("status") or "").lower()
        if when < today or status in {"cancelled", "completed", "attended", "no-show", "noshow"}:
            past.append(row)
    if not past:
        return {
            "no_show_percent": None,
            "risk_level": "Unknown",
            "show_prediction": "Not scored",
            "past_visits": 0,
            "missed_visits": 0,
            "source": "no-history",
        }
    missed = [row for row in past if str(row.get("status") or "").lower() in {"cancelled", "no-show", "noshow"}]
    pct = round(100 * len(missed) / len(past), 1)
    if pct >= 50:
        risk = "High"
    elif pct >= 25:
        risk = "Medium"
    else:
        risk = "Low"
    return {
        "no_show_percent": pct,
        "risk_level": risk,
        "show_prediction": "May miss the visit" if pct >= 40 else "Likely to attend",
        "past_visits": len(past),
        "missed_visits": len(missed),
        "source": "hospital-records",
    }


def choose_gap(rows: list, freed: dict) -> dict | None:
    """Pick one later confirmed visit that can take a cancelled slot."""
    doctor = _name(freed.get("doctor"))
    freed_key = (str(freed.get("date") or "")[:10], _clock(freed.get("time")))
    choices = []
    for row in rows:
        if str(row.get("id")) == str(freed.get("id")) or not _open(row):
            continue
        if doctor and not _same(row.get("doctor"), doctor):
            continue
        key = (str(row.get("date") or "")[:10], _clock(row.get("time")))
        if key <= freed_key:
            continue
        choices.append(row)
    choices.sort(key=lambda row: (str(row.get("date") or ""), _clock(row.get("time"))))
    return choices[0] if choices else None


def _patient_row(rows: list, name: str) -> dict:
    return next((row for row in rows if _same(row.get("name") or ((row.get("first_name") or "") + " " + (row.get("last_name") or "")), name) or _same(row.get("patient"), name)), {})


def _account_phone(user: dict, users: list) -> str:
    email = str(user.get("email") or "").strip().lower()
    uid = str(user.get("sub") or user.get("id") or "")
    name = str(user.get("name") or "")
    for row in users:
        matched = (uid and str(row.get("id") or "") == uid) or (email and str(row.get("email") or "").strip().lower() == email) or (name and _same(row.get("name"), name))
        if not matched:
            continue
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        for raw in (row.get("phone"), details.get("phone")):
            number = normalize_phone(raw)
            if number:
                return number
    return ""


def _phone_for(name: str, appointment: dict, patients: list, users: list) -> str:
    details = appointment.get("details") if isinstance(appointment.get("details"), dict) else {}
    person = _patient_row(patients, name)
    person_details = person.get("details") if isinstance(person.get("details"), dict) else {}
    user = next((row for row in users if _same(row.get("name"), name)), {})
    user_details = user.get("details") if isinstance(user.get("details"), dict) else {}
    for raw in (
        appointment.get("phone"),
        details.get("phone"),
        person.get("phone"),
        person_details.get("phone"),
        user.get("phone"),
        user_details.get("phone"),
    ):
        number = normalize_phone(raw)
        if number:
            return number
    return ""


def _facts_for(name: str) -> dict:
    appointments = [row for row in _rows("appointments") if _same(row.get("patient"), name)]
    prescriptions = [row for row in _rows("prescriptions") if _same(row.get("patient"), name)]
    labs = [row for row in _rows("lab_results") if _same(row.get("patient"), name)]
    medications = [row for row in _rows("medications") if _same(row.get("patient"), name)]
    people = _rows("patients")
    person = _patient_row(people, name)
    return {
        "appointments": appointments[:12],
        "prescriptions": prescriptions[:8],
        "labs": labs[:8],
        "medications": medications[:8],
        "person": {k: person.get(k) for k in ("first_name", "last_name", "age", "gender", "blood", "phone", "email", "condition", "last_visit") if person.get(k)},
    }


def _clip(rows: list, keys: tuple) -> list:
    out = []
    for row in rows[:8]:
        out.append({key: row.get(key) for key in keys if row.get(key) not in (None, "", [])})
    return out


def _save_message(patient: str, subject: str, body: str, kind: str) -> bool:
    row = {
        "id": "M-" + secrets.token_hex(4),
        "from": "Wolaita Sodo Hospital",
        "from_role": "reception",
        "subject": subject[:120],
        "body": body[:1200],
        "date": date.today().isoformat(),
        "read": False,
        "priority": "normal",
        "to": patient,
        "kind": kind,
    }
    saved = insert_row("messages", row)
    return bool(saved.get("ok"))


def _groq_note(system: str, facts: str) -> tuple:
    if not groq_configured():
        return "", "missing-key"
    parsed, source = ask_json(system, facts, 500)
    note = str(parsed.get("note") or parsed.get("summary") or "").strip()
    return note[:800], source


@router.post("/ai/predict-appointment")
def predict_appointment(req: AppointmentRequest, user=Depends(current_user)):
    rows = _rows("appointments")
    risk = risk_from_history(rows, req.patient or req.doctor_id)
    if req.prev_no_shows and risk["source"] == "no-history":
        total = max(req.prev_visits + req.prev_no_shows, 1)
        pct = round(100 * req.prev_no_shows / total, 1)
        risk = {
            "no_show_percent": pct,
            "risk_level": "High" if pct >= 50 else "Medium" if pct >= 25 else "Low",
            "show_prediction": "May miss the visit" if pct >= 40 else "Likely to attend",
            "past_visits": req.prev_visits,
            "missed_visits": req.prev_no_shows,
            "source": "request-history",
        }
    reminder = "Send a hospital message the day before."
    if risk["risk_level"] == "High":
        reminder = "Send a hospital message two days before and again the day before."
    elif risk["risk_level"] == "Unknown":
        reminder = "There is no saved visit history, so no risk percent is shown."
    return {
        **risk,
        "best_reminder_timing": reminder,
        "model": "groq-appointment",
        "model_version": "groq",
        "sms": "not-connected",
        "explanation": reminder,
        "explained_by": "hospital-records",
    }


@router.post("/ai/appointment/schedule")
def schedule(body: ScheduleBody, user=Depends(current_user)):
    _staff(user)
    patient = _name(body.patient)
    if not patient:
        raise HTTPException(status_code=400, detail="Type the patient name")
    department = body.department if body.department in DEPARTMENTS else (body.department or DEPARTMENTS[0])
    doctor = _name(body.doctor)
    if not doctor:
        raise HTTPException(status_code=400, detail="Choose a saved doctor")
    rows = _rows("appointments")
    slots = open_slots(rows, doctor, department)
    risk = risk_from_history(rows, patient)
    if not slots:
        return {"slots": [], "summary": "No open weekday slot was found in the next 8 days.", "risk": risk, "model": "groq-appointment", "explained_by": "hospital-records"}
    picked = next((item for item in slots if item["id"] == body.slot_id), None) if body.slot_id else None
    if body.slot_id and not picked:
        return {"slots": [], "summary": "That slot is no longer open.", "risk": risk, "model": "groq-appointment", "explained_by": "hospital-records"}
    if picked:
        chosen = [picked]
        note = "Selected slot from the hospital calendar."
        source = "selected-slot"
        booked = None
        if body.book:
            row = {
                "id": "A-" + secrets.token_hex(4),
                "patient": patient,
                "doctor": picked["doctor"],
                "dept": department,
                "date": picked["date"],
                "time": picked["time"],
                "type": "Consultation",
                "status": "confirmed",
                "no_show": risk.get("no_show_percent"),
                "reason": body.reason[:180],
            }
            saved = insert_row("appointments", row)
            booked = row if saved.get("ok") else None
            if not saved.get("ok"):
                note = saved.get("error") or "The slot was not saved."
        return {
            "slots": chosen,
            "summary": note,
            "explained_by": source,
            "risk": risk,
            "booked": booked,
            "model": "groq-appointment",
            "sms": "not-connected",
        }
    parsed, source = ask_json(
        "You schedule visits at Wolaita Sodo Hospital. Return JSON with keys note and chosen_ids. "
        "chosen_ids must be copied from the given ids. Do not invent a patient, doctor, time, or diagnosis.",
        "Past visits: " + str(risk["past_visits"]) + ". Missed visits: " + str(risk["missed_visits"])
        + ". Urgency: " + (body.urgency or "routine") + ". Reason: " + (body.reason or "not stated")[:300]
        + ". Open slot ids: " + ", ".join(item["id"] for item in slots),
        400,
    ) if groq_configured() else ({}, "missing-key")
    note = str(parsed.get("note") or "").strip()[:800]
    parsed_ids = parsed.get("chosen_ids") if isinstance(parsed.get("chosen_ids"), list) else []
    allowed = {item["id"]: item for item in slots}
    chosen = []
    for item in parsed_ids:
        if item in allowed and allowed[item] not in chosen:
            chosen.append(allowed[item])
    if not chosen:
        chosen = slots[:3]
    booked = None
    if body.book and chosen:
        slot = chosen[0]
        row = {
            "id": "A-" + secrets.token_hex(4),
            "patient": patient,
            "doctor": slot["doctor"],
            "dept": department,
            "date": slot["date"],
            "time": slot["time"],
            "type": "Consultation",
            "status": "confirmed",
            "no_show": risk.get("no_show_percent"),
            "reason": body.reason[:180],
        }
        saved = insert_row("appointments", row)
        booked = row if saved.get("ok") else None
    summary = note or ("Suggested " + str(len(chosen)) + " open slots from the hospital calendar.")
    return {
        "slots": chosen,
        "summary": summary,
        "explained_by": source or "hospital-records",
        "risk": risk,
        "booked": booked,
        "model": "groq-appointment",
        "sms": "not-connected",
    }


@router.post("/ai/appointment/reminders")
def reminders(body: ReminderBody, user=Depends(current_user)):
    _staff(user)
    today = date.today()
    window = max(1, min(int(body.days or 3), 7))
    wanted = str(body.appointment_id or "").strip()
    span = 30 if (body.all_upcoming or wanted) else window
    rows = _rows("appointments")
    patients = _rows("patients")
    users = _rows("users")
    sent = []
    sms_sent = 0
    sms_failed = 0
    seen = False
    for row in rows:
        if wanted and str(row.get("id")) != wanted:
            continue
        if wanted:
            seen = True
        if not _open(row):
            continue
        try:
            when = date.fromisoformat(str(row.get("date") or "")[:10])
        except ValueError:
            continue
        ahead = (when - today).days
        if ahead < 0 or ahead > span:
            continue
        risk = risk_from_history(rows, row.get("patient") or "")
        early = risk["missed_visits"] > 0
        if not wanted and not body.all_upcoming and ahead > (2 if early else 1):
            continue
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        already = str(details.get("reminded_on") or "") == today.isoformat()
        if not wanted and already and str(details.get("sms") or "") == "sent":
            continue
        patient = _name(row.get("patient"))
        when_text = "two days before" if early else "the day before"
        phone = _phone_for(patient, row, patients, users)
        sms_text = (
            "Wolaita Sodo Hospital reminder: " + str(row.get("dept") or "your visit")
            + " with " + str(row.get("doctor") or "the hospital")
            + " on " + str(row.get("date") or "") + " at " + _clock(row.get("time"))
            + ". Please arrive on time."
        )
        result = send_sms(phone, sms_text)
        where = mask_phone(result.get("number") or phone)
        staff_number = _account_phone(user, users)
        staff_result = None
        if staff_number and staff_number != (result.get("number") or normalize_phone(phone)):
            staff_result = send_sms(staff_number, sms_text)
        alert_number = normalize_phone(os.getenv("STAFF_ALERT_PHONE", ""))
        alert_result = None
        if alert_number and alert_number not in {result.get("number") or "", staff_number or ""}:
            alert_result = send_sms(alert_number, "STAFF ALERT: " + patient + " on " + str(row.get("date") or "") + " at " + _clock(row.get("time")) + ". " + str(row.get("dept") or ""))
        def sms_label(item, empty):
            if not item:
                return empty
            if item.get("ok"):
                return "accepted for " + mask_phone(item.get("number") or "", "number")
            if item.get("status") == "no-phone":
                return empty
            return "not accepted: " + str(item.get("detail") or "failed")
        patient_sms = sms_label(result, "no phone saved")
        staff_pick = next((item for item in (staff_result, alert_result) if item and item.get("ok")), None) or staff_result or alert_result
        staff_sms = sms_label(staff_pick, "no staff phone")
        if result.get("ok"):
            note = "Africa's Talking accepted the patient SMS for " + where + ". That is not proof the handset has received it."
        else:
            note = patient_sms
        if staff_sms not in {"no staff phone"}:
            note += " Staff SMS: " + staff_sms + "."
        text = (
            "Reminder for " + patient + ": " + str(row.get("dept") or "your visit")
            + " with " + str(row.get("doctor") or "the hospital")
            + " on " + str(row.get("date") or "") + " at " + _clock(row.get("time"))
            + ". This reminder is " + when_text + " because "
            + ("earlier visits were missed." if early else "the visit is soon.")
            + " " + note
        )
        if not already and not _save_message(patient, "Appointment reminder", text, "reminder"):
            continue
        update_row("appointments", str(row.get("id")), {"details": {
            "reminded_on": today.isoformat(),
            "reminder": when_text,
            "sms": "sent" if result.get("ok") else str(result.get("status") or "failed"),
        }})
        if result.get("ok"):
            sms_sent += 1
        elif result.get("status") != "no-phone":
            sms_failed += 1
        sent.append({
            "patient": patient,
            "date": row.get("date"),
            "time": _clock(row.get("time")),
            "early": early,
            "sms": "accepted" if result.get("ok") else str(result.get("status") or "failed"),
            "patient_sms": patient_sms,
            "staff_sms": staff_sms,
            "note": note,
        })
    if wanted and not seen:
        summary = "That appointment was not found."
    elif not sent:
        summary = "No upcoming visit needed a new reminder."
    else:
        label = "reminder message" if len(sent) == 1 else "reminder messages"
        accepted = [str(item.get("note") or "") for item in sent if item.get("sms") == "sent" and item.get("note")]
        summary = "Saved " + str(len(sent)) + " " + label + "."
        if accepted:
            summary += " " + " ".join(accepted[:1])
        else:
            summary += " Africa's Talking accepted " + str(sms_sent) + " SMS."
        reasons = [str(item.get("note") or "") for item in sent if item.get("sms") != "sent" and item.get("note")]
        if sms_failed:
            summary += " " + str(sms_failed) + " SMS could not be sent."
            if reasons:
                summary += " " + " ".join(reasons[:2])
        elif not sms_sent:
            summary += " No SMS was sent."
            if reasons:
                summary += " " + " ".join(reasons[:2])
    return {
        "sent": sent,
        "total": len(sent),
        "sms": "sent" if sms_sent and not sms_failed else ("partial" if sms_sent else "not-sent"),
        "sms_sent": sms_sent,
        "email": "not-sent",
        "summary": summary,
        "model": "groq-appointment",
    }


@router.post("/ai/appointment/prescreen")
def prescreen(body: NamedBody, user=Depends(current_user)):
    if _role(user) == "patient":
        body.patient = user.get("name") or user.get("email") or ""
    elif _role(user) not in STAFF:
        raise HTTPException(status_code=403, detail="You cannot open this form")
    patient = _name(body.patient)
    if not patient:
        raise HTTPException(status_code=400, detail="Type the patient name")
    facts = _facts_for(patient)
    known = facts["person"]
    previous = _clip(facts["appointments"], ("date", "dept", "doctor", "type", "status"))
    note, source = _groq_note(
        "Write an intake form for Wolaita Sodo Hospital. Return JSON with keys note and questions. "
        "questions is a list of short question strings. Do not invent answers, allergies, diagnoses, or doses. "
        "Use the reason for the visit. Say when a fact is not in the record.",
        "Reason: " + (body.reason or "not stated")[:400] + ". Known record fields: " + str(known) + ". Previous visits: " + str(previous),
    )
    questions = [
        "What is the reason for this visit?",
        "When did this problem start?",
        "Do you have pain, fever, or trouble breathing today?",
        "Which medicines are you taking now?",
    ]
    if source == "groq":
        parsed, _ = ask_json(
            "Return JSON with key questions, a list of 4 short intake questions. Do not include answers.",
            "Reason: " + (body.reason or "general visit")[:300],
            300,
        )
        got = parsed.get("questions") if isinstance(parsed.get("questions"), list) else []
        clean = [str(item).strip()[:160] for item in got if str(item).strip()]
        if clean:
            questions = clean[:6]
    return {
        "patient": patient,
        "prefilled": known,
        "previous_visits": previous,
        "questions": questions,
        "summary": note or "Intake questions are ready. Answers are not invented.",
        "explained_by": source or "hospital-records",
        "model": "groq-appointment",
    }


@router.post("/ai/appointment/doctor-brief")
def doctor_brief(body: NamedBody, user=Depends(current_user)):
    if _role(user) not in {"admin", "manager", "doctor", "nurse"}:
        raise HTTPException(status_code=403, detail="Only a clinician can open this brief")
    patient = _name(body.patient)
    if not patient:
        raise HTTPException(status_code=400, detail="Type the patient name")
    facts = _facts_for(patient)
    visits = _clip(facts["appointments"], ("date", "time", "dept", "doctor", "type", "status"))
    drugs = _clip(facts["medications"], ("drug", "dose", "status", "due"))
    labs = _clip(facts["labs"], ("test", "date", "status", "ai_flag"))
    missed = sum(1 for row in facts["appointments"] if str(row.get("status") or "").lower() in {"cancelled", "no-show", "noshow"})
    flags = []
    if not visits and not drugs and not labs:
        flags.append("No saved visits, medicines, or lab results for this name.")
    if missed:
        flags.append(str(missed) + " saved visit(s) were cancelled or missed.")
    note, source = _groq_note(
        "Summarize a hospital chart for a doctor at Wolaita Sodo Hospital. Return JSON with key note. "
        "Use only the facts. If a fact is missing, say it is not in the record. Do not diagnose. Do not give a new drug dose.",
        "Patient: " + patient + ". Flags: " + "; ".join(flags) + ". Visits: " + str(visits) + ". Medicines: " + str(drugs) + ". Labs: " + str(labs),
    )
    summary = note or ("Saved visits: " + str(len(visits)) + ". Saved medicines: " + str(len(drugs)) + ". Saved labs: " + str(len(labs)) + ".")
    return {
        "patient": patient,
        "flags": flags,
        "visits": visits,
        "medicines": drugs,
        "labs": labs,
        "summary": summary,
        "explained_by": source or "hospital-records",
        "model": "groq-appointment",
    }


@router.post("/ai/appointment/follow-up")
def follow_up(body: NamedBody, user=Depends(current_user)):
    _staff(user)
    today = date.today()
    rows = _rows("appointments")
    targets = []
    for row in rows:
        status = str(row.get("status") or "").lower()
        if status not in {"completed", "attended"}:
            continue
        try:
            when = date.fromisoformat(str(row.get("date") or "")[:10])
        except ValueError:
            continue
        if (today - when).days > 14 or when > today:
            continue
        later = [item for item in rows if _same(item.get("patient"), row.get("patient")) and _open(item) and str(item.get("date") or "") > str(row.get("date") or "")]
        if later:
            continue
        targets.append(row)
    if body.patient:
        targets = [row for row in targets if _same(row.get("patient"), body.patient)]
    sent = []
    medicines = _rows("medications")
    for row in targets[:8]:
        patient = _name(row.get("patient"))
        meds = [item for item in medicines if _same(item.get("patient"), patient)]
        med_line = ""
        if meds and meds[0].get("drug"):
            med_line = " Your saved medicine record lists " + str(meds[0].get("drug")) + "."
        text = (
            "Follow-up for " + patient + " after the " + str(row.get("date") or "")
            + " " + str(row.get("dept") or "visit") + ". No later open visit is saved."
            + med_line + " Please tell reception if you need another visit. This is not a diagnosis."
        )
        if _save_message(patient, "Follow-up check", text, "follow-up"):
            sent.append({"patient": patient, "date": row.get("date"), "needs_follow_up": True})
    return {
        "flagged": sent,
        "total": len(sent),
        "sms": "not-connected",
        "email": "not-sent",
        "summary": "Flagged " + str(len(sent)) + " completed visits with no later booking. Messages were saved. No SMS was sent.",
        "model": "groq-appointment",
    }


def fill_cancelled_slot(freed: dict) -> dict:
    """Move one later visit into a slot that was just cancelled. Never invents a patient."""
    try:
        when = date.fromisoformat(str(freed.get("date") or "")[:10])
    except ValueError:
        return {"moved": False, "reason": "The cancelled visit has no date."}
    if when < date.today():
        return {"moved": False, "reason": "The cancelled visit is in the past, so no one was moved."}
    rows = _rows("appointments")
    chosen = choose_gap(rows, freed)
    if not chosen:
        return {"moved": False, "reason": "No later visit with the same doctor can take this slot."}
    update_row("appointments", str(chosen.get("id")), {
        "date": str(freed.get("date") or "")[:10],
        "time": _clock(freed.get("time")),
        "details": {
            "moved_from": str(chosen.get("date") or "")[:10] + " " + _clock(chosen.get("time")),
            "moved_reason": "earlier slot opened after a cancellation",
        },
    })
    patient = _name(chosen.get("patient"))
    text = (
        "Your visit with " + str(chosen.get("doctor") or "the hospital")
        + " moved from " + str(chosen.get("date") or "") + " " + _clock(chosen.get("time"))
        + " to " + str(freed.get("date") or "")[:10] + " " + _clock(freed.get("time"))
        + " because an earlier slot opened. SMS was not sent."
    )
    _save_message(patient, "Appointment moved earlier", text, "reschedule")
    return {
        "moved": True,
        "patient": patient,
        "from": str(chosen.get("date") or "") + " " + _clock(chosen.get("time")),
        "to": str(freed.get("date") or "")[:10] + " " + _clock(freed.get("time")),
        "summary": text,
        "explained_by": "hospital-records",
    }

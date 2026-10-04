# =============================================================================
# Wolaita Sodo Hospital — routers/chatbot.py  (Module 7: Symptom Checker Chatbot)
# POST /ai/symptom-chat
# Uses the trained TF-IDF + RF/XGB ensemble (43 disease classes) plus
# urgency keywords and response templates from backend/models.
# =============================================================================
import json
import logging
import re
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from groq_client import assistant_reply, chat_reply
from model_loader import load_module, load_config, blend, MODELS_DIR

router = APIRouter(tags=["AI · Chatbot"])
log = logging.getLogger("mediq.chatbot")


class ChatTurn(BaseModel):
    role: str = "user"
    content: str = ""


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    history: list[ChatTurn] = Field(default_factory=list)


SYMPTOM_HINTS = (
    "fever", "cough", "headache", "pain", "ache", "hurt", "vomit", "nausea",
    "diarrhea", "bleed", "breath", "dizziness", "rash", "chill", "swell", "itch",
    "fatigue", "tired", "weak", "sore", "chest", "stomach", "abdominal",
    "seizure", "unconscious", "malaria", "symptom", "sick", "ill", "unwell",
    "wound", "cramp", "throat", "faint", "nausea", "constipation",
    "not feeling", "feel sick", "feel unwell", "feeling bad",
    "ትኩሳት", "ሳል", "ራስ ምታት",
)
ASSISTANT_FALLBACK = (
    "I am the Wolaita Sodo Hospital assistant. I can explain the system and how to use it: "
    "sign-in, the dashboard, appointments, medical records, bills, complaints, the health card, "
    "messages, settings, and health videos. I can also say what each page or role means. "
    "If you feel unwell, describe your own symptoms and I will check possible conditions."
)
ASSISTANT_FOLLOW = "Which page or word should I explain, or do you want the steps to use it?"
SYSTEM_GUIDE = (
    "Wolaita Sodo University Hospital system, Wolaita Sodo, South Ethiopia. "
    "Patients and staff sign in on the main login page. A new patient uses Create Account. "
    "A health card is created automatically after the account is created. Forgot password is on the login page. "
    "Administrators sign in only through the Administrator portal. Other roles must use the main login. "
    "The left menu is the sidebar. The bottom bar is the taskbar. Settings and Messages are in the sidebar. "
    "If a page is missing, the administrator has not granted that permission. "
    "Patient Dashboard, also called Home, shows the welcome page, upcoming appointments, recent complaints, and the outstanding bill summary. "
    "Appointments: open Appointments, choose Book Appointment, then department, doctor from the list, date, time, and reason, then Request Booking. "
    "Bookable departments are Internal Medicine, Pediatrics, Cardiology, Maternity, and Orthopedics. "
    "An open appointment can be edited, rescheduled, or cancelled. A cancelled, completed, or attended appointment cannot be changed here. This chat cannot book. "
    "Medical Records is a timeline of saved visits, prescriptions, and laboratory notes. The patient reads them; a doctor files the clinical note. "
    "Bills shows billing history and the outstanding balance. Status means Paid, Pending, or Overdue. View a bill for the itemized breakdown. Print a receipt only for a paid bill. The page does not take payment; settle an unpaid bill at the hospital cashier. Do not invent an amount. "
    "Complaints: open Complaints, choose a category, subject, priority, and description, then Submit. The General Manager reviews it and can write a solution. Status means pending, in-review, or resolved. "
    "Health Card is the hospital identity card. Open Health Card to see it, print it, or show it at the front desk for check-in. The barcode links the file to pharmacy and laboratory. If it is not ready, sign out and sign in again. "
    "Messages: open Messages, choose Compose, type a name or email, subject, and message, then Send. The search shows the person's profile and email. A sent message appears for the receiver. Known contacts are Front Desk, Pharmacy, Laboratory, and Dr. Daniel Alemu in Internal Medicine. "
    "Health Videos are educational only, not medical advice. Search a topic or play a suggestion. "
    "Settings saves the profile, profile photo, password of at least 8 characters, notification preferences, and appearance. "
    "This AI Chatbot explains the hospital and the system. It checks possible conditions only when the person describes their own symptoms. It is not a diagnosis. "
    "Role meanings: Reception registers patients, admissions, appointments, the queue, ambulance, cashier, and insurance. "
    "A doctor sees patients, consultations, prescriptions, referrals, and bed requests. "
    "A nurse records vitals, observations, medications, care plans, and beds. "
    "A pharmacist handles prescriptions and medicine stock. "
    "Laboratory handles test requests, samples, results, and the blood bank. "
    "The General Manager handles departments, staff, finance, reports, and complaints. "
    "The Administrator handles users, roles and permissions, wards, announcements, and audit logs. "
    "Emergency care is the Emergency Department, or call 907 in Ethiopia. Do not invent a phone number, price, or opening hours."
)
SYSTEM_TOPICS = (
    (("sign in", "sign up", "login", "log in", "password", "account", "create account"),
     "Sign in on the main login page. Create a patient account from Create Account. A health card is made automatically. Use Forgot password on the login page if needed. Administrators use only the Administrator portal."),
    (("dashboard", "home", "taskbar", "sidebar", "menu", "system", "how can i use", "how do i use", "how to use"),
     "The Dashboard is the home page. It shows upcoming appointments, complaints, and the bill summary. The sidebar is the left menu. The bottom taskbar has Home, Appointments, Records, Health Card, and Messages. Settings and Messages are also in the sidebar."),
    (("appointment", "book", "reschedule"),
     "Open Appointments, then Book Appointment. Choose a department, a doctor from the list, a date, a time, and a reason, then Request Booking. You can edit, reschedule, or cancel an open appointment. This chat cannot book one for you."),
    (("record", "medical record", "timeline"),
     "Medical Records means the saved timeline of visits, prescriptions, and laboratory notes. You read them there. A doctor files the clinical note."),
    (("bill", "payment", "cashier", "receipt"),
     "Bills means your billing history and outstanding balance. Paid, Pending, and Overdue are the statuses. You can view a bill and print a receipt only when it is paid. The page does not take payment; settle an unpaid bill at the cashier."),
    (("complaint",),
     "A complaint is a report for the General Manager. Open Complaints, enter category, subject, priority, and description, then Submit. Status means pending, in-review, or resolved."),
    (("health card", "card"),
     "The health card is your hospital identity card. It is created with your account. Open Health Card to view or print it, and show it at the front desk. The barcode links your file to pharmacy and laboratory."),
    (("message", "front desk", "pharmacy"),
     "Open Messages, then Compose. Type a name or email, a subject, and the message, then Send. The search shows that person's profile and email. Front Desk, Pharmacy, Laboratory, and Dr. Daniel Alemu can be contacted there."),
    (("video",),
     "Health Videos are for learning only. They are not medical advice. Search a topic or play a suggestion."),
    (("setting", "profile", "photo"),
     "Settings is where you save your profile, photo, password, notifications, and appearance. A new password must be at least 8 characters."),
    (("role", "permission", "doctor", "nurse", "reception", "admin", "manager", "laboratory", "pharmacist"),
     "Reception registers patients and handles the queue, cashier, and ambulance. A doctor consults and prescribes. A nurse records vitals and care. Pharmacy handles medicines. Laboratory handles tests and the blood bank. The manager reviews complaints, finance, and reports. The administrator controls users and permissions. A missing page means that permission was not granted."),
    (("emergency", "907"),
     "For an emergency, go to the Emergency Department or call 907 in Ethiopia."),
)


def _has_symptom(text: str) -> bool:
    msg = (text or "").lower()
    msg = msg.replace("blood test", " ").replace("blood bank", " ")
    msg = re.sub(r"\b(?:sick|tired|ill)\s+of\b", " ", msg)
    for hint in SYMPTOM_HINTS:
        if any(ord(ch) > 127 for ch in hint):
            if hint in (text or ""):
                return True
            continue
        # Match the word or a longer form, never a shorter word inside another.
        if re.search(r"\b" + re.escape(hint) + r"(?:s|es|ing|ed|ness|ish)?\b", msg):
            return True
    return False


def _is_system_question(msg: str) -> bool:
    marks = (
        "how do i", "how can i", "how to", "how does", "what does", "what is", "what are",
        "what mean", "means", "explain", "guide", "help me", "where is", "where can",
        "sign in", "sign up", "log in", "password", "dashboard", "taskbar", "sidebar",
        "permission", "use the system", "use this", "page", "menu",
    )
    return any(mark in msg for mark in marks)


def _reports_own_symptoms(msg: str) -> bool:
    personal = bool(re.search(r"\b(i have|i feel|i am having|i'm having|i've got|i got)\b", msg))
    if personal and (_has_symptom(msg) or any(keyword in msg for keyword in URGENCY_KEYWORDS["red"])):
        return True
    if re.search(r"\b(hurts|painful)\b", msg) and not _is_system_question(msg):
        return True
    return False


def local_system_reply(message: str) -> tuple:
    msg = (message or "").lower()
    hits = [text for keys, text in SYSTEM_TOPICS if any(key in msg for key in keys)]
    if not hits:
        return ASSISTANT_FALLBACK, ASSISTANT_FOLLOW
    reply = " ".join(hits[:2])
    return reply[:1200], "What else should I explain about the system?"


def is_symptom_request(message: str, history: list) -> bool:
    """Disease prediction only when the person describes their own symptoms."""
    msg = (message or "").lower()
    if _is_system_question(msg) and not _reports_own_symptoms(msg):
        return False
    red = URGENCY_KEYWORDS["red"]
    if any(keyword in msg for keyword in red):
        return True
    if _has_symptom(msg):
        return True
    words = msg.split()
    if len(words) > 14 or not history:
        return False
    if any(phrase in msg for phrase in (
        "appointment", "opening", "where is", "where can", "bill", "pharmacy",
        "login", "department", "health card", "laboratory", "how do i", "how can i",
    )):
        return False
    prior = " ".join(str(turn.get("content") or "") for turn in history[-4:])
    return _has_symptom(prior) or any(keyword in prior.lower() for keyword in red)


URGENCY_KEYWORDS = {
    "red": ["chest pain", "difficulty breathing", "shortness of breath", "unconscious", "seizure", "severe bleeding", "stroke", "can't breathe", "cannot breathe", "choking"],
    "orange": ["fever", "vomiting", "diarrhea", "dehydrat", "dizziness", "confusion", "rash", "swelling", "severe pain"],
    "green": ["cough", "headache", "tired", "fatigue", "itch", "sore throat", "runny nose", "mild"],
}


def _load_json(rel: str):
    p = Path(MODELS_DIR) / rel
    if p.is_file():
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None
    return None


def _assistant(req: ChatRequest) -> dict:
    history = [{"role": turn.role, "content": turn.content} for turn in (req.history or [])]
    try:
        local_reply, local_follow = local_system_reply(req.message)
        reply, follow_up, explained_by = assistant_reply(
            req.message, history, local_reply, local_follow, SYSTEM_GUIDE
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("hospital assistant failed: %s", type(exc).__name__)
        reply, follow_up, explained_by = local_system_reply(req.message) + ("local",)
    return {
        "mode": "assistant",
        "reply": reply,
        "explanation": reply,
        "explained_by": explained_by,
        "conditions": [],
        "urgency": "",
        "action": "",
        "follow_up": follow_up,
        "disclaimer": "Hospital assistant only. This is not a diagnosis.",
        "model": "hospital-assistant",
        "model_version": "1.0.0",
        "source": explained_by,
    }


@router.post("/ai/symptom-chat")
def symptom_chat(req: ChatRequest):
    history = [{"role": turn.role, "content": turn.content} for turn in (req.history or [])]
    if not is_symptom_request(req.message, history):
        return _assistant(req)
    symptom_text = req.message
    if not _has_symptom(req.message):
        earlier = " ".join(
            str(turn.get("content") or "")
            for turn in history
            if turn.get("role") == "user" and _has_symptom(str(turn.get("content") or ""))
        )
        if earlier:
            symptom_text = f"{earlier} {req.message}"
    models = load_module("symptom")
    cfg = load_config("symptom", "model_config.json") or {}
    urgency_kw = _load_json("symptom-checker/urgency_keywords.json") or URGENCY_KEYWORDS
    templates = _load_json("symptom-checker/response_templates.json") or {}

    rf = models.get("rf_model.pkl")
    xgb = models.get("xgb_model.pkl")
    tfidf = models.get("tfidf_vectorizer.pkl")
    le = models.get("label_encoder.pkl")

    conditions = []
    source = "rules"
    if tfidf is not None and (rf is not None or xgb is not None) and le is not None:
        try:
            X = tfidf.transform([symptom_text]).toarray()
            w = cfg.get("ensemble", {})
            p_rf = rf.predict_proba(X)[0] if rf is not None else None
            p_xgb = xgb.predict_proba(X)[0] if xgb is not None else None
            probs = blend(p_rf, p_xgb,
                          float(w.get("rf_weight", 0.6)),
                          float(w.get("xgb_weight", 0.4)))
            n = len(le.classes_)
            full = np.zeros(n)
            if probs is not None:
                full[: len(probs)] = probs[:n]
            top = np.argsort(-full)[:3]
            conditions = [str(le.inverse_transform([int(i)])[0]).title() for i in top if full[i] > 0.02]
            source = "trained-model"
        except Exception as exc:  # noqa: BLE001
            log.warning("chatbot inference failed: %s → keywords", exc)

    msg = (symptom_text or "").lower()
    if not conditions:
        if "fever" in msg and ("chill" in msg or "headache" in msg):
            conditions = ["Malaria"]
        elif "chest" in msg:
            conditions = ["Angina", "Acid Reflux"]
        elif "cough" in msg or "throat" in msg:
            conditions = ["Upper Respiratory Infection"]
        elif "headache" in msg:
            conditions = ["Tension Headache", "Migraine"]
        elif "breath" in msg:
            conditions = ["Asthma Exacerbation", "Pneumonia"]
        elif "stomach" in msg or "abdominal" in msg or "diarrhea" in msg:
            conditions = ["Gastroenteritis", "Food Poisoning"]
        elif "tired" in msg or "fatigue" in msg or "weak" in msg:
            conditions = ["Anemia", "Hypothyroidism"]
        else:
            conditions = ["General Health Query"]

    # urgency — the most severe matching keyword wins. Groq must not lower it.
    URGENCY_MAP = {"emergency": "red", "critical": "red", "see_doctor": "orange", "warning": "orange",
                   "self_care": "green", "mild": "green", "red": "red", "orange": "orange", "green": "green"}
    rank = {"green": 0, "orange": 1, "red": 2}
    urgency = "green"
    for level, kws in urgency_kw.items():
        mapped = URGENCY_MAP.get(level, "orange")
        if mapped not in rank:
            mapped = "orange"
        if any(k in msg for k in kws) and rank[mapped] > rank[urgency]:
            urgency = mapped

    action = {"red": "Seek emergency care", "orange": "See a doctor", "green": "Self-care"}[urgency]
    follow = templates.get("follow_up", {}).get(urgency, "Can you describe when the symptoms started?")
    if isinstance(follow, dict):
        follow = list(follow.values())[0]
    fallback_reply = "Based on the symptoms you described, I found some possible conditions. This is not a medical diagnosis — please consult a clinician."
    try:
        reply, follow_up, explained_by = chat_reply(
            symptom_text, conditions[:3], urgency, action, history, fallback_reply, str(follow)
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("chatbot explanation failed: %s", type(exc).__name__)
        reply, follow_up, explained_by = fallback_reply, str(follow), "local"

    return {
        "mode": "symptoms",
        "reply": reply,
        "explanation": reply,
        "explained_by": explained_by,
        "conditions": conditions[:3],
        "urgency": urgency,
        "action": action,
        "follow_up": follow_up,
        "disclaimer": "AI suggestions only. Final diagnosis by doctor.",
        "model": "symptom_ensemble", "model_version": cfg.get("version", "1.0.0"),
        "source": source,
    }

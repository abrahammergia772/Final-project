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
    "I am the Wolaita Sodo Hospital assistant. I can help with appointments, "
    "departments, the laboratory, pharmacy, bills, your health card, and messages. "
    "If you feel unwell, describe your symptoms and I will check possible conditions. "
    "I only answer questions about this hospital."
)
ASSISTANT_FOLLOW = "Would you like help with an appointment, a department, or your symptoms?"


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


def is_symptom_request(message: str, history: list) -> bool:
    """Disease prediction only when the person describes symptoms."""
    msg = (message or "").lower()
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
        reply, follow_up, explained_by = assistant_reply(
            req.message, history, ASSISTANT_FALLBACK, ASSISTANT_FOLLOW
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("hospital assistant failed: %s", type(exc).__name__)
        reply, follow_up, explained_by = ASSISTANT_FALLBACK, ASSISTANT_FOLLOW, "local"
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

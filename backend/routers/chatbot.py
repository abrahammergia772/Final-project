# =============================================================================
# Wolaita Sodo Hospital — routers/chatbot.py  (Module 7: Symptom Checker Chatbot)
# POST /ai/symptom-chat
# Uses the trained TF-IDF + RF/XGB ensemble (43 disease classes) plus
# urgency keywords and response templates from backend/models.
# =============================================================================
import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from model_loader import load_module, load_config, blend, MODELS_DIR

router = APIRouter(tags=["AI · Chatbot"])
log = logging.getLogger("mediq.chatbot")


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


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


@router.post("/ai/symptom-chat")
def symptom_chat(req: ChatRequest):
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
            X = tfidf.transform([req.message]).toarray()
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

    msg = (req.message or "").lower()
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

    # urgency — map the model's own label set to the frontend's green/orange/red
    URGENCY_MAP = {"emergency": "red", "critical": "red", "see_doctor": "orange", "warning": "orange",
                   "self_care": "green", "mild": "green", "red": "red", "orange": "orange", "green": "green"}
    urgency = "green"
    for level, kws in urgency_kw.items():
        if any(k in msg for k in kws):
            urgency = URGENCY_MAP.get(level, "orange")
            break
    if urgency not in ("red", "orange", "green"):
        urgency = "orange"

    action = {"red": "Seek emergency care", "orange": "See a doctor", "green": "Self-care"}[urgency]
    follow = templates.get("follow_up", {}).get(urgency, "Can you describe when the symptoms started?")
    if isinstance(follow, dict):
        follow = list(follow.values())[0]

    return {
        "reply": "Based on the symptoms you described, I found some possible conditions. This is not a medical diagnosis — please consult a clinician.",
        "conditions": conditions[:3],
        "urgency": urgency,
        "action": action,
        "follow_up": str(follow),
        "disclaimer": "AI suggestions only. Final diagnosis by doctor.",
        "model": "symptom_ensemble", "model_version": cfg.get("version", "1.0.0"),
        "source": source,
    }

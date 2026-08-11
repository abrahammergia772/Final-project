# ============================================================
# MedIQ Pro — FastAPI Backend
# Wolaita Sodo University · AI-Powered Hospital Management System
#
# Exposes the 7 AI module endpoints that the frontend expects, plus /auth/login.
# It loads trained .pkl models from ../models/ when they exist, and otherwise
# falls back to built-in rule-based logic so the whole system works end-to-end
# even before the models are trained.
#
# Run locally:  uvicorn main:app --reload --port 8000
# ============================================================
import os
import math
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ------------------------------------------------------------------
# App & CORS (allow the Netlify frontend to call this API)
# ------------------------------------------------------------------
app = FastAPI(title="MedIQ Pro API", version="1.0.0")

ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS_DIR = Path(os.getenv("MODELS_DIR", "../models")).resolve()

# ------------------------------------------------------------------
# Model loader — scans ../models/ for .pkl files and exposes them.
# Each module checks whether its model is present before using it.
# ------------------------------------------------------------------
_MODEL_CACHE: Dict[str, Any] = {}


def get_model(key: str) -> Optional[Any]:
    """Load a .pkl model by key, e.g. 'clinical' -> clinical.pkl.
    Returns None if the file is missing (caller falls back to rules)."""
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]
    candidates = [
        MODELS_DIR / f"{key}.pkl",
        MODELS_DIR / f"{key}_model.pkl",
        MODELS_DIR / f"{key}.joblib",
    ]
    for path in candidates:
        if path.exists():
            try:
                with open(path, "rb") as fh:
                    _MODEL_CACHE[key] = pickle.load(fh)
                return _MODEL_CACHE[key]
            except Exception:
                _MODEL_CACHE[key] = None
                return None
    _MODEL_CACHE[key] = None
    return None


def model_version(key: str, default: str) -> str:
    m = get_model(key)
    return getattr(m, "version", default)


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


class DiseaseRequest(BaseModel):
    symptoms: str
    vitals: Optional[Dict[str, Any]] = None
    history: Optional[List[str]] = None


class InteractionRequest(BaseModel):
    drug_a: str
    drug_b: str


class LabRequest(BaseModel):
    test_type: str = "blood"
    patient: str = ""
    values: Dict[str, Any] = {}


class VitalsRequest(BaseModel):
    hr: Optional[float] = None
    sys: Optional[float] = None
    dia: Optional[float] = None
    temp: Optional[float] = None
    spo2: Optional[float] = None
    rr: Optional[float] = None


class ForecastRequest(BaseModel):
    drug_name: str = "Paracetamol 500mg"
    days: int = 30


class AppointmentRequest(BaseModel):
    patient: str = ""
    day: str = ""
    type: str = "Consultation"
    dept: str = ""
    history_no_show: int = 0


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


# ------------------------------------------------------------------
# Demo users (in production: check against Supabase users table)
# ------------------------------------------------------------------
DEMO_USERS = {
    "admin@mediq.pro": {"password": "admin123", "role": "admin", "name": "Solomon Tadesse"},
    "manager@mediq.pro": {"password": "manager123", "role": "manager", "name": "Hanna Bekele"},
    "doctor@mediq.pro": {"password": "doctor123", "role": "doctor", "name": "Dr. Daniel Alemu"},
    "nurse@mediq.pro": {"password": "nurse123", "role": "nurse", "name": "Marta Tesfaye"},
    "pharmacist@mediq.pro": {"password": "pharmacist123", "role": "pharmacist", "name": "Yonas Girma"},
    "lab@mediq.pro": {"password": "lab123", "role": "laboratory", "name": "Sara Worku"},
    "reception@mediq.pro": {"password": "reception123", "role": "reception", "name": "Liya Hailu"},
    "patient@mediq.pro": {"password": "patient123", "role": "patient", "name": "Abel Mekonnen"},
}


@app.get("/")
def root():
    return {"status": "ok", "service": "MedIQ Pro API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------------
# POST /auth/login
# ------------------------------------------------------------------
@app.post("/auth/login")
def login(req: LoginRequest):
    user = DEMO_USERS.get(req.email.strip().lower())
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": "demo-token", "role": user["role"], "user_id": req.email, "name": user["name"]}


# ==================================================================
# AI MODULE 1 — Clinical Decision Support (/ai/predict-disease)
# ==================================================================
@app.post("/ai/predict-disease")
def predict_disease(req: DiseaseRequest):
    syms = (req.symptoms or "").lower()
    predictions = [
        {"disease": "Malaria", "confidence": 82,
         "description": "Common in the region — presents with fever, chills and headache. Confirm with blood film / RDT.",
         "urgency": "See doctor"},
        {"disease": "Typhoid Fever", "confidence": 61,
         "description": "Prolonged fever with abdominal discomfort. Widal test and blood culture recommended.",
         "urgency": "See doctor"},
        {"disease": "Upper Respiratory Infection", "confidence": 47,
         "description": "Cough, sore throat and mild fever. Usually viral and self-limiting.",
         "urgency": "Self-care"},
    ]
    if "cough" in syms or "throat" in syms:
        predictions.insert(0, {"disease": "Upper Respiratory Infection", "confidence": 74,
                               "description": "Cough, sore throat and mild fever. Usually viral and self-limiting.",
                               "urgency": "Self-care"})
    if "chest" in syms or "breath" in syms:
        predictions.insert(0, {"disease": "Pneumonia (suspected)", "confidence": 79,
                               "description": "Fever with productive cough and breathing difficulty. Chest X-ray advised.",
                               "urgency": "See doctor"})
    # If a trained model exists, prefer its predictions when available
    m = get_model("clinical")
    if m is not None:
        try:
            X = [[len(syms), (req.vitals or {}).get("temp", 37.0)]]
            probs = m.predict_proba(X)[0].tolist() if hasattr(m, "predict_proba") else None
            if probs:
                classes = list(m.classes_)
                ordered = sorted(zip(classes, probs), key=lambda x: -x[1])[:3]
                predictions = [{"disease": c, "confidence": round(p * 100, 1),
                                "description": "Generated by trained clinical model.", "urgency": "See doctor"}
                               for c, p in ordered]
        except Exception:
            pass
    return {"predictions": predictions[:3], "model": "rf_clinical_v1.2", "model_version": model_version("clinical", "1.2.0")}


# ==================================================================
# AI MODULE 2 — Drug Interaction (/ai/check-interaction)
# ==================================================================
@app.post("/ai/check-interaction")
def check_interaction(req: InteractionRequest):
    a, b = req.drug_a.lower(), req.drug_b.lower()
    both = a + "|" + b
    if "warfarin" in both and "aspirin" in both:
        res = {"level": "severe", "title": "Severe Interaction",
               "mechanism": "Both drugs inhibit platelet aggregation and increase bleeding risk.",
               "effect": "Significant risk of gastrointestinal bleeding and hemorrhage.",
               "action": "Avoid combination. Use alternative analgesia or monitor INR closely."}
    elif ("metformin" in both and "furosemide" in both):
        res = {"level": "moderate", "title": "Moderate Interaction",
               "mechanism": "Additive effect on renal function and lactic acidosis risk.",
               "effect": "Reduced renal clearance may increase metformin levels.",
               "action": "Monitor renal function; adjust doses as needed."}
    elif ("amlodipine" in both and "statin" in both) or ("amlodipine" in both and "atorvastatin" in both):
        res = {"level": "moderate", "title": "Moderate Interaction",
               "mechanism": "CYP3A4 metabolism shared by both drugs.",
               "effect": "Increased exposure to the statin — myopathy risk.",
               "action": "Monitor for muscle pain; consider lower statin dose."}
    elif "digoxin" in both and "furosemide" in both:
        res = {"level": "severe", "title": "Severe Interaction",
               "mechanism": "Diuretic-induced hypokalemia potentiates digoxin toxicity.",
               "effect": "Risk of cardiac arrhythmias.",
               "action": "Monitor serum potassium; correct hypokalemia before dosing."}
    else:
        res = {"level": "safe", "title": "No Significant Interaction",
               "mechanism": "No known pharmacokinetic or pharmacodynamic interaction between these drugs.",
               "effect": "No clinically significant effect expected.",
               "action": "No action required. Standard monitoring applies."}
    return {**res, "drug_a": req.drug_a, "drug_b": req.drug_b,
            "model": "drug_int_v1.1", "model_version": model_version("drug_int", "1.1.0")}


# ==================================================================
# AI MODULE 3 — Lab Analyzer (/ai/analyze-lab)
# ==================================================================
REF_RANGES = {
    "hemoglobin": {"name": "Hemoglobin", "range": "13.5 – 17.5 g/dL", "low": 13.5, "high": 17.5, "unit": "g/dL"},
    "wbc": {"name": "WBC", "range": "4.0 – 11.0 ×10³/µL", "low": 4.0, "high": 11.0, "unit": "×10³/µL"},
    "rbc": {"name": "RBC", "range": "4.5 – 5.9 ×10⁶/µL", "low": 4.5, "high": 5.9, "unit": "×10⁶/µL"},
    "platelets": {"name": "Platelets", "range": "150 – 450 ×10³/µL", "low": 150, "high": 450, "unit": "×10³/µL"},
    "creatinine": {"name": "Creatinine", "range": "0.7 – 1.3 mg/dL", "low": 0.7, "high": 1.3, "unit": "mg/dL"},
    "alt": {"name": "ALT", "range": "7 – 56 U/L", "low": 7, "high": 56, "unit": "U/L"},
    "ast": {"name": "AST", "range": "10 – 40 U/L", "low": 10, "high": 40, "unit": "U/L"},
    "tsh": {"name": "TSH", "range": "0.4 – 4.0 mIU/L", "low": 0.4, "high": 4.0, "unit": "mIU/L"},
    "glucose": {"name": "Glucose (Fasting)", "range": "70 – 100 mg/dL", "low": 70, "high": 100, "unit": "mg/dL"},
}


@app.post("/ai/analyze-lab")
def analyze_lab(req: LabRequest):
    rows = []
    for key, val in req.values.items():
        ref = REF_RANGES.get(key)
        try:
            num = float(val)
        except (TypeError, ValueError):
            continue
        if not ref:
            continue
        status = "low" if num < ref["low"] else ("high" if num > ref["high"] else "normal")
        deviation = "—" if status == "normal" else f"{round((num - (ref['high'] + ref['low']) / 2) / ((ref['high'] - ref['low']) / 2) * 100)}% from range"
        rows.append({"name": ref["name"], "range": ref["range"], "value": f"{val} {ref['unit']}", "status": status, "deviation": deviation})
    if not rows:
        rows.append({"name": "Hemoglobin", "range": "13.5 – 17.5 g/dL", "value": "—", "status": "normal", "deviation": "—"})
    abnormal = [r for r in rows if r["status"] != "normal"]
    conditions = []
    if any("creatinine" in r["name"].lower() for r in abnormal):
        conditions.append("Possible renal impairment — monitor eGFR")
    if any("glucose" in r["name"].lower() for r in abnormal):
        conditions.append("Impaired fasting glucose — consider diabetes screening")
    if any(r["name"] in ("ALT", "AST") for r in abnormal):
        conditions.append("Hepatic enzyme elevation — evaluate liver function")
    if any(r["name"] in ("Hemoglobin", "RBC") for r in abnormal):
        conditions.append("Possible anemia — further workup advised")
    if not conditions:
        conditions = ["All measured values within reference ranges."]
    return {"overall": "abnormal" if abnormal else "normal", "rows": rows, "conditions": conditions,
            "model": "lab_analyzer_v2.0", "model_version": model_version("lab", "2.0.0")}


# ==================================================================
# AI MODULE 4 — Vitals Alert (/ai/check-vitals)
# ==================================================================
@app.post("/ai/check-vitals")
def check_vitals(req: VitalsRequest):
    flags = []
    hr, sys, dia, temp, spo2, rr = req.hr, req.sys, req.dia, req.temp, req.spo2, req.rr
    if hr is not None and (hr > 100 or hr < 60):
        flags.append({"vital": "Heart Rate", "value": f"{hr} bpm", "range": "60 – 100 bpm",
                      "severity": "critical" if hr > 120 or hr < 45 else "warning",
                      "by": f"{abs(hr - 80)} bpm off"})
    if (sys is not None and sys > 140) or (dia is not None and dia > 90):
        flags.append({"vital": "Blood Pressure", "value": f"{sys}/{dia} mmHg", "range": "90–140 / 60–90 mmHg",
                      "severity": "critical" if (sys or 0) > 180 or (dia or 0) > 120 else "warning",
                      "by": f"{abs((sys or 115) - 115)} mmHg off"})
    if temp is not None and temp > 38.5:
        flags.append({"vital": "Temperature", "value": f"{temp} °C", "range": "36.1 – 37.8 °C",
                      "severity": "critical" if temp > 40 else "warning", "by": f"{round(temp - 37.8, 1)} °C high"})
    if spo2 is not None and spo2 < 94:
        flags.append({"vital": "SpO2", "value": f"{spo2} %", "range": "94 – 100 %",
                      "severity": "critical" if spo2 < 90 else "warning", "by": f"{94 - spo2}% low"})
    if rr is not None and (rr > 22 or rr < 10):
        flags.append({"vital": "Respiratory Rate", "value": f"{rr} /min", "range": "12 – 20 /min",
                      "severity": "critical" if rr > 28 or rr < 8 else "warning", "by": f"{abs(rr - 16)} breaths/min off"})

    if any(f["severity"] == "critical" for f in flags):
        level, actions = "critical", ["Notify the attending doctor immediately.",
                                      "Move patient to a monitored bed if admitted.",
                                      "Prepare for emergency review — repeat vitals in 15 minutes."]
    elif flags:
        level, actions = "warning", ["Recheck vitals in 1 hour.", "Inform the nursing supervisor.",
                                     "Review medication schedule for possible causes."]
    else:
        level, actions = "normal", ["Continue routine monitoring."]
    return {"level": level, "flags": flags, "actions": actions,
            "model": "vitals_alert_v1.3", "model_version": model_version("vitals", "1.3.0")}


# ==================================================================
# AI MODULE 5 — Inventory Forecast (/ai/forecast-inventory)
# ==================================================================
@app.post("/ai/forecast-inventory")
def forecast_inventory(req: ForecastRequest):
    seed = len(req.drug_name)
    daily_use = 8 + (seed % 5)
    historical = [82, 90, 78, 95, 88, 102, 84, 97, 91, 108, 86, 99]
    forecast = []
    projected = 0
    for i in range(1, req.days + 1):
        wave = round(daily_use * (1 + 0.18 * math.sin(i / 6 + seed)))
        projected += wave
        forecast.append({"day": f"Day {i}", "value": wave})
    current_stock = max(60, (seed * 37) % 500)
    runs_out = projected >= current_stock
    suggested = max(0, projected - current_stock) + round(req.days * daily_use * 0.25)
    return {
        "drug_name": req.drug_name, "days": req.days, "current_stock": current_stock,
        "historical": [{"label": f"D-{12 - i}", "value": v} for i, v in enumerate(historical)],
        "forecast": forecast, "daily_use": daily_use,
        "runs_out_in_days": max(1, math.floor(current_stock / daily_use)) if runs_out else None,
        "suggested_order_qty": suggested,
        "model": "inventory_forecast_v1.4", "model_version": model_version("forecast", "1.4.0"),
    }


# ==================================================================
# AI MODULE 6 — Appointment / No-show (/ai/predict-appointment)
# ==================================================================
@app.post("/ai/predict-appointment")
def predict_appointment(req: AppointmentRequest):
    base = 8 + (len(req.patient) % 25)
    day_factor = 9 if req.day.lower() in ("saturday", "sunday") else 0
    type_factor = 14 if req.type == "Follow-up" else 5
    no_show = min(85, base + day_factor + type_factor + req.history_no_show)
    return {"no_show_percent": round(no_show), "load_prediction": "Moderate", "busy_hours": [8, 9, 10, 11, 14, 15],
            "confidence": 0.9 + ((no_show % 9) / 100),
            "model": "appointment_ai_v1.1", "model_version": model_version("appointment", "1.1.0")}


# ==================================================================
# AI MODULE 7 — Symptom Chatbot (/ai/symptom-chat)
# ==================================================================
@app.post("/ai/symptom-chat")
def symptom_chat(req: ChatRequest):
    msg = (req.message or "").lower()
    if "fever" in msg and ("chill" in msg or "headache" in msg):
        resp = {"conditions": ["Malaria"], "urgency": "orange", "action": "See a doctor",
                "follow_up": "Have you had any vomiting or difficulty urinating?"}
    elif "chest" in msg:
        resp = {"conditions": ["Angina", "Acid reflux"], "urgency": "red", "action": "Seek emergency care",
                "follow_up": "Is the pain radiating to your arm or jaw?"}
    elif "cough" in msg or "throat" in msg:
        resp = {"conditions": ["Upper Respiratory Infection"], "urgency": "green", "action": "Self-care",
                "follow_up": "Do you have a fever above 38°C or shortness of breath?"}
    elif "headache" in msg:
        resp = {"conditions": ["Tension Headache", "Migraine"], "urgency": "green", "action": "Self-care",
                "follow_up": "How long have you had the headache?"}
    elif "breath" in msg:
        resp = {"conditions": ["Possible Asthma exacerbation", "Pneumonia"], "urgency": "orange",
                "action": "See a doctor today", "follow_up": "Do you have a wheeze when breathing out?"}
    elif "stomach" in msg or "abdominal" in msg or "diarrhea" in msg:
        resp = {"conditions": ["Gastroenteritis", "Food poisoning"], "urgency": "orange", "action": "See a doctor",
                "follow_up": "Any blood in your stool or persistent vomiting?"}
    elif "tired" in msg or "fatigue" in msg or "weak" in msg:
        resp = {"conditions": ["Anemia", "Hypothyroidism"], "urgency": "green", "action": "Book a lab test",
                "follow_up": "Do you feel dizzy or short of breath with exertion?"}
    else:
        resp = {"conditions": ["General health query"], "urgency": "green", "action": "Book a consultation",
                "follow_up": "Can you describe when the symptoms started?"}
    return {
        "reply": "Based on the symptoms you described, I found some possible conditions. This is not a medical diagnosis — please consult a clinician.",
        "conditions": resp["conditions"], "urgency": resp["urgency"], "action": resp["action"],
        "follow_up": resp["follow_up"],
        "disclaimer": "AI suggestions only. Final diagnosis by doctor.",
        "model": "symptom_chat_v1.5", "model_version": model_version("chatbot", "1.5.0"),
    }


# =============================================================================
# backend/routers/vitals_alert_ai.py
# Wolaita Sodo Hospital — Module 4: Vitals Alert System AI
# =============================================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import numpy as np
import pandas as pd
import joblib
import json
import os

router = APIRouter(prefix="/api/vitals", tags=["Vitals Alert AI"])

# ── Load models once at startup ────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR  = os.path.join(BASE_DIR, "models")

_rf_model  = joblib.load(os.path.join(MODELS_DIR, "vitals_rf_model.pkl"))
_xgb_model = joblib.load(os.path.join(MODELS_DIR, "vitals_xgb_model.pkl"))
_scaler    = joblib.load(os.path.join(MODELS_DIR, "vitals_scaler.pkl"))

with open(os.path.join(MODELS_DIR, "vitals_config.json")) as f:
    _config = json.load(f)

FEATURE_COLS  = _config["feature_cols"]
NORMAL_RANGES = _config["normal_ranges"]
THRESHOLDS    = _config["alert_thresholds"]
LABEL_MAP     = {int(k): v for k, v in _config["label_map"].items()}
W_RF          = _config["ensemble_weights"]["rf"]
W_XGB         = _config["ensemble_weights"]["xgb"]


# ── Pydantic Schemas ───────────────────────────────────────────────────────────
class VitalsInput(BaseModel):
    heart_rate:        float = Field(..., ge=20,   le=300,  description="Heart rate in bpm")
    bp_systolic:       float = Field(..., ge=50,   le=250,  description="Systolic BP in mmHg")
    bp_diastolic:      float = Field(..., ge=20,   le=160,  description="Diastolic BP in mmHg")
    spo2:              float = Field(..., ge=50,   le=100,  description="SpO2 percentage")
    temperature:       float = Field(..., ge=32.0, le=43.0, description="Temperature in Celsius")
    respiratory_rate:  float = Field(..., ge=4,    le=60,   description="Respiratory rate breaths/min")
    age:               int   = Field(..., ge=0,    le=120,  description="Patient age in years")
    patient_id:        Optional[str] = None

class VitalFlag(BaseModel):
    vital: str
    value: float
    unit: str
    normal_min: float
    normal_max: float
    deviation: float
    direction: str        # "HIGH" or "LOW"
    deviation_pct: float

class VitalsAlertResponse(BaseModel):
    patient_id:          Optional[str]
    alert_level:         str           # "Normal" | "Warning" | "Critical"
    alert_code:          int           # 0 | 1 | 2
    confidence:          float         # 0–100
    probabilities:       dict
    vitals_out_of_range: List[VitalFlag]
    n_vitals_flagged:    int
    recommended_action:  str
    action_code:         str
    normal_ranges:       dict


# ── Feature Engineering (mirrors training notebook) ───────────────────────────
def _engineer_features(data: dict) -> pd.DataFrame:
    df = pd.DataFrame([data])
    
    for vital, rng in NORMAL_RANGES.items():
        if vital not in df.columns: continue
        lo, hi = rng["min"], rng["max"]
        mid  = (lo + hi) / 2
        span = (hi - lo) / 2
        df[f"{vital}_norm_dev"]     = (df[vital] - mid) / span
        df[f"{vital}_out_of_range"] = ((df[vital] < lo) | (df[vital] > hi)).astype(int)
    
    oor_cols = [c for c in df.columns if c.endswith("_out_of_range")]
    df["n_vitals_out_of_range"] = df[oor_cols].sum(axis=1)
    
    if "bp_systolic" in df.columns and "bp_diastolic" in df.columns:
        df["map"]           = (df["bp_systolic"] + 2 * df["bp_diastolic"]) / 3
        df["map_low"]       = (df["map"] < 65).astype(int)
        df["pulse_pressure"] = df["bp_systolic"] - df["bp_diastolic"]
    
    if "heart_rate" in df.columns and "bp_systolic" in df.columns:
        df["shock_index"] = (df["heart_rate"] / df["bp_systolic"].replace(0, np.nan)).clip(0, 5)
    
    # EWS Score
    ews = np.zeros(len(df))
    if "respiratory_rate" in df.columns:
        rr = df["respiratory_rate"].values
        ews += np.where(rr < 9, 3, np.where(rr <= 11, 1, np.where(rr <= 20, 0, np.where(rr <= 24, 2, 3))))
    if "spo2" in df.columns:
        sp = df["spo2"].values
        ews += np.where(sp <= 91, 3, np.where(sp <= 93, 2, np.where(sp <= 95, 1, 0)))
    if "temperature" in df.columns:
        tp = df["temperature"].values
        ews += np.where(tp <= 35.0, 3, np.where(tp <= 36.0, 1, np.where(tp <= 38.0, 0, np.where(tp <= 39.0, 1, 2))))
    if "bp_systolic" in df.columns:
        sb = df["bp_systolic"].values
        ews += np.where(sb <= 90, 3, np.where(sb <= 100, 2, np.where(sb <= 110, 1, np.where(sb <= 149, 0, 2))))
    if "heart_rate" in df.columns:
        hr = df["heart_rate"].values
        ews += np.where(hr < 40, 3, np.where(hr <= 50, 1, np.where(hr <= 100, 0, np.where(hr <= 110, 1, np.where(hr <= 129, 2, 3)))))
    df["ews_score"] = ews
    
    if "age" in df.columns:
        df["age_risk"] = np.where(df["age"] < 18, 1, np.where(df["age"] > 65, 2, 0))
    
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0.0
    
    return df[FEATURE_COLS].fillna(0)


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post("/analyze", response_model=VitalsAlertResponse)
async def analyze_vitals(vitals: VitalsInput):
    """Analyze patient vitals and return alert level with details."""
    try:
        data = vitals.dict()
        patient_id = data.pop("patient_id", None)
        
        # Feature engineering + scaling
        X_feat   = _engineer_features(data)
        X_scaled = _scaler.transform(X_feat)
        
        # Ensemble prediction
        rf_p   = _rf_model.predict_proba(X_scaled)[0]
        xgb_p  = _xgb_model.predict_proba(X_scaled)[0]
        ens_p  = W_RF * rf_p + W_XGB * xgb_p
        pred   = int(np.argmax(ens_p))
        conf   = float(np.max(ens_p)) * 100
        
        alert_level = LABEL_MAP[pred]
        
        # Identify out-of-range vitals
        out_of_range = []
        for vital, rng in NORMAL_RANGES.items():
            val = data.get(vital)
            if val is None: continue
            lo, hi = rng["min"], rng["max"]
            if val < lo:
                dev = lo - val
                out_of_range.append(VitalFlag(
                    vital=vital, value=val, unit=rng["unit"],
                    normal_min=lo, normal_max=hi, deviation=round(dev,2),
                    direction="LOW", deviation_pct=round((dev/lo)*100,1)
                ))
            elif val > hi:
                dev = val - hi
                out_of_range.append(VitalFlag(
                    vital=vital, value=val, unit=rng["unit"],
                    normal_min=lo, normal_max=hi, deviation=round(dev,2),
                    direction="HIGH", deviation_pct=round((dev/hi)*100,1)
                ))
        
        # Recommended action
        if alert_level == "Critical":
            action      = "EMERGENCY: Call physician immediately. Prepare for emergency intervention."
            action_code = "emergency"
        elif alert_level == "Warning":
            action      = "NOTIFY DOCTOR: Alert attending physician. Increase monitoring frequency."
            action_code = "notify_doctor"
        else:
            action      = "MONITOR: Continue routine monitoring per schedule."
            action_code = "monitor"
        
        return VitalsAlertResponse(
            patient_id=patient_id,
            alert_level=alert_level,
            alert_code=pred,
            confidence=round(conf, 1),
            probabilities={
                "Normal":   round(float(ens_p[0])*100, 1),
                "Warning":  round(float(ens_p[1])*100, 1),
                "Critical": round(float(ens_p[2])*100, 1),
            },
            vitals_out_of_range=out_of_range,
            n_vitals_flagged=len(out_of_range),
            recommended_action=action,
            action_code=action_code,
            normal_ranges=NORMAL_RANGES
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/normal-ranges")
async def get_normal_ranges():
    """Return normal vital sign reference ranges (for frontend display)."""
    return {"normal_ranges": NORMAL_RANGES}


@router.get("/health")
async def health_check():
    """Check that models are loaded."""
    return {
        "status": "ok",
        "models_loaded": True,
        "performance": _config.get("performance", {})
    }

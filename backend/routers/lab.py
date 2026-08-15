# =============================================================================
# MedIQ Pro — routers/lab.py  (Module 3: Lab Result Analyzer)
# POST /ai/analyze-lab
# Uses the trained 78-feature RF/XGB ensemble (Anemia / CKD / Liver / Normal).
# =============================================================================
import logging
from typing import Any, Dict, Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from model_loader import load_module, load_config

router = APIRouter(tags=["AI · Lab Analyzer"])
log = logging.getLogger("mediq.lab")


class LabRequest(BaseModel):
    test_type: str = "blood"
    patient: str = ""
    values: Dict[str, Any] = {}


CONDITIONS = ["Anemia", "Chronic Kidney Disease", "Liver Disease", "Normal"]


def build_features(values: dict, cfg: dict) -> np.ndarray:
    """Build the 78-feature vector exactly as trained."""
    refs = cfg.get("reference_ranges", {})
    features = cfg.get("features", [])
    feats: Dict[str, float] = {}
    # raw values (fallback to mid-normal when absent)
    for name, ref in refs.items():
        try:
            v = float(values.get(name, (ref["low"] + ref["high"]) / 2.0))
        except (TypeError, ValueError):
            v = (ref["low"] + ref["high"]) / 2.0
        feats[name] = v
    feats.setdefault("age", 40.0)
    # flags + deviation for every measured analyte
    for name, ref in refs.items():
        v = feats.get(name, 0.0)
        flag = 0 if ref["low"] <= v <= ref["high"] else (1 if v < ref["low"] else 2)
        mid = (ref["low"] + ref["high"]) / 2.0
        dev = (v - mid) / max(mid, 1e-9)
        feats[f"{name}_flag"] = float(flag)
        feats[f"{name}_deviation"] = float(dev)
    # ratios / extras the model may expect
    feats.setdefault("albumin_globulin_ratio", 1.5)
    feats.setdefault("albumin_globulin_ratio_flag", 0.0)
    feats.setdefault("albumin_globulin_ratio_deviation", 0.0)
    # build in training order
    vec = []
    for f in features:
        vec.append(float(feats.get(f, 0.0)))
    return np.array([vec])


@router.post("/ai/analyze-lab")
def analyze_lab(req: LabRequest):
    models = load_module("lab")
    cfg = load_config("lab", "lab_feature_config.json") or {}
    refs = cfg.get("reference_ranges", {})

    rf = models.get("lab_rf_model.pkl")
    xgb = models.get("lab_xgb_model.pkl")
    scaler = models.get("lab_scaler.pkl")

    pred_idx = None
    if (rf is not None or xgb is not None) and cfg.get("features"):
        try:
            X = build_features(req.values, cfg)
            if scaler is not None:
                X = scaler.transform(X)
            probs = np.zeros(4)
            w = cfg.get("weights", {})
            if rf is not None:
                p = rf.predict_proba(X)[0]
                probs[: len(p)] += float(w.get("rf", 0.5)) * p
            if xgb is not None:
                p = xgb.predict_proba(X)[0]
                probs[: len(p)] += float(w.get("xgb", 0.5)) * p
            pred_idx = int(np.argmax(probs))
        except Exception as exc:  # noqa: BLE001
            log.warning("lab inference failed: %s → rules", exc)

    # ---- per-value rows ----
    rows = []
    abnormal = []
    for name, ref in refs.items():
        if name not in req.values:
            continue
        try:
            v = float(req.values[name])
        except (TypeError, ValueError):
            continue
        status = "low" if v < ref["low"] else ("high" if v > ref["high"] else "normal")
        if status != "normal":
            abnormal.append(name)
        unit = ref.get("unit", "")
        rows.append({"name": name.replace("_", " ").title(), "range": f"{ref['low']} – {ref['high']} {unit}",
                     "value": f"{v} {unit}".strip(), "status": status, "deviation": "—"})
    if not rows:
        rows.append({"name": "Hemoglobin", "range": "12.0 – 17.5 g/dL", "value": "—", "status": "normal", "deviation": "—"})

    # ---- conditions ----
    if pred_idx is not None and 0 <= pred_idx < len(CONDITIONS):
        conditions = [CONDITIONS[pred_idx]] if pred_idx != 3 else ["All measured values within reference ranges."]
    else:
        conditions = []
        if any(n in abnormal for n in ("hemoglobin", "mcv", "mch", "mchc", "rbc")):
            conditions.append("Possible anemia — further workup advised")
        if "creatinine" in abnormal or "blood_urea" in abnormal:
            conditions.append("Possible renal impairment — monitor eGFR")
        if any(n in abnormal for n in ("total_bilirubin", "direct_bilirubin", "alamine_aminotransferase", "aspartate_aminotransferase", "alkaline_phosphatase", "albumin")):
            conditions.append("Hepatic enzyme elevation — evaluate liver function")
        if not conditions:
            conditions = ["All measured values within reference ranges."]

    return {"overall": "abnormal" if abnormal else "normal", "rows": rows, "conditions": conditions,
            "model": "lab_ensemble", "model_version": cfg.get("model_version", "1.0.0"),
            "source": "trained-model" if pred_idx is not None else "rules"}

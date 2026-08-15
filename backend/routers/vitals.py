# =============================================================================
# MedIQ Pro — routers/vitals.py  (Module 4: Vitals Alert System)
# POST /ai/check-vitals
# Uses the trained 26-feature RobustScaler + RF/XGB ensemble
# (labels: 0 Normal, 1 Warning, 2 Critical).
# =============================================================================
import logging
from typing import Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from model_loader import load_module, load_config

router = APIRouter(tags=["AI · Vitals"])
log = logging.getLogger("mediq.vitals")


class VitalsRequest(BaseModel):
    hr: Optional[float] = None
    sys: Optional[float] = None
    dia: Optional[float] = None
    temp: Optional[float] = None
    spo2: Optional[float] = None
    rr: Optional[float] = None
    age: Optional[float] = 40


LABELS = {0: "Normal", 1: "Warning", 2: "Critical"}


def build_features(req: VitalsRequest, cfg: dict) -> np.ndarray:
    cols = cfg.get("feature_cols", [])
    norm = cfg.get("normal_ranges", {})
    hr = req.hr if req.hr is not None else 80.0
    sys = req.sys if req.sys is not None else 115.0
    dia = req.dia if req.dia is not None else 75.0
    spo2 = req.spo2 if req.spo2 is not None else 97.0
    temp = req.temp if req.temp is not None else 36.8
    rr = req.rr if req.rr is not None else 16.0
    age = req.age or 40.0

    f: dict = {
        "heart_rate": hr, "bp_systolic": sys, "bp_diastolic": dia, "spo2": spo2,
        "temperature": temp, "respiratory_rate": rr, "age": age,
    }
    # normalized deviations + out-of-range flags
    for key, (mn, mx) in {
        "heart_rate": (norm["heart_rate"]["min"], norm["heart_rate"]["max"]),
        "bp_systolic": (norm["bp_systolic"]["min"], norm["bp_systolic"]["max"]),
        "bp_diastolic": (norm["bp_diastolic"]["min"], norm["bp_diastolic"]["max"]),
        "spo2": (norm["spo2"]["min"], norm["spo2"]["max"]),
        "temperature": (norm["temperature"]["min"], norm["temperature"]["max"]),
        "respiratory_rate": (norm["respiratory_rate"]["min"], norm["respiratory_rate"]["max"]),
    }.items():
        v = f[key]
        f[f"{key}_norm_dev"] = (v - (mn + mx) / 2) / max((mx - mn) / 2, 1e-9)
        f[f"{key}_out_of_range"] = 0 if mn <= v <= mx else 1
    vals = [f["heart_rate"], f["bp_systolic"], f["bp_diastolic"], f["spo2"], f["temperature"], f["respiratory_rate"]]
    f["n_vitals_out_of_range"] = sum(f[f"{k}_out_of_range"] for k in
                                     ["heart_rate", "bp_systolic", "bp_diastolic", "spo2", "temperature", "respiratory_rate"])
    f["map"] = (sys + 2 * dia) / 3.0
    f["map_low"] = 1 if f["map"] < 70 else 0
    f["pulse_pressure"] = sys - dia
    f["shock_index"] = hr / max(sys, 1)
    # simple EWS approximation (0-6)
    ews = 0
    ews += 3 if hr > 110 or hr < 50 else (1 if hr > 100 else 0)
    ews += 2 if sys < 90 else (1 if sys > 160 else 0)
    ews += 2 if spo2 < 92 else (1 if spo2 < 94 else 0)
    ews += 2 if temp >= 38.5 else (1 if temp >= 38.0 else 0)
    ews += 2 if rr > 24 else (1 if rr > 20 else 0)
    f["ews_score"] = ews
    # fill any remaining engineered cols the model wants with sensible defaults
    for c in cols:
        f.setdefault(c, 0.0)
    return np.array([[float(f.get(c, 0.0)) for c in cols]])


@router.post("/ai/check-vitals")
def check_vitals(req: VitalsRequest):
    models = load_module("vitals")
    cfg = load_config("vitals", "vitals_config.json") or {}

    rf = models.get("vitals_rf_model.pkl")
    xgb = models.get("vitals_xgb_model.pkl")
    scaler = models.get("vitals_scaler.pkl")

    pred_label = None
    if (rf is not None or xgb is not None) and cfg.get("feature_cols"):
        try:
            X = build_features(req, cfg)
            if scaler is not None:
                X = scaler.transform(X)
            probs = np.zeros(3)
            w = cfg.get("ensemble_weights", {})
            if rf is not None:
                p = rf.predict_proba(X)[0]
                probs[: len(p)] += float(w.get("rf", 0.6)) * p
            if xgb is not None:
                p = xgb.predict_proba(X)[0]
                probs[: len(p)] += float(w.get("xgb", 0.4)) * p
            pred_label = LABELS.get(int(np.argmax(probs)), "Normal")
        except Exception as exc:  # noqa: BLE001
            log.warning("vitals inference failed: %s → rules", exc)

    # ---- flag rows ----
    flags = []
    checks = [
        ("Heart Rate", req.hr, (60, 100), "bpm", 120, 45),
        ("Blood Pressure", (req.sys, req.dia), ((90, 140), (60, 90)), "mmHg", (180, 120), (70, 40)),
        ("Temperature", req.temp, (36.1, 37.8), "°C", 40, 34),
        ("SpO2", req.spo2, (94, 100), "%", 88, None),
        ("Respiratory Rate", req.rr, (12, 20), "/min", 28, 8),
    ]
    for name, val, rng, unit, crit_hi, crit_lo in checks:
        if val is None:
            continue
        if isinstance(rng, tuple) and isinstance(rng[0], tuple):  # BP special
            sys_v, dia_v = val
            sys_ok = rng[0][0] <= sys_v <= rng[0][1]
            dia_ok = rng[1][0] <= dia_v <= rng[1][1]
            if not (sys_ok and dia_ok):
                sev = "critical" if sys_v >= crit_hi[0] or sys_v <= crit_lo[0] or dia_v >= crit_hi[1] or dia_v <= crit_lo[1] else "warning"
                flags.append({"vital": name, "value": f"{sys_v}/{dia_v} mmHg", "range": "90–140 / 60–90 mmHg",
                              "severity": sev, "by": f"{abs(sys_v - 115)} mmHg off"})
            continue
        lo, hi = rng
        if not (lo <= val <= hi):
            sev = "critical" if (crit_hi is not None and val > crit_hi) or (crit_lo is not None and val < crit_lo) else "warning"
            flags.append({"vital": name, "value": f"{val} {unit}".strip(), "range": f"{lo} – {hi} {unit}",
                          "severity": sev, "by": f"{abs(val - (lo + hi) / 2):.1f} {unit} off"})

    # ---- decide level ----
    # Clinical-safety guardrail: the final level is the most severe of the
    # model's prediction and the rule-based vital flags.
    rule_level = "normal"
    if any(f["severity"] == "critical" for f in flags):
        rule_level = "critical"
    elif flags:
        rule_level = "warning"
    model_level = (pred_label or "normal").lower()
    order = {"normal": 0, "warning": 1, "critical": 2}
    level = "critical" if order[model_level] >= 2 or order[rule_level] >= 2 else (
        "warning" if order[model_level] == 1 or order[rule_level] == 1 else "normal")

    actions = {
        "critical": ["Notify the attending doctor immediately.", "Move patient to a monitored bed if admitted.",
                     "Prepare for emergency review — repeat vitals in 15 minutes."],
        "warning": ["Recheck vitals in 1 hour.", "Inform the nursing supervisor.", "Review medication schedule for possible causes."],
        "normal": ["Continue routine monitoring."],
    }[level]

    return {"level": level, "flags": flags, "actions": actions,
            "model": "vitals_ensemble", "model_version": cfg.get("version", "1.0.0"),
            "source": "trained-model" if pred_label else "rules"}

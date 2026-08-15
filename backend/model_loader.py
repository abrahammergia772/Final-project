# =============================================================================
# MedIQ Pro — backend/model_loader.py
# Loads the trained .pkl models for all 7 AI modules from backend/models/.
# Missing files (e.g. the >25 MB appointment RF model that GitHub rejected)
# are logged and the module falls back to whichever models ARE present, or to
# built-in rules — the API never crashes because a file is missing.
# =============================================================================
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import joblib

from config import MODELS_DIR

log = logging.getLogger("mediq.models")

# Module -> subfolder + the files we expect
EXPECTED = {
    "clinical": ("clinical_decision", ["rf_model.pkl", "xgb_model.pkl", "tfidf_vectorizer.pkl", "label_encoder.pkl", "model_config.json"]),
    "drug":     ("drug_interaction", ["drug_interaction_rf.pkl", "drug_interaction_xgb.pkl", "drug_interaction_tfidf.pkl", "drug_interaction_label_encoder.pkl", "drug_interaction_config.json"]),
    "lab":      ("lab", ["lab_rf_model.pkl", "lab_xgb_model.pkl", "lab_scaler.pkl", "lab_imputer.pkl", "lab_label_encoder.pkl", "lab_feature_config.json"]),
    "inventory":("inventory", ["inventory_xgb_model.pkl", "inventory_scaler.pkl", "inventory_label_encoder.pkl", "inventory_config.json"]),
    "symptom":  ("symptom-checker", ["rf_model.pkl", "xgb_model.pkl", "tfidf_vectorizer.pkl", "label_encoder.pkl", "urgency_keywords.json", "response_templates.json", "model_config.json"]),
    "vitals":   ("vitals", ["vitals_rf_model.pkl", "vitals_xgb_model.pkl", "vitals_scaler.pkl", "vitals_config.json"]),
    "appointment": ("appointment", ["xgb_appointment.pkl", "rf_appointment.pkl", "feature_cols.pkl",
                                    "le_department.pkl", "le_doctor.pkl", "le_appt_type.pkl",
                                    "le_gender.pkl", "le_insurance.pkl", "le_reminder.pkl", "appointment_config.json"]),
}

# subfolder -> glob of prophet seasonal files (inventory)
PROPHET_GLOB = ("inventory", "prophet_*.json")

_cache: Dict[str, Any] = {}
_loaded: Dict[str, list] = {}  # module -> list of successfully loaded file names


def _safe_load(path: Path):
    if path.suffix == ".json":
        return None  # handled separately as config
    try:
        return joblib.load(path)
    except Exception as exc:  # noqa: BLE001
        log.warning("  ! could not load %s : %s", path.name, exc)
        return None


def load_module(module: str) -> Dict[str, Any]:
    """Load every expected file for a module into a dict. Returns {} on failure."""
    if module in _cache:
        return _cache[module]
    sub, files = EXPECTED.get(module, (module, []))
    folder = MODELS_DIR / sub
    out: Dict[str, Any] = {}
    ok: list = []
    if folder.is_dir():
        for f in files:
            p = folder / f
            if p.is_file():
                obj = _safe_load(p)
                if obj is not None:
                    key = f.rsplit(".", 1)[0] if f.endswith(".json") else Path(f).stem
                    out[f] = obj
                    ok.append(f)
    # configs: always load raw json text if present
    for f in list(files):
        if f.endswith(".json") and (folder / f).is_file():
            try:
                with open(folder / f, encoding="utf-8") as fh:
                    out[f] = json.load(fh)
            except Exception as exc:  # noqa: BLE001
                log.warning("  ! bad json %s: %s", f, exc)
    _cache[module] = out
    _loaded[module] = ok
    log.info("module %-12s loaded: %s", module, ", ".join(ok) if ok else "NONE (fallback → rules)")
    return out


def module_loaded(module: str) -> bool:
    return bool(_loaded.get(module))


def list_missing(module: str) -> list:
    """Which expected files are missing (e.g. the >25 MB appointment RF model)."""
    sub, files = EXPECTED.get(module, (module, []))
    folder = MODELS_DIR / sub
    missing = []
    for f in files:
        if not (folder / f).is_file():
            missing.append(f)
    return missing


def load_config(module: str, filename: str) -> Optional[dict]:
    data = _cache.get(module, {})
    cfg = data.get(filename)
    if isinstance(cfg, dict):
        return cfg
    sub, _ = EXPECTED.get(module, (module, []))
    p = MODELS_DIR / sub / filename
    if p.is_file():
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None
    return None


def prophet_files() -> Dict[str, Path]:
    """inventory: drug -> prophet seasonal JSON path"""
    sub, _ = PROPHET_GLOB
    folder = MODELS_DIR / sub
    out: Dict[str, Path] = {}
    if folder.is_dir():
        for p in folder.glob("prophet_*.json"):
            drug = p.stem.replace("prophet_", "").replace("_", " ").title()
            out[drug] = p
    return out


def load_all() -> None:
    for m in EXPECTED:
        try:
            load_module(m)
        except Exception as exc:  # noqa: BLE001
            log.warning("module %s failed to load: %s", m, exc)
    missing_appt = list_missing("appointment")
    if missing_appt:
        log.warning("Appointment module missing files (GitHub 25 MB limit?): %s — using XGB only.",
                    ", ".join(missing_appt))

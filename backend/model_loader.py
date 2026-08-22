# =============================================================================
# MedIQ Pro — backend/model_loader.py
# Loads trained .pkl models for all 7 AI modules from backend/models/.
#
# MEMORY-SAFE MODE (default on Render free tier, set LAZY_LOAD=1 or
# SKIP_RF_MODELS=1):
#   - Startup does NOT eager-load all models. Each module is loaded on first
#     request via the existing load_module() cache.
#   - Heavy RandomForest models (tens of MB on disk → hundreds of MB in RAM)
#     are skipped so the API fits in the 512 MB Render free tier. XGBoost
#     models are small and still provide high accuracy (top-1 ≈ 0.91–0.99).
#
# When a model is missing, its router falls back to the other model or to
# built-in rules — the API never crashes because a file is missing.
# =============================================================================
import json
import logging
import os
import gc
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

from config import MODELS_DIR, LAZY_LOAD, SKIP_RF_MODELS

log = logging.getLogger("mediq.models")

# Files that are huge in RAM (RandomForest ensembles). Skipped when
# SKIP_RF_MODELS=1 (default on low-memory / Render free).
RF_FILES = {
    "rf_model.pkl",            # clinical_decision & symptom-checker
    "lab_rf_model.pkl",        # lab
    "vitals_rf_model.pkl",     # vitals
    "drug_interaction_rf.pkl", # drug_interaction
    "rf_appointment.pkl",      # appointment (also >25 MB GitHub limit)
}

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

_cache: Dict[str, Dict[str, Any]] = {}
_loaded: Dict[str, list] = {}  # module -> list of successfully loaded file names


def _should_skip(filename: str) -> bool:
    """Decide whether to skip loading a particular file (RF memory guard)."""
    if not SKIP_RF_MODELS:
        return False
    return filename in RF_FILES


def _safe_load(path: Path):
    if path.suffix == ".json":
        return None  # handled separately as config
    if _should_skip(path.name):
        log.info("  ⊘ skipping %s (SKIP_RF_MODELS=1, memory-save mode)", path.name)
        return None
    try:
        return joblib.load(path)
    except Exception as exc:  # noqa: BLE001
        log.warning("  ! could not load %s : %s", path.name, exc)
        return None


def load_module(module: str) -> Dict[str, Any]:
    """Load every expected file for a module into a dict. Returns {} on failure.

    Results are cached after the first call (per-process). In lazy mode the
    cache starts empty and modules are loaded on first request.
    """
    if module in _cache:
        return _cache[module]
    sub, files = EXPECTED.get(module, (module, []))
    folder = MODELS_DIR / sub
    out: Dict[str, Any] = {}
    ok: list = []
    skipped: list = []
    if folder.is_dir():
        for f in files:
            p = folder / f
            if not p.is_file():
                continue
            if _should_skip(f):
                skipped.append(f)
                continue
            obj = _safe_load(p)
            if obj is not None:
                out[f] = obj
                ok.append(f)
    # configs: always load raw json text if present (small, never skipped)
    for f in list(files):
        if f.endswith(".json") and (folder / f).is_file():
            try:
                with open(folder / f, encoding="utf-8") as fh:
                    out[f] = json.load(fh)
                if f not in ok:
                    ok.append(f)
            except Exception as exc:  # noqa: BLE001
                log.warning("  ! bad json %s: %s", f, exc)
    _cache[module] = out
    _loaded[module] = ok
    parts = ", ".join(ok) if ok else "NONE (fallback → rules)"
    if skipped:
        parts += f"  [skipped RF: {', '.join(skipped)}]"
    log.info("module %-12s loaded: %s", module, parts)
    return out


def unload_module(module: str) -> None:
    """Free memory by evicting a previously loaded module."""
    if module in _cache:
        _cache.pop(module, None)
        _loaded.pop(module, None)
        gc.collect()
        log.info("module %s unloaded (memory freed)", module)


def unload_all() -> None:
    _cache.clear()
    _loaded.clear()
    gc.collect()


def module_loaded(module: str) -> bool:
    return bool(_loaded.get(module))


def list_missing(module: str) -> list:
    """Which expected files are missing (e.g. the >25 MB appointment RF model)."""
    sub, files = EXPECTED.get(module, (module, []))
    folder = MODELS_DIR / sub
    missing = []
    for f in files:
        if _should_skip(f):
            continue
        if not (folder / f).is_file():
            missing.append(f)
    return missing


def load_config(module: str, filename: str) -> Optional[dict]:
    # Configs are JSON and cheap; allow loading even if module isn't cached.
    data = _cache.get(module, {})
    cfg = data.get(filename)
    if isinstance(cfg, dict):
        return cfg
    sub, _ = EXPECTED.get(module, (module, []))
    p = MODELS_DIR / sub / filename
    if p.is_file():
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:  # noqa: BLE001
            return None
    return None


# ---------------------------------------------------------------------------
# Ensemble helper
# ---------------------------------------------------------------------------
def blend(rf_probs, xgb_probs, rf_weight: float = 0.5, xgb_weight: float = 0.5):
    """Blend two probability vectors (either can be None). Returns normalized probs.

    When only one model is present (e.g. SKIP_RF_MODELS=1), returns that model's
    probabilities directly so confidences stay calibrated.
    """
    import numpy as np
    if rf_probs is None and xgb_probs is None:
        return None
    if rf_probs is None:
        return np.asarray(xgb_probs, dtype=float)
    if xgb_probs is None:
        return np.asarray(rf_probs, dtype=float)
    p = float(rf_weight) * np.asarray(rf_probs, dtype=float) + float(xgb_weight) * np.asarray(xgb_probs, dtype=float)
    s = p.sum()
    if s > 0:
        p = p / s
    return p


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


# Modules that are small / required for health endpoints and can be safely
# preloaded even on low-memory tiers. XGBoost models + encoders are tiny.
_LIGHT_PRELOAD: List[str] = ["inventory"]  # inventory uses only xgb (~1.3 MB)


def preload_light() -> None:
    """Preload small XGBoost-only modules to warm the cache without using much RAM.

    Used by the lifespan when LAZY_LOAD=1 — avoids the first-request latency for
    lightweight endpoints while still skipping the big RF models.
    """
    for m in _LIGHT_PRELOAD:
        try:
            load_module(m)
        except Exception as exc:  # noqa: BLE001
            log.warning("module %s preload failed: %s", m, exc)


def load_all() -> None:
    """Eager-load all modules. Only used when LAZY_LOAD=0 (e.g. local dev, paid tier)."""
    if LAZY_LOAD:
        log.info("LAZY_LOAD=1 — skipping eager load_all(); modules load on first request.")
        preload_light()
        return
    for m in EXPECTED:
        try:
            load_module(m)
        except Exception as exc:  # noqa: BLE001
            log.warning("module %s failed to load: %s", m, exc)
    missing_appt = list_missing("appointment")
    if missing_appt:
        log.warning("Appointment module missing files (GitHub 25 MB limit?): %s — using XGB only.",
                    ", ".join(missing_appt))
    if SKIP_RF_MODELS:
        log.info("SKIP_RF_MODELS=1 — RandomForest models skipped to fit within memory limit.")

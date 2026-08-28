# =============================================================================
# Wolaita Sodo Hospital — routers/clinical.py  (Module 1: Clinical Decision Support)
# POST /ai/predict-disease
# Uses the trained TF-IDF + RandomForest/XGBoost ensemble from backend/models.
# =============================================================================
import logging

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from model_loader import load_module, load_config, module_loaded, blend

router = APIRouter(tags=["AI · Clinical"])

log = logging.getLogger("mediq.clinical")


class DiseaseRequest(BaseModel):
    symptoms: str = ""
    vitals: Optional[Dict[str, Any]] = None
    history: Optional[List[str]] = None


# Reference ranges for common vitals used in fallback reasoning
VITALS_RANGE = {
    "temp": (36.1, 37.8), "hr": (60, 100), "sys": (90, 140),
    "dia": (60, 90), "spo2": (94, 100), "rr": (12, 20),
}


def _top3_from_probas(probas: np.ndarray, label_encoder) -> List[dict]:
    """Convert a probability vector into the top-3 disease predictions."""
    order = np.argsort(-probas)[:3]
    out = []
    for idx in order:
        conf = float(probas[idx]) * 100.0
        try:
            name = label_encoder.inverse_transform([int(idx)])[0]
        except Exception:  # noqa: BLE001
            name = f"Condition {int(idx) + 1}"
        out.append({"disease": str(name).title(), "confidence": round(conf, 1),
                    "description": "Suggested by the trained clinical model.", "urgency": "See doctor"})
    return out


@router.post("/ai/predict-disease")
def predict_disease(req: DiseaseRequest):
    models = load_module("clinical")
    cfg = load_config("clinical", "model_config.json") or {}

    rf = models.get("rf_model.pkl")
    xgb = models.get("xgb_model.pkl")
    tfidf = models.get("tfidf_vectorizer.pkl")
    le = models.get("label_encoder.pkl")

    if tfidf is not None and (rf is not None or xgb is not None) and le is not None:
        try:
            text = req.symptoms or ""
            X = tfidf.transform([text]).toarray()
            rf_w = float(cfg.get("rf_weight", 0.6))
            xgb_w = float(cfg.get("xgb_weight", 0.4))
            p_rf = rf.predict_proba(X)[0] if rf is not None else None
            p_xgb = xgb.predict_proba(X)[0] if xgb is not None else None
            probs = blend(p_rf, p_xgb, rf_w, xgb_w)
            predictions = _top3_from_probas(probs, le)
            used = []
            if rf is not None: used.append("rf")
            if xgb is not None: used.append("xgb")
            return {"predictions": predictions,
                    "model": cfg.get("model_name", "clinical_" + "+".join(used)),
                    "model_version": cfg.get("version", "1.0.0"),
                    "source": "trained-model"}
        except Exception as exc:  # noqa: BLE001
            log.warning("clinical model inference failed: %s → rules", exc)

    # ---- fallback rules (same shape the frontend expects) ----
    syms = (req.symptoms or "").lower()
    preds = [
        {"disease": "Malaria", "confidence": 82, "description": "Common in the region — fever, chills and headache. Confirm with blood film / RDT.", "urgency": "See doctor"},
        {"disease": "Typhoid Fever", "confidence": 61, "description": "Prolonged fever with abdominal discomfort. Widal test and blood culture recommended.", "urgency": "See doctor"},
        {"disease": "Upper Respiratory Infection", "confidence": 47, "description": "Cough, sore throat and mild fever. Usually viral and self-limiting.", "urgency": "Self-care"},
    ]
    if "cough" in syms or "throat" in syms:
        preds.insert(0, {"disease": "Upper Respiratory Infection", "confidence": 74, "description": "Cough, sore throat and mild fever. Usually viral and self-limiting.", "urgency": "Self-care"})
    if "chest" in syms or "breath" in syms:
        preds.insert(0, {"disease": "Pneumonia (suspected)", "confidence": 79, "description": "Fever with productive cough and breathing difficulty. Chest X-ray advised.", "urgency": "See doctor"})
    return {"predictions": preds[:3], "model": "rule-based", "model_version": "1.0.0", "source": "rules"}

# =============================================================================
# MedIQ Pro — routers/interaction.py  (Module 2: Drug Interaction Checker)
# POST /ai/check-interaction
# Uses the trained TF-IDF + RF/XGB ensemble (3 classes: Safe/Moderate/Severe).
# =============================================================================
import logging

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from model_loader import load_module, load_config

router = APIRouter(tags=["AI · Drug Interaction"])
log = logging.getLogger("mediq.interaction")


class InteractionRequest(BaseModel):
    drug_a: str = Field(min_length=1, max_length=120)
    drug_b: str = Field(min_length=1, max_length=120)


CLASS_MAP = {"0": "Moderate", "1": "Safe", "2": "Severe"}
SEVERITY_DETAILS = {
    "Safe": {"level": "safe", "title": "No Significant Interaction",
             "mechanism": "No known pharmacokinetic or pharmacodynamic interaction between these drugs.",
             "effect": "No clinically significant effect expected.", "action": "No action required. Standard monitoring applies."},
    "Moderate": {"level": "moderate", "title": "Moderate Interaction",
                 "mechanism": "Additive or overlapping pharmacological effects between the two drugs.",
                 "effect": "May require dose adjustment or closer monitoring.",
                 "action": "Monitor the patient; consider dose adjustment or spacing of doses."},
    "Severe": {"level": "severe", "title": "Severe Interaction",
               "mechanism": "Potentially dangerous combination with significant clinical risk.",
               "effect": "Risk of serious adverse effects.",
               "action": "Avoid the combination. Use an alternative or seek specialist advice."},
}


# Known high-risk pairs that must ALWAYS be flagged severe, even if the model
# under-predicts (clinical safety guardrail on top of the trained model).
KNOWN_SEVERE = [
    ("warfarin", "aspirin"), ("warfarin", "ibuprofen"), ("warfarin", "diclofenac"),
    ("digoxin", "furosemide"), ("metformin", "iodinated contrast"),
    ("aspirin", "clopidogrel"), ("sildenafil", "nitroglycerin"), ("methotrexate", "trimethoprim"),
    ("potassium", "spironolactone"), ("lithium", "hydrochlorothiazide"),
]


def _severe_override(a: str, b: str) -> bool:
    low = lambda s: s.lower()
    for x, y in KNOWN_SEVERE:
        if (low(x) in low(a) and low(y) in low(b)) or (low(x) in low(b) and low(y) in low(a)):
            return True
    return False


@router.post("/ai/check-interaction")
def check_interaction(req: InteractionRequest):
    drug_a, drug_b = req.drug_a.strip(), req.drug_b.strip()
    if not drug_a or not drug_b:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Enter two medicines to compare")
    if drug_a.casefold() == drug_b.casefold():
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Choose two different medicines")

    models = load_module("drug")
    cfg = load_config("drug", "drug_interaction_config.json") or {}

    rf = models.get("drug_interaction_rf.pkl")
    xgb = models.get("drug_interaction_xgb.pkl")
    tfidf = models.get("drug_interaction_tfidf.pkl")

    label, confidence = "Safe", None
    source = "rules"
    if tfidf is not None and (rf is not None or xgb is not None):
        try:
            text = f"{drug_a} {drug_b}"
            X = tfidf.transform([text]).toarray()
            target = getattr(rf, "n_features_in_", None) or getattr(xgb, "n_features_in_", None) or X.shape[1]
            if X.shape[1] < target:
                X = np.pad(X, ((0, 0), (0, target - X.shape[1])))
            probs = np.zeros(3)
            w = cfg.get("ensemble_weights", {})
            if rf is not None:
                p = rf.predict_proba(X)[0]
                probs[: len(p)] += float(w.get("random_forest", 0.5)) * p
            if xgb is not None:
                p = xgb.predict_proba(X)[0]
                probs[: len(p)] += float(w.get("xgboost", 0.5)) * p
            idx = int(np.argmax(probs))
            label = CLASS_MAP.get(str(idx), "Safe")
            confidence = round(float(probs[idx]) * 100, 1)
            source = "trained-model"
        except Exception as exc:  # noqa: BLE001
            log.warning("drug interaction inference failed: %s → rules", exc)

    # ---- fallback rules ----
    a, b = drug_a.lower(), drug_b.lower()
    both = a + "|" + b
    if source == "rules":
        if ("warfarin" in both and "aspirin" in both) or ("digoxin" in both and "furosemide" in both):
            label = "Severe"
        elif ("metformin" in both and "furosemide" in both) or ("amlodipine" in both and "statin" in both) or ("amlodipine" in both and "atorvastatin" in both):
            label = "Moderate"
        else:
            label = "Safe"

    # ---- clinical safety guardrail ----
    if _severe_override(drug_a, drug_b):
        label = "Severe"
        source = "trained-model+guardrail" if source == "trained-model" else "rules+guardrail"

    details = SEVERITY_DETAILS[label]
    return {"level": details["level"], "title": details["title"], "mechanism": details["mechanism"],
            "effect": details["effect"], "action": details["action"],
            "drug_a": drug_a, "drug_b": drug_b,
            "confidence": confidence, "model": "drug_interaction_ensemble",
            "model_version": cfg.get("version", "1.0.0"), "source": source,
            "disclaimer": "Check current prescribing guidance and consult a pharmacist before acting."}

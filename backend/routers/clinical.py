# =============================================================================
# Wolaita Sodo Hospital — routers/clinical.py  (Module 1: Clinical Decision Support)
# POST /ai/predict-disease
# Uses the trained TF-IDF + RandomForest/XGBoost ensemble from backend/models.
# =============================================================================
import base64
import io
import logging
import re
import secrets
from datetime import date

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from db import insert_row
from model_loader import load_module, load_config, module_loaded, blend
from security import current_user

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


def _extract_file_text(name: str, raw: bytes, mime: str) -> str:
    """Read a new clinical file. Images are rejected instead of guessed."""
    lower = (name or "").lower()
    if lower.endswith((".txt", ".csv", ".md", ".json")) or (mime or "").startswith("text/"):
        return raw.decode("utf-8", errors="ignore")
    if lower.endswith(".docx"):
        from docx import Document
        document = Document(io.BytesIO(raw))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    if lower.endswith(".pdf") or mime == "application/pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join((page.extract_text() or "") for page in reader.pages[:20])
        except Exception:  # noqa: BLE001
            parts = re.findall(rb"\((?:\\\)|\\.|[^\\)]){2,}\)", raw)
            return " ".join(part[1:-1].decode("latin-1", errors="ignore") for part in parts[:400])
    raise HTTPException(status_code=400, detail="Use a text, Word, or PDF file. A photo cannot be read as a clinical note.")


def _predict_from_text(text: str) -> dict:
    models = load_module("clinical")
    cfg = load_config("clinical", "model_config.json") or {}

    rf = models.get("rf_model.pkl")
    xgb = models.get("xgb_model.pkl")
    tfidf = models.get("tfidf_vectorizer.pkl")
    le = models.get("label_encoder.pkl")

    if tfidf is not None and (rf is not None or xgb is not None) and le is not None:
        try:
            X = tfidf.transform([text or ""]).toarray()
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

    return None


@router.post("/ai/predict-disease")
def predict_disease(req: DiseaseRequest):
    trained = _predict_from_text(req.symptoms or "")
    if trained:
        return trained

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


@router.post("/ai/clinical-decision/file")
async def clinical_decision_from_file(
    file: UploadFile = File(...),
    patient: str = Form(""),
    title: str = Form(""),
    user=Depends(current_user),
):
    """Read a new file, run the trained clinical model, then save both in Supabase."""
    if user.get("role") not in {"doctor", "admin"}:
        raise HTTPException(status_code=403, detail="Only a doctor can file a clinical decision")
    name = (patient or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Enter the patient name")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Choose a file")
    if len(raw) > 1_200_000:
        raise HTTPException(status_code=413, detail="File is too large. Use a file under 1.2 MB.")
    text = _extract_file_text(file.filename or "", raw, file.content_type or "").strip()
    if len(text) < 8:
        raise HTTPException(status_code=400, detail="No readable clinical text was found in that file.")
    trained = _predict_from_text(text[:8000])
    if not trained or not trained.get("predictions"):
        raise HTTPException(status_code=503, detail="AI module unavailable")
    top = trained["predictions"][0]
    mime = file.content_type or "application/octet-stream"
    row = {
        "id": "CD-" + secrets.token_hex(4).upper(),
        "patient": name,
        "patient_id": "",
        "type": "Clinical Decision",
        "title": (title or "").strip() or (file.filename or "Clinical decision"),
        "date": date.today().isoformat(),
        "size": str(max(1, round(len(raw) / 1024))) + " KB",
        "uploaded_by": user.get("name") or user.get("email") or "",
        "summary": top.get("disease", "Decision") + " (" + str(top.get("confidence")) + "%). From uploaded file.",
        "file_name": file.filename or "clinical-file",
        "file_mime": mime,
        "file_data": "data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii"),
        "prediction": top.get("disease") or "",
        "confidence": top.get("confidence"),
        "predictions": trained.get("predictions") or [],
        "model": trained.get("model") or "",
        "model_version": trained.get("model_version") or "",
    }
    saved = insert_row("documents", row)
    if saved.get("ok") is False:
        raise HTTPException(status_code=503, detail=saved.get("error") or "Could not save the clinical decision")
    stored = saved.get("row") or {}
    stored.pop("file_data", None)
    return {
        "ok": True,
        "saved": True,
        "document_id": stored.get("id") or row["id"],
        "predictions": trained["predictions"],
        "model": trained.get("model"),
        "model_version": trained.get("model_version"),
        "source": trained.get("source"),
        "disclaimer": "This is an AI-assisted suggestion. Always consult a qualified medical professional before making clinical decisions.",
    }

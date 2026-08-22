# =============================================================================
# MedIQ Pro — backend/main.py
# FastAPI application — all 7 AI modules + auth + Supabase-backed data CRUD.
#
# Run locally:   uvicorn main:app --reload --port 8000
# Deploy:        Render  →  Root Directory: backend
#                Build:   pip install -r requirements.txt
#                Start:   uvicorn main:app --host 0.0.0.0 --port 10000
#
# Memory-safe for Render free tier (~512 MB):
#   * Large RandomForest models are skipped (XGBoost-only inference).
#   * Models are lazy-loaded on first request instead of at startup.
#   Override with env vars: LAZY_LOAD=0, SKIP_RF_MODELS=0 for paid tiers.
# =============================================================================
import gc
import logging
import os
import resource
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, MODEL_DOWNLOAD_URLS, LAZY_LOAD, SKIP_RF_MODELS, LOW_MEMORY
import model_loader
from security import current_user
from routers import auth, clinical, interaction, lab, vitals, inventory, appointment, chatbot, data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mediq")


def _log_memory(tag: str = "") -> None:
    try:
        ru = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is KB on Linux
        mb = ru.ru_maxrss / 1024.0
        log.info("mem[%s] %.1f MB (max RSS)%s", tag or "-", mb,
                 "  [low-memory mode]" if LOW_MEMORY else "")
    except Exception:  # noqa: BLE001
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("MedIQ Pro starting (LAZY_LOAD=%s, SKIP_RF_MODELS=%s, LOW_MEMORY=%s)",
             LAZY_LOAD, SKIP_RF_MODELS, LOW_MEMORY)

    # 1) In eager mode, try to fetch any missing >25 MB model files.
    #    In lazy/low-mem mode we skip this: we won't load the RF anyway.
    if MODEL_DOWNLOAD_URLS and not SKIP_RF_MODELS:
        import download_models
        try:
            download_models.main()
        except Exception as exc:  # noqa: BLE001
            log.warning("model download step skipped: %s", exc)

    # 2) Load models. In lazy mode this only preloads a tiny warmup set.
    model_loader.load_all()
    gc.collect()
    _log_memory("post-init")
    log.info("MedIQ Pro API ready.")
    yield
    _log_memory("shutdown")


app = FastAPI(title="MedIQ Pro API", version="2.0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODULES = ["clinical", "drug", "lab", "vitals", "inventory", "appointment", "symptom"]


# ---- health ----
@app.get("/")
def root():
    return {"status": "ok", "service": "MedIQ Pro API", "version": "2.0.1",
            "low_memory": LOW_MEMORY,
            "lazy_load": LAZY_LOAD,
            "skip_rf_models": SKIP_RF_MODELS,
            "models": {m: model_loader.module_loaded(m) for m in MODULES}}


@app.get("/health")
def health():
    return {"status": "ok", "models": {m: model_loader.module_loaded(m) for m in MODULES}}


@app.get("/debug/memory")
def debug_memory():
    """Diagnostic endpoint — returns current RSS memory usage."""
    try:
        ru = resource.getrusage(resource.RUSAGE_SELF)
        mb = ru.ru_maxrss / 1024.0
    except Exception:  # noqa: BLE001
        mb = -1
    return {
        "max_rss_mb": round(mb, 1),
        "low_memory": LOW_MEMORY,
        "lazy_load": LAZY_LOAD,
        "skip_rf_models": SKIP_RF_MODELS,
        "loaded_modules": {m: model_loader.module_loaded(m) for m in MODULES},
    }


# ---- routers ----
app.include_router(auth.router)
# All data and AI routes require a signed application token. Auth routes above
# remain public so users can sign in or request registration/reset.
protected = {"dependencies": [Depends(current_user)]}
app.include_router(clinical.router, **protected)
app.include_router(interaction.router, **protected)
app.include_router(lab.router, **protected)
app.include_router(vitals.router, **protected)
app.include_router(inventory.router, **protected)
app.include_router(appointment.router, **protected)
app.include_router(chatbot.router, **protected)
app.include_router(data.router)

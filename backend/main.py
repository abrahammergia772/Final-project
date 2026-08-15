# =============================================================================
# MedIQ Pro — backend/main.py
# FastAPI application — all 7 AI modules + auth + Supabase-backed data CRUD.
#
# Run locally:   uvicorn main:app --reload --port 8000
# Deploy:        Render  →  Root Directory: backend
#                Build:   pip install -r requirements.txt
#                Start:   uvicorn main:app --host 0.0.0.0 --port 10000
# =============================================================================
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, MODEL_DOWNLOAD_URLS
import model_loader
from routers import auth, clinical, interaction, lab, vitals, inventory, appointment, chatbot, data

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mediq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) try to fetch any missing >25 MB model files (appointment RF)
    if MODEL_DOWNLOAD_URLS:
        import download_models
        try:
            download_models.main()
        except Exception as exc:  # noqa: BLE001
            log.warning("model download step skipped: %s", exc)
    # 2) load all trained models (missing files → graceful fallback)
    model_loader.load_all()
    log.info("MedIQ Pro API ready.")
    yield


app = FastAPI(title="MedIQ Pro API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- health ----
@app.get("/")
def root():
    return {"status": "ok", "service": "MedIQ Pro API", "version": "2.0.0",
            "models": {m: model_loader.module_loaded(m) for m in [
                "clinical", "drug", "lab", "vitals", "inventory", "appointment", "symptom"]}}


@app.get("/health")
def health():
    return {"status": "ok", "models": {m: model_loader.module_loaded(m) for m in [
        "clinical", "drug", "lab", "vitals", "inventory", "appointment", "symptom"]}}


# ---- routers ----
app.include_router(auth.router)
app.include_router(clinical.router)
app.include_router(interaction.router)
app.include_router(lab.router)
app.include_router(vitals.router)
app.include_router(inventory.router)
app.include_router(appointment.router)
app.include_router(chatbot.router)
app.include_router(data.router)

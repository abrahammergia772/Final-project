"""MedIQ Pro FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS, MODEL_DOWNLOAD_URLS, public_config
import model_loader
from security import current_user
from routers import appointment, auth, chatbot, clinical, data, interaction, inventory, lab, vitals


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("mediq")
MODULES = ["clinical", "drug", "lab", "vitals", "inventory", "appointment", "symptom"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Download optional model assets and load models once per worker."""
    if MODEL_DOWNLOAD_URLS:
        import download_models

        try:
            download_models.main()
        except Exception as exc:  # noqa: BLE001
            # A missing optional model must not take down the whole API.
            log.warning("Optional model download skipped: %s", exc)
    model_loader.load_all()
    log.info("MedIQ Pro API ready")
    yield


app = FastAPI(
    title="MedIQ Pro API",
    version="2.1.0",
    description="Authenticated AI-assisted hospital management services.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add browser hardening headers without affecting the JSON API contract."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


def _model_status() -> dict[str, bool]:
    return {module: model_loader.module_loaded(module) for module in MODULES}


@app.get("/", tags=["System"])
def root():
    return {"status": "ok", "service": "MedIQ Pro API", "version": app.version, "models": _model_status()}


@app.get("/health", tags=["System"])
def health():
    """Render health check; returns diagnostics without exposing secrets."""
    return {
        "status": "ok",
        "models": _model_status(),
        "configuration": public_config(),
    }


# Auth remains public so users can sign in, register, and request a reset code.
app.include_router(auth.router)

# Every AI route requires a signed application token.
protected = {"dependencies": [Depends(current_user)]}
for router in (clinical.router, interaction.router, lab.router, vitals.router,
               inventory.router, appointment.router, chatbot.router):
    app.include_router(router, **protected)

# Data routes apply their own resource and operation authorization checks.
app.include_router(data.router)

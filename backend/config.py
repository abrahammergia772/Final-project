"""Application configuration for MedIQ Pro.

Configuration is deliberately kept in environment variables so deployments do
not need a code change for secrets, database connections, or allowed origins.
The module remains safe to import locally, but refuses an unsafe secret in a
production environment.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(BASE_DIR / "models"))).resolve()


def _environment() -> str:
    value = os.getenv("ENVIRONMENT", "").strip().lower()
    if value:
        return value
    # Render sets this automatically. Keep local development friction-free.
    return "production" if os.getenv("RENDER") else "development"


ENVIRONMENT = _environment()
IS_PRODUCTION = ENVIRONMENT in {"production", "prod", "staging"}

# --- Supabase --------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
# Optional: use the service-role key for server-side writes (keep secret!).
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

# --- CORS ------------------------------------------------------------------
def _parse_origins(value: str) -> List[str]:
    return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]


_default_origins = "" if IS_PRODUCTION else "http://localhost:8000,http://127.0.0.1:8000"
CORS_ORIGINS = _parse_origins(os.getenv("CORS_ORIGINS", _default_origins))
if IS_PRODUCTION and "*" in CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS must list explicit origins in production; '*' is unsafe.")

# --- Model download (for .pkl files >25 MB that GitHub rejects) ------------
# Example: appointment_rf=https://.../rf_appointment.pkl
MODEL_DOWNLOAD_URLS = {
    key.strip(): value.strip()
    for key, value in (
        pair.split("=", 1)
        for pair in os.getenv("MODEL_DOWNLOAD_URLS", "").split(",")
        if "=" in pair
    )
    if key.strip() and value.strip()
}

# --- Secrets ---------------------------------------------------------------
_DEV_SECRET = "mediq-pro-dev-secret-change-me"
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError("SECRET_KEY must be configured in production.")
    SECRET_KEY = _DEV_SECRET
elif IS_PRODUCTION and SECRET_KEY == _DEV_SECRET:
    raise RuntimeError("SECRET_KEY must not use the development default in production.")


# --- Demo mode -------------------------------------------------------------
def supabase_configured() -> bool:
    """Return true only when both required Supabase connection values exist."""
    return bool(SUPABASE_URL and SUPABASE_KEY)


def public_config() -> dict:
    """Safe, non-secret configuration details for diagnostics and tests."""
    return {
        "environment": ENVIRONMENT,
        "supabase_configured": supabase_configured(),
        "model_downloads_configured": bool(MODEL_DOWNLOAD_URLS),
        "cors_origins": CORS_ORIGINS,
    }

# =============================================================================
# MedIQ Pro — backend/config.py
# Central configuration read from environment variables (set in Render).
# =============================================================================
import os
from pathlib import Path

# --- Paths -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(BASE_DIR / "models"))).resolve()

# --- Supabase --------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
# Optional: use the service-role key for server-side writes (keep secret!)
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

# --- CORS ------------------------------------------------------------------
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# --- Model download (for .pkl files >25 MB that GitHub rejects) ------------
# e.g. MODEL_DOWNLOAD_URLS = 'appointment_rf=https://github.com/you/repo/releases/download/v1/rf_appointment.pkl'
MODEL_DOWNLOAD_URLS = {
    k.strip(): v.strip()
    for k, v in (p.split("=", 1) for p in os.getenv("MODEL_DOWNLOAD_URLS", "").split(",") if "=" in p)
}

# --- Secrets ---------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "mediq-pro-dev-secret-change-me")

# --- Demo mode -------------------------------------------------------------
# When Supabase is not configured, the API falls back to built-in demo data so
# the system is fully usable end-to-end before Supabase is set up.
def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

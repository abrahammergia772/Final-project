# =============================================================================
# Wolaita Sodo Hospital — backend/config.py
# Central configuration read from environment variables (set in Render).
# =============================================================================
import os
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    """Parse an env var as boolean. Accepts 1/0, true/false, yes/no, on/off."""
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _detect_low_memory() -> bool:
    """Auto-enable memory-saving mode on Render free tier / small containers.

    Looks for Render-specific env vars and cgroup memory limits.
    """
    # Explicit override
    if os.getenv("LOW_MEMORY") is not None:
        return _env_bool("LOW_MEMORY", True)
    # Render exposes RENDER; free tier has ~512 MB
    if os.getenv("RENDER") == "true":
        return True
    # Detect cgroup memory limit (Linux containers)
    try:
        with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
            limit = int(f.read().strip())
            if 0 < limit <= 600 * 1024 * 1024:  # ≤ ~600 MB
                return True
    except (OSError, ValueError):
        pass
    try:
        with open("/sys/fs/cgroup/memory.max") as f:
            v = f.read().strip()
            if v != "max":
                limit = int(v)
                if limit <= 600 * 1024 * 1024:
                    return True
    except (OSError, ValueError):
        pass
    return False


# --- Paths -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(BASE_DIR / "models"))).resolve()

# --- Memory mode (auto-detected; override with env vars) -------------------
LOW_MEMORY = _detect_low_memory()
LAZY_LOAD = _env_bool("LAZY_LOAD", LOW_MEMORY)
SKIP_RF_MODELS = _env_bool("SKIP_RF_MODELS", LOW_MEMORY)

# --- Supabase --------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
# Optional: use the service-role key for server-side writes (keep secret!)
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

# --- CORS ------------------------------------------------------------------
# Default list covers: localhost dev, any Render static site (onrender.com),
# Netlify, Vercel, GitHub Pages, and a custom comma-separated override via env.
_default_cors = (
    "http://localhost:8000,http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500,"
    "http://127.0.0.1:8000,https://*.onrender.com,https://*.netlify.app,"
    "https://*.vercel.app,https://*.github.io"
)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_cors).split(",") if o.strip()]
# Render free-tier / preview: allow wildcard origin in dev by inspecting env
CORS_ALLOW_ALL = _env_bool("CORS_ALLOW_ALL", True)  # safe: auth uses bearer tokens, no cookies

# --- Model download (for .pkl files >25 MB that GitHub rejects) ------------
# e.g. MODEL_DOWNLOAD_URLS = 'appointment_rf=https://github.com/you/repo/releases/download/v1/rf_appointment.pkl'
MODEL_DOWNLOAD_URLS = {
    k.strip(): v.strip()
    for k, v in (p.split("=", 1) for p in os.getenv("MODEL_DOWNLOAD_URLS", "").split(",") if "=" in p)
}
# In low-memory mode we don't even try to download the big RF model (it can't be loaded anyway).
if SKIP_RF_MODELS:
    MODEL_DOWNLOAD_URLS.pop("appointment_rf", None)

# --- Secrets ---------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "mediq-pro-dev-secret-change-me")

# --- Demo mode -------------------------------------------------------------
# When Supabase is not configured, the API falls back to built-in demo data so
# the system is fully usable end-to-end before Supabase is set up.
def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

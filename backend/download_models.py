#!/usr/bin/env python3
# =============================================================================
# Wolaita Sodo Hospital — backend/download_models.py
# SOLUTION FOR GITHUB'S 25 MB FILE LIMIT
# ---------------------------------------------------------------
# GitHub rejects files larger than 25 MB when pushed normally. The trained
# appointment RandomForest model (rf_appointment.pkl) is over that limit.
#
# Two free options:
#
#   OPTION A — GitHub Release asset (RECOMMENDED, works on Render free)
#     1. Create a Release on GitHub (Releases → New release → tag e.g. v1-models)
#     2. Upload rf_appointment.pkl as a Release asset (assets allow up to 2 GB)
#     3. Copy its browser URL, e.g.
#        https://github.com/you/Final-project/releases/download/v1-models/rf_appointment.pkl
#     4. Set env var in Render:
#        MODEL_DOWNLOAD_URLS=appointment_rf=<that-url>
#     5. Render's build (or this script at startup) downloads it into
#        backend/models/appointment/rf_appointment.pkl and the ensemble works.
#
#   OPTION B — Compress the pickle under 25 MB (no external hosting)
#     python -c "import joblib; m=joblib.load('rf_appointment.pkl');
#                joblib.dump(m,'rf_appointment.pkl',compress=3)"
#     If the result is < 25 MB, commit it normally.
#
# Run manually:   python download_models.py
# =============================================================================
import logging
import os
import sys
from pathlib import Path
from urllib.request import urlopen

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("download")

MODELS_DIR = Path(__file__).resolve().parent / "models"

# key -> destination path under backend/models/
DESTINATIONS = {
    "appointment_rf": "appointment/rf_appointment.pkl",
}


def main() -> int:
    urls = {}
    for part in os.getenv("MODEL_DOWNLOAD_URLS", "").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            urls[k.strip()] = v.strip()

    downloaded = 0
    for key, dest_rel in DESTINATIONS.items():
        dest = MODELS_DIR / dest_rel
        if dest.is_file() and dest.stat().st_size > 1024:
            log.info("✓ %s already present (%d KB)", dest_rel, dest.stat().st_size // 1024)
            continue
        url = urls.get(key)
        if not url:
            log.warning("· %s missing and no URL configured — skipping (set MODEL_DOWNLOAD_URLS)", dest_rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        log.info("↓ downloading %s from %s", dest_rel, url)
        try:
            with urlopen(url, timeout=120) as r, open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            log.info("✓ saved %s (%d KB)", dest_rel, dest.stat().st_size // 1024)
            downloaded += 1
        except Exception as exc:  # noqa: BLE001
            log.error("✗ failed to download %s: %s", dest_rel, exc)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

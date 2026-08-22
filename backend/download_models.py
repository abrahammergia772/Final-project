#!/usr/bin/env python3
"""Download optional model assets that are too large for a normal Git commit.

The downloader is intentionally conservative: only HTTPS URLs are accepted,
files are size-limited, and writes are atomic so a failed deploy cannot leave a
truncated pickle that looks valid to the model loader.
"""
from __future__ import annotations

import hashlib
import logging
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("download")
MODELS_DIR = Path(__file__).resolve().parent / "models"
MAX_MODEL_BYTES = 250 * 1024 * 1024
DESTINATIONS = {"appointment_rf": "appointment/rf_appointment.pkl"}


def _configured_urls() -> dict[str, str]:
    return {
        key.strip(): value.strip()
        for key, value in (
            part.split("=", 1)
            for part in os.getenv("MODEL_DOWNLOAD_URLS", "").split(",")
            if "=" in part
        )
        if key.strip() and value.strip()
    }


def _download(url: str, destination: Path) -> int:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("model URLs must use HTTPS")

    request = Request(url, headers={"User-Agent": "MedIQ-Pro-model-loader/1.0"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    digest = hashlib.sha256()
    temp_name = None
    try:
        with urlopen(request, timeout=120) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_MODEL_BYTES:
                raise ValueError("remote model exceeds the size limit")
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
            ) as handle:
                temp_name = handle.name
                while chunk := response.read(1 << 20):
                    total += len(chunk)
                    if total > MAX_MODEL_BYTES:
                        raise ValueError("remote model exceeds the size limit")
                    digest.update(chunk)
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        if total <= 1024:
            raise ValueError("remote model is unexpectedly small")
        os.replace(temp_name, destination)
        return total
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    urls = _configured_urls()
    for key, destination_rel in DESTINATIONS.items():
        destination = MODELS_DIR / destination_rel
        if destination.is_file() and 1024 < destination.stat().st_size <= MAX_MODEL_BYTES:
            log.info("✓ %s already present (%d KB)", destination_rel, destination.stat().st_size // 1024)
            continue
        url = urls.get(key)
        if not url:
            log.warning("· %s missing and no URL configured — skipping", destination_rel)
            continue
        try:
            size = _download(url, destination)
            log.info("✓ saved %s (%d KB)", destination_rel, size // 1024)
        except Exception as exc:  # noqa: BLE001
            log.error("✗ failed to download %s: %s", destination_rel, exc)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

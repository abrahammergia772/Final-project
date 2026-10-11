"""Smoke tests — the API process starts and the public health routes answer.

Run from backend/:
    LAZY_LOAD=1 SKIP_RF_MODELS=1 python -m pytest tests/test_smoke.py
"""
import os

os.environ.setdefault("LAZY_LOAD", "1")
os.environ.setdefault("SKIP_RF_MODELS", "1")
os.environ.setdefault("LOW_MEMORY", "1")

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

import main


def test_health_and_root():
    with TestClient(main.app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        root = client.get("/")
        assert root.status_code == 200
        assert root.json()["service"] == "Wolaita Sodo Hospital API"


def test_reset_does_not_reveal_a_code(monkeypatch):
    for name in ("BREVO_API_KEY", "SENDGRID_API_KEY", "RESEND_API_KEY", "MAIL_FROM", "SMTP_HOST", "SMTP_PASSWORD"):
        monkeypatch.delenv(name, raising=False)
    with TestClient(main.app) as client:
        res = client.post("/auth/reset-password", json={"email": "person@example.com"})
        assert res.status_code == 503
        body = res.json()
        assert "code" not in body
        assert "not set up" in str(body.get("detail") or "").lower()


def test_debug_memory_requires_auth():
    with TestClient(main.app) as client:
        res = client.get("/debug/memory")
        assert res.status_code in (401, 403)

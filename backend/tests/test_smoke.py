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


def test_debug_memory_requires_auth():
    with TestClient(main.app) as client:
        res = client.get("/debug/memory")
        assert res.status_code in (401, 403)

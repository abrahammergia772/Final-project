"""Password-reset code storage and mail provider selection. No network."""
import os

os.environ.setdefault("LAZY_LOAD", "1")
os.environ.setdefault("SKIP_RF_MODELS", "1")
os.environ.setdefault("LOW_MEMORY", "1")

import sys
import types

if "fastapi" not in sys.modules:
    fastapi = types.ModuleType("fastapi")
    fastapi.Depends = lambda *args, **kwargs: None
    fastapi.HTTPException = Exception
    fastapi.status = types.SimpleNamespace()
    sys.modules["fastapi"] = fastapi
    security_mod = types.ModuleType("fastapi.security")
    security_mod.HTTPAuthorizationCredentials = object
    security_mod.HTTPBearer = lambda *args, **kwargs: None
    sys.modules["fastapi.security"] = security_mod

import mailer
import reset_otp
from security import hash_password, password_saved, verify_password


def test_saved_password_replaces_the_old_one():
    old_hash = hash_password("old-password")
    new_hash = hash_password("new-password-1")
    assert password_saved("new-password-1", new_hash, old_hash)
    assert verify_password("new-password-1", new_hash)
    assert not verify_password("old-password", new_hash)
    assert not password_saved("old-password", old_hash, old_hash)
    assert not password_saved("new-password-1", old_hash, old_hash)


def test_seal_round_trip():
    blob = reset_otp.seal("482913", "test-secret", 1_700_000_600)
    assert reset_otp.sealed_matches("482913", blob, "test-secret", now=1_700_000_100)
    assert not reset_otp.sealed_matches("000000", blob, "test-secret", now=1_700_000_100)
    assert not reset_otp.sealed_matches("482913", blob, "other-secret", now=1_700_000_100)
    assert not reset_otp.sealed_matches("482913", blob, "test-secret", now=1_700_000_700)


def test_memory_code_expires():
    reset_otp.remember("person@example.com", "123456", now=100)
    assert reset_otp.memory_matches("person@example.com", "123456", now=200)
    assert not reset_otp.memory_matches("person@example.com", "123456", now=100 + reset_otp.TTL + 1)
    reset_otp.forget("person@example.com")
    assert not reset_otp.memory_matches("person@example.com", "123456", now=200)


def test_mail_not_configured_without_keys(monkeypatch):
    for name in ("BREVO_API_KEY", "SENDGRID_API_KEY", "RESEND_API_KEY", "MAIL_FROM", "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_PORT", "MAIL_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    assert mailer.configured() is False
    assert mailer.provider_name() == ""


def test_gmail_smtp_is_not_used_on_render_free(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "ward@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("MAIL_FROM", "ward@example.com")
    monkeypatch.delenv("BREVO_API_KEY", raising=False)
    assert mailer.configured() is False


def test_messy_brevo_key_is_cleaned():
    assert mailer._normalize_secret("api-key: xkeysib-abc123") == "xkeysib-abc123"
    assert mailer._normalize_secret("  xkeysib-abc123  ") == "xkeysib-abc123"
    assert mailer._normalize_secret("SMTP key xsmtpsib-secret") == "xsmtpsib-secret"


def test_brevo_key_name_is_not_case_sensitive(monkeypatch):
    monkeypatch.delenv("BREVO_API_KEY", raising=False)
    monkeypatch.setenv("brevo-api-key", "xkeysib-test")
    monkeypatch.setenv("MAIL_FROM", "wolaitasodo2026@gmail.com")
    assert mailer.provider_name() == "brevo"


def test_brevo_is_selected_when_configured(monkeypatch):
    monkeypatch.setenv("BREVO_API_KEY", "xkeysib-test")
    monkeypatch.setenv("MAIL_FROM", "ward@example.com")
    assert mailer.provider_name() == "brevo"
    subject, text, html = mailer._messages("Abebe", "482913")
    assert "482913" in text and "482913" in html
    assert "Abebe" in subject or "reset code" in subject

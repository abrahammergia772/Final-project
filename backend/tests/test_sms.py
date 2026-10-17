"""Africa's Talking reminder SMS does not call the network in these tests."""
import os

from sms import normalize_phone, send_sms


def test_ethiopian_numbers_become_e164():
    assert normalize_phone("0911234567") == "+251911234567"
    assert normalize_phone("+251 911 234 567") == "+251911234567"
    assert normalize_phone("711234567") == "+251711234567"
    assert normalize_phone("not a phone") == ""


def test_missing_key_does_not_send(monkeypatch):
    monkeypatch.delenv("AT_API_KEY", raising=False)
    monkeypatch.delenv("AT_USERNAME", raising=False)
    result = send_sms("0911234567", "Visit reminder")
    assert result["ok"] is False
    assert result["status"] == "not-configured"
    assert "AT_API_KEY" not in os.environ or os.environ.get("AT_API_KEY", "") == ""

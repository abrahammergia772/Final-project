"""Africa's Talking reminder SMS does not call the network in these tests."""
import json
import os

from sms import interpret_sms_response, normalize_phone, send_sms


def test_ethiopian_numbers_become_e164():
    assert normalize_phone("0911234567") == "+251911234567"
    assert normalize_phone("+251 911 234 567") == "+251911234567"
    assert normalize_phone("711234567") == "+251711234567"
    assert normalize_phone("not a phone") == ""


def test_xml_success_counts_as_accepted():
    body = "<AfricasTalkingResponse><SMSMessageData><Message>Sent to 1/1</Message><Recipients><Recipient><status>Success</status><statusCode>101</statusCode></Recipient></Recipients></SMSMessageData></AfricasTalkingResponse>"
    result = interpret_sms_response(201, body, "+251911234567")
    assert result["ok"] is True
    assert result["status"] == "sent"


def test_invalid_phone_names_the_number():
    body = json.dumps({"SMSMessageData": {"Message": "Sent to 0/1", "Recipients": [{"statusCode": 403, "status": "InvalidPhoneNumber", "number": "+251911234567"}]}})
    result = interpret_sms_response(201, body, "+251911234567")
    assert result["ok"] is False
    assert "+251911234567" in result["detail"]


def test_low_balance_is_named():
    body = json.dumps({"SMSMessageData": {"Message": "Sent to 0/1", "Recipients": [{"statusCode": 405, "status": "InsufficientBalance"}]}})
    result = interpret_sms_response(201, body, "+251911234567")
    assert result["ok"] is False
    assert "balance" in result["detail"].lower()


def test_http_error_body_is_kept():
    result = interpret_sms_response(401, "Invalid API key", "")
    assert result["ok"] is False
    assert "username or API key" in result["detail"]


def test_missing_key_does_not_send(monkeypatch):
    monkeypatch.delenv("AT_API_KEY", raising=False)
    monkeypatch.delenv("AT_USERNAME", raising=False)
    result = send_sms("0911234567", "Visit reminder")
    assert result["ok"] is False
    assert result["status"] == "not-configured"
    assert "AT_API_KEY" not in os.environ or os.environ.get("AT_API_KEY", "") == ""

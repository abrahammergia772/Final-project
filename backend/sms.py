# Appointment reminder SMS through Africa's Talking.
# The API key stays in the Render environment. Never log it or return it.
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

SUCCESS_CODES = {100, 101, 102}


def _env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip().strip('"').strip("'")
        if value:
            return value
    return ""


def configured() -> bool:
    return bool(_env("AT_API_KEY") and _env("AT_USERNAME", "AFRICASTALKING_USERNAME"))


def normalize_phone(raw) -> str:
    text = str(raw or "").strip()
    digits = re.sub(r"\D", "", text)
    if digits.startswith("251") and len(digits) == 12:
        return "+" + digits
    if digits.startswith("0") and len(digits) == 10 and digits[1] in "79":
        return "+251" + digits[1:]
    if len(digits) == 9 and digits[0] in "79":
        return "+251" + digits
    if text.startswith("+") and re.fullmatch(r"\+\d{10,15}", text):
        return text
    return ""


def send_sms(phone, message: str) -> dict:
    key = _env("AT_API_KEY")
    username = _env("AT_USERNAME", "AFRICASTALKING_USERNAME")
    number = normalize_phone(phone)
    if not key:
        return {"ok": False, "status": "not-configured", "detail": "AT_API_KEY is not set on this service"}
    if not username:
        return {"ok": False, "status": "missing-username", "detail": "Add the Africa's Talking app username as AT_USERNAME"}
    if not number:
        return {"ok": False, "status": "no-phone", "detail": "No usable phone number on the patient record"}
    host = "api.sandbox.africastalking.com" if username == "sandbox" else "api.africastalking.com"
    fields = {
        "username": username,
        "to": number,
        "message": str(message or "").replace("\r\n", "\n").replace("\n", "\r\n")[:320],
        "bulkSMSMode": "1",
    }
    sender = _env("AT_SENDER_ID", "AFRICASTALKING_SENDER_ID")
    if sender:
        fields["from"] = sender
    request = urllib.request.Request(
        "https://" + host + "/version1/messaging",
        data=urllib.parse.urlencode(fields).encode(),
        method="POST",
    )
    request.add_header("Accept", "application/json")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    request.add_header("apiKey", key)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": "failed", "detail": "Africa's Talking rejected the reminder (" + str(exc.code) + ")"}
    except Exception:
        return {"ok": False, "status": "failed", "detail": "Africa's Talking could not be reached"}
    try:
        parsed = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {"ok": False, "status": "failed", "detail": "Africa's Talking returned an unreadable response"}
    recipients = ((parsed.get("SMSMessageData") or {}).get("Recipients") or [])
    first = recipients[0] if recipients else {}
    try:
        code = int(first.get("statusCode") or 0)
    except (TypeError, ValueError):
        code = 0
    if code in SUCCESS_CODES:
        return {"ok": True, "status": "sent", "detail": str(first.get("status") or "Sent")}
    detail = str(first.get("status") or (parsed.get("SMSMessageData") or {}).get("Message") or "Africa's Talking did not accept the reminder")
    return {"ok": False, "status": "failed", "detail": detail[:180]}

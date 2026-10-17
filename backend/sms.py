# Appointment reminder SMS through Africa's Talking.
# The API key stays in the Render environment. Never log it or return it.
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

SUCCESS_CODES = {100, 101, 102}
SUCCESS_WORDS = {"success", "sent", "queued", "processed"}


def _env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip().strip('"').strip("'")
        if value:
            return value
    return ""


def _api_key() -> str:
    value = _env("AT_API_KEY")
    for prefix in ("apiKey ", "ApiKey ", "apikey ", "Bearer "):
        if value.startswith(prefix):
            value = value[len(prefix):].strip()
    return value


def configured() -> bool:
    return bool(_api_key() and _env("AT_USERNAME", "AFRICASTALKING_USERNAME"))


def normalize_phone(raw) -> str:
    text = str(raw or "").strip()
    digits = re.sub(r"\D", "", text)
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("2510") and len(digits) == 13:
        digits = "251" + digits[4:]
    if digits.startswith("251") and len(digits) == 12 and digits[3] in "79":
        return "+" + digits
    if digits.startswith("0") and len(digits) == 10 and digits[1] in "79":
        return "+251" + digits[1:]
    if len(digits) == 9 and digits[0] in "79":
        return "+251" + digits
    compact = "+" + digits if digits else ""
    if compact.startswith("+") and re.fullmatch(r"\+\d{10,15}", compact):
        return compact
    return ""


def _reason(code: int, status: str, message: str, number: str, http_code: int) -> str:
    text = str(status or message or "").strip()
    folded = re.sub(r"\s+", "", text.lower())
    if http_code == 401 or "invalidapi" in folded or "authentication" in folded or "invalidusername" in folded:
        return "Africa's Talking rejected the app username or API key. The username must belong to that key. The sandbox username is sandbox."
    if code == 403 or "invalidphone" in folded:
        shown = number or "saved on the visit"
        return "Africa's Talking rejected the phone number " + shown + "."
    if code == 405 or "insufficientbalance" in folded:
        return "Africa's Talking balance is too low to send this SMS."
    if code == 402 or "invalidsender" in folded:
        return "The sender ID is not registered for this SMS."
    if code == 407 or "couldnotroute" in folded:
        return "Africa's Talking could not route this SMS to the phone network."
    if code == 406 or "blacklist" in folded:
        return "Africa's Talking blocked this phone number."
    if code == 409 or "donotdisturb" in folded:
        return "The phone number is on do-not-disturb."
    if code == 401 or "riskhold" in folded:
        return "Africa's Talking held this SMS for a risk check."
    if text:
        return text[:180]
    if http_code and not 200 <= http_code < 300:
        return "Africa's Talking rejected the reminder (HTTP " + str(http_code) + ")."
    return "Africa's Talking did not accept the reminder."


def interpret_sms_response(http_code: int, body: str, number: str = "") -> dict:
    text = str(body or "").lstrip("\ufeff").strip()
    parsed = {}
    if text.startswith("{") or text.startswith("["):
        try:
            loaded = json.loads(text)
            parsed = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            parsed = {}
    if not parsed and "<statusCode>" in text:
        code_match = re.search(r"<statusCode>\s*(\d+)\s*</statusCode>", text)
        status_match = re.search(r"<status>\s*([^<]+)\s*</status>", text)
        message_match = re.search(r"<Message>\s*([^<]+)\s*</Message>", text)
        parsed = {
            "SMSMessageData": {
                "Message": message_match.group(1).strip() if message_match else "",
                "Recipients": [{
                    "statusCode": code_match.group(1) if code_match else 0,
                    "status": status_match.group(1).strip() if status_match else "",
                }],
            }
        }
    data = parsed.get("SMSMessageData") if isinstance(parsed.get("SMSMessageData"), dict) else {}
    recipients = data.get("Recipients") or []
    if isinstance(recipients, dict):
        recipients = [recipients]
    first = recipients[0] if recipients else {}
    try:
        code = int(first.get("statusCode") or 0)
    except (TypeError, ValueError):
        code = 0
    status = str(first.get("status") or "")
    message = str(data.get("Message") or parsed.get("message") or parsed.get("error") or "")
    if code in SUCCESS_CODES or status.lower() in SUCCESS_WORDS:
        return {"ok": True, "status": "sent", "code": code or http_code, "detail": status or "Sent"}
    if not recipients and text and not parsed:
        message = message or text[:180]
    detail = _reason(code, status, message, number, http_code if not recipients else 0)
    return {"ok": False, "status": "failed", "code": code or http_code, "detail": detail}


def _sender_rejected(result: dict) -> bool:
    code = int(result.get("code") or 0)
    detail = str(result.get("detail") or "").lower()
    return code == 402 or "sender id" in detail or "invalidsender" in re.sub(r"\s+", "", detail)


def _post(host: str, fields: dict, key: str) -> tuple:
    request = urllib.request.Request(
        "https://" + host + "/version1/messaging",
        data=urllib.parse.urlencode(fields).encode(),
        method="POST",
    )
    request.add_header("Accept", "application/json")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    request.add_header("apiKey", key)
    request.add_header("User-Agent", "wolaita-sodo-hospital/sms")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception:
        return 0, ""


def mask_phone(number: str) -> str:
    digits = re.sub(r"\D", "", str(number or ""))
    if len(digits) < 4:
        return "the patient number on the visit"
    return "the patient number ending " + digits[-4:]


def _tagged(result: dict, number: str) -> dict:
    result["number"] = number
    return result


def send_sms(phone, message: str) -> dict:
    key = _api_key()
    username = _env("AT_USERNAME", "AFRICASTALKING_USERNAME")
    number = normalize_phone(phone)
    if not key:
        return _tagged({"ok": False, "status": "not-configured", "detail": "AT_API_KEY is not set on this service"}, "")
    if not username:
        return _tagged({"ok": False, "status": "missing-username", "detail": "Add the Africa's Talking app username as AT_USERNAME"}, "")
    if not number:
        return _tagged({"ok": False, "status": "no-phone", "detail": "No usable phone number on the patient record"}, "")
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
    http_code, body = _post(host, fields, key)
    if http_code == 0 and not body:
        return _tagged({"ok": False, "status": "failed", "detail": "Africa's Talking could not be reached"}, number)
    result = interpret_sms_response(http_code, body, number)
    if result.get("ok") or "from" not in fields or not _sender_rejected(result):
        return _tagged(result, number)
    fields.pop("from", None)
    retry_code, retry_body = _post(host, fields, key)
    if retry_code == 0 and not retry_body:
        return _tagged({"ok": False, "status": "failed", "detail": "The sender ID was rejected, and Africa's Talking could not be reached for the retry."}, number)
    retried = interpret_sms_response(retry_code, retry_body, number)
    if retried.get("ok"):
        retried["detail"] = "Africa's Talking accepted it with the default sender after the saved sender ID was rejected. That is not proof the phone has received it."
        return _tagged(retried, number)
    retried["detail"] = "The saved sender ID was rejected. " + str(retried.get("detail") or "The retry without it also failed.")
    return _tagged(retried, number)

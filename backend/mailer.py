# =============================================================================
# Wolaita Sodo Hospital — mailer.py
# Sends the password-reset code by email.
#
# Render free web services block outbound SMTP on ports 25, 465, and 587.
# Brevo, SendGrid, and Resend send over HTTPS, so those work on the free plan.
# Set one provider in the Render dashboard. Never put the key in this repo.
#   BREVO_API_KEY + MAIL_FROM     (recommended)
#   SENDGRID_API_KEY + MAIL_FROM
#   RESEND_API_KEY + MAIL_FROM
# =============================================================================
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger("mediq.mail")

BLOCKED_SMTP = {25, 465, 587}


class MailError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _clean(name: str) -> str:
    return os.getenv(name, "").strip().strip('"').strip("'")


def _from_address() -> str:
    return _clean("MAIL_FROM") or _clean("SMTP_USER")


def _from_name() -> str:
    return _clean("MAIL_FROM_NAME") or "Wolaita Sodo Hospital"


def _smtp_port() -> int:
    try:
        return int(_clean("SMTP_PORT") or "0")
    except ValueError:
        return 0


def _smtp_usable() -> bool:
    if not (_clean("SMTP_HOST") and _clean("SMTP_USER") and _clean("SMTP_PASSWORD") and _from_address()):
        return False
    port = _smtp_port()
    if port in BLOCKED_SMTP and os.getenv("RENDER", "").strip().lower() == "true":
        return False
    return port > 0


def provider_name() -> str:
    forced = _clean("MAIL_PROVIDER").lower()
    available = []
    if _clean("BREVO_API_KEY") and _from_address():
        available.append("brevo")
    if _clean("SENDGRID_API_KEY") and _from_address():
        available.append("sendgrid")
    if _clean("RESEND_API_KEY") and _from_address():
        available.append("resend")
    if _smtp_usable():
        available.append("smtp")
    if forced and forced in available:
        return forced
    return available[0] if available else ""


def configured() -> bool:
    return bool(provider_name())


def _safe(text: str) -> str:
    text = (text or "").replace("\n", " ")
    for name in ("BREVO_API_KEY", "SENDGRID_API_KEY", "RESEND_API_KEY", "SMTP_PASSWORD"):
        secret = _clean(name)
        if secret and len(secret) > 4:
            text = text.replace(secret, "***")
    return text[:180]


def _esc(value: str) -> str:
    return (value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _messages(name: str, code: str) -> tuple[str, str, str]:
    who = (name or "").strip() or "there"
    subject = "Your Wolaita Sodo Hospital reset code"
    text = (
        f"Hello {who},\n\n"
        f"Your password reset code is {code}.\n"
        "It expires in 10 minutes. If you did not ask to reset your password, ignore this email.\n\n"
        f"የይለፍ ቃል ዳግም ማስጀመሪያ ኮድዎ፦ {code}\n"
        "ይህ ኮድ በ10 ደቂቃ ውስጥ ያበቃል።\n\n"
        "Wolaita Sodo Hospital\n"
    )
    html = (
        "<div style=\"font-family:Arial,sans-serif;color:#11212D;line-height:1.5\">"
        f"<p>Hello {_esc(who)},</p>"
        "<p>Your password reset code is</p>"
        f"<p style=\"font-size:32px;letter-spacing:6px;font-weight:700;margin:8px 0\">{_esc(code)}</p>"
        "<p>It expires in 10 minutes. If you did not ask to reset your password, ignore this email.</p>"
        f"<p>የይለፍ ቃል ዳግም ማስጀመሪያ ኮድዎ፦ <strong>{_esc(code)}</strong><br>ይህ ኮድ በ10 ደቂቃ ውስጥ ያበቃል።</p>"
        "<p>Wolaita Sodo Hospital</p>"
        "</div>"
    )
    return subject, text, html


def send_reset_code(to_email: str, name: str, code: str) -> str:
    """Send the code. Returns the provider name. Raises MailError on failure."""
    provider = provider_name()
    if not provider:
        raise MailError("not_configured")
    subject, text, html = _messages(name, code)
    sender = _from_address()
    if provider == "brevo":
        _post_json(
            "https://api.brevo.com/v3/smtp/email",
            {"api-key": _clean("BREVO_API_KEY"), "accept": "application/json"},
            {
                "sender": {"email": sender, "name": _from_name()},
                "to": [{"email": to_email, "name": (name or "").strip() or to_email}],
                "subject": subject,
                "textContent": text,
                "htmlContent": html,
            },
        )
    elif provider == "sendgrid":
        _post_json(
            "https://api.sendgrid.com/v3/mail/send",
            {"authorization": "Bearer " + _clean("SENDGRID_API_KEY")},
            {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": sender, "name": _from_name()},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": text},
                    {"type": "text/html", "value": html},
                ],
            },
        )
    elif provider == "resend":
        _post_json(
            "https://api.resend.com/emails",
            {"authorization": "Bearer " + _clean("RESEND_API_KEY")},
            {
                "from": f"{_from_name()} <{sender}>",
                "to": [to_email],
                "subject": subject,
                "text": text,
                "html": html,
            },
        )
    else:
        _send_smtp(to_email, subject, text)
    return provider


def _post_json(url: str, headers: dict, payload: dict) -> None:
    import httpx

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=15.0)
    except Exception as exc:  # noqa: BLE001
        log.error("email provider unreachable: %s", type(exc).__name__)
        raise MailError("send_failed") from exc
    if response.status_code < 200 or response.status_code >= 300:
        log.error("email provider rejected the message: %s %s", response.status_code, _safe(response.text))
        raise MailError("send_failed")


def _send_smtp(to_email: str, subject: str, text: str) -> None:
    port = _smtp_port()
    if port in BLOCKED_SMTP and os.getenv("RENDER", "").strip().lower() == "true":
        raise MailError("smtp_blocked")
    message = EmailMessage()
    message["From"] = f"{_from_name()} <{_from_address()}>"
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text)
    try:
        if port == 2465:
            with smtplib.SMTP_SSL(_clean("SMTP_HOST"), port, timeout=15, context=ssl.create_default_context()) as smtp:
                smtp.login(_clean("SMTP_USER"), _clean("SMTP_PASSWORD"))
                smtp.send_message(message)
            return
        with smtplib.SMTP(_clean("SMTP_HOST"), port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(_clean("SMTP_USER"), _clean("SMTP_PASSWORD"))
            smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001
        raise MailError("send_failed") from exc

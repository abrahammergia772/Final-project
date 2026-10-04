# Patient bill payment. The hospital records the wallet or bank the patient pays with.
# Card numbers, PINs, and wallet passwords are never collected.
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db import get_row, insert_row, update_row
from permissions import assert_resource
from security import current_user

router = APIRouter(tags=["Payments"])

WALLETS = (
    ("Telebirr", "Ethio Telecom"),
    ("CBE Birr", "Commercial Bank of Ethiopia"),
    ("M-Pesa", "Safaricom Ethiopia"),
    ("Amole", "Dashen Bank"),
    ("HelloCash", "Lion International Bank"),
    ("Awash Birr", "Awash Bank"),
    ("Coopay", "Cooperative Bank of Oromia"),
    ("E-Birr", "E-Birr wallet"),
    ("Kacha", "Kacha"),
    ("YenePay", "YenePay"),
    ("M-Birr", "M-Birr"),
    ("Other wallet", "Type the wallet name"),
)

BANKS = (
    ("Commercial Bank of Ethiopia", "CBE"),
    ("Awash Bank", "Awash"),
    ("Dashen Bank", "Dashen"),
    ("Bank of Abyssinia", "Abyssinia"),
    ("Wegagen Bank", "Wegagen"),
    ("Hibret Bank", "Hibret"),
    ("Nib International Bank", "NIB"),
    ("Cooperative Bank of Oromia", "Coop"),
    ("Lion International Bank", "Anbesa"),
    ("Zemen Bank", "Zemen"),
    ("Oromia Bank", "Oromia"),
    ("Berhan Bank", "Berhan"),
    ("Bunna Bank", "Bunna"),
    ("Abay Bank", "Abay"),
    ("Addis International Bank", "Addis"),
    ("Enat Bank", "Enat"),
    ("ZamZam Bank", "Interest-free"),
    ("Hijra Bank", "Interest-free"),
    ("Shabelle Bank", "Interest-free"),
    ("Siinqee Bank", "Siinqee"),
    ("Amhara Bank", "Amhara"),
    ("Ahadu Bank", "Ahadu"),
    ("Tsedey Bank", "Tsedey"),
    ("Gadaa Bank", "Gadaa"),
    ("Goh Betoch Bank", "Goh Betoch"),
    ("Global Bank Ethiopia", "Global"),
    ("Sidama Bank", "Sidama"),
    ("Omo Bank", "Omo"),
    ("CBE Noor", "CBE interest-free"),
    ("Other bank", "Type the bank name"),
)

_KNOWN = {name for name, _note in WALLETS + BANKS}
_OTHER = {"Other wallet", "Other bank"}
_STAFF = {"admin", "manager", "reception"}


class PayBody(BaseModel):
    method: str = ""
    channel: str = "wallet"
    amount: float = 0
    phone: str = ""
    account_name: str = ""
    account_number: str = ""
    other_name: str = ""
    note: str = Field(default="", max_length=160)


def payment_catalog() -> dict:
    return {
        "ok": True,
        "wallets": [{"name": name, "note": note} for name, note in WALLETS],
        "banks": [{"name": name, "note": note} for name, note in BANKS],
    }


def _flatten(row: dict | None) -> dict | None:
    if not row:
        return None
    row = dict(row)
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    for key, value in details.items():
        if key not in row or row.get(key) in (None, "", []):
            row[key] = value
    row["details"] = details
    return row


def _owns(row: dict, user) -> bool:
    email = str(user.get("email") or "").strip().lower()
    name = str(user.get("name") or "").strip().lower()
    details = row.get("details") if isinstance(row.get("details"), dict) else {}
    values = {
        str(row.get(key) or details.get(key) or "").strip().lower()
        for key in ("email", "patient", "reporter", "name", "from", "uploaded_by")
    }
    if email and email in values:
        return True
    if name and name in values:
        return True
    patient = str(row.get("patient") or details.get("patient") or "").strip().lower()
    return bool(patient and ((name and name in patient) or (email and email in patient)))


def _money(value) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("251") and len(digits) >= 12:
        digits = "0" + digits[3:12]
    elif len(digits) == 9 and digits[0] in "79":
        digits = "0" + digits
    return digits if re.fullmatch(r"0[79]\d{8}", digits) else ""


def _account_number(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    return digits if re.fullmatch(r"\d{8,20}", digits) else ""


def _clean_name(value: str) -> str:
    text = re.sub(r"[\x00-\x1f<>]", "", value or "")
    return re.sub(r"\s+", " ", text).strip()[:60]


def _method(body: PayBody) -> tuple[str, str]:
    chosen = str(body.method or "").strip()
    if any(chosen == name for name, _note in WALLETS):
        channel = "wallet"
    elif any(chosen == name for name, _note in BANKS):
        channel = "bank"
    else:
        raise HTTPException(status_code=400, detail="Choose a wallet or bank")
    if chosen in _OTHER:
        custom = _clean_name(body.other_name)
        if len(custom) < 2:
            raise HTTPException(status_code=400, detail="Type the bank or wallet name")
        return custom, channel
    return chosen, channel


def _save(endpoint: str, row_id: str, payload: dict, exists: bool) -> None:
    result = update_row(endpoint, row_id, payload) if exists else insert_row(endpoint, {**payload, "id": row_id})
    if result.get("ok") is False and not exists:
        result = update_row(endpoint, row_id, payload)
    if result.get("ok") is False:
        raise HTTPException(status_code=503, detail=result.get("error") or "Could not record the payment")


@router.get("/bills/payment-methods")
def list_payment_methods(user=Depends(current_user)):
    assert_resource(user, "bills")
    return payment_catalog()


@router.post("/bills/{bill_id}/pay")
def pay_bill(bill_id: str, body: PayBody, user=Depends(current_user)):
    assert_resource(user, "bills")
    bill_id = str(bill_id or "").strip()
    if not bill_id or len(bill_id) > 80:
        raise HTTPException(status_code=400, detail="Bill not found")
    bill = _flatten(get_row("bills", bill_id))
    invoice = _flatten(get_row("cashier_invoices", bill_id))
    if not bill and not invoice:
        raise HTTPException(status_code=404, detail="Bill not found")
    role = str(user.get("role") or "")
    if role not in _STAFF and not ((bill and _owns(bill, user)) or (invoice and _owns(invoice, user))):
        raise HTTPException(status_code=403, detail="You can only pay your own bill")

    source = bill or invoice or {}
    amount = _money(source.get("amount") or (invoice or {}).get("amount") or (bill or {}).get("amount"))
    already = max(_money((bill or {}).get("paid")), _money((invoice or {}).get("paid")))
    due = round(max(0.0, amount - already), 2)
    if due <= 0:
        raise HTTPException(status_code=400, detail="This bill is already paid")
    paying = _money(body.amount)
    if paying <= 0 or paying > due + 0.001:
        raise HTTPException(status_code=400, detail="Enter an amount up to the balance")
    method, channel = _method(body)
    phone = _phone(body.phone) if channel == "wallet" else ""
    account = _clean_name(body.account_name)
    account_number = _account_number(body.account_number) if channel == "bank" else ""
    if channel == "wallet" and not phone:
        raise HTTPException(status_code=400, detail="Enter the wallet phone number, like 09xxxxxxxx")
    if channel == "bank" and not account_number:
        raise HTTPException(status_code=400, detail="Enter the bank account number")

    paid = round(already + paying, 2)
    status = "paid" if paid + 0.001 >= amount and amount else "pending"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt = "WSH" + datetime.now(timezone.utc).strftime("%m%d%H%M%S")
    payment = {
        "receipt": receipt,
        "at": stamp,
        "method": method,
        "channel": channel,
        "amount": paying,
        "phone": phone,
        "account_name": account,
        "account_number": account_number,
        "by": str(user.get("email") or user.get("name") or ""),
        "note": _clean_name(body.note)[:160],
    }
    def _history(row):
        if not row or not isinstance(row.get("details"), dict):
            return []
        items = row["details"].get("payments") or []
        return items if isinstance(items, list) else []

    old_details = {}
    if bill and isinstance(bill.get("details"), dict):
        old_details.update(bill["details"])
    if invoice and isinstance(invoice.get("details"), dict):
        for key, value in invoice["details"].items():
            if key not in old_details or old_details.get(key) in (None, "", []):
                old_details[key] = value
    history = _history(bill)
    seen = {str(item.get("receipt") or "") for item in history if isinstance(item, dict)}
    for item in _history(invoice):
        if isinstance(item, dict) and str(item.get("receipt") or "") not in seen:
            history.append(item)
    history.append(payment)
    details = {
        "payments": history[-20:],
        "last_payment": payment,
        "email": old_details.get("email") or user.get("email") or "",
        "patient_id": old_details.get("patient_id") or source.get("patient_id") or "",
    }
    patient = source.get("patient") or user.get("name") or ""
    service = source.get("service") or source.get("description") or "Invoice"
    common = {
        "amount": amount,
        "paid": paid,
        "status": status,
        "method": method,
        "patient": patient,
        "service": service,
        "details": details,
    }
    if bill:
        _save("bills", bill_id, common, True)
    else:
        _save("bills", bill_id, {
            **common,
            "date": str(source.get("date") or stamp[:10]),
            "description": service,
        }, False)
    if invoice:
        _save("cashier_invoices", bill_id, {
            "patient": patient,
            "service": service,
            "amount": amount,
            "paid": paid,
            "method": method,
            "status": status,
            "details": details,
        }, True)
    else:
        _save("cashier_invoices", bill_id, {
            "patient": patient,
            "service": service,
            "amount": amount,
            "paid": paid,
            "method": method,
            "status": status,
            "details": details,
        }, False)
    return {
        "ok": True,
        "id": bill_id,
        "receipt": receipt,
        "method": method,
        "channel": channel,
        "amount": paying,
        "paid": paid,
        "balance": round(max(0.0, amount - paid), 2),
        "status": status,
        "patient": patient,
        "phone": phone,
        "account_name": account,
        "account_number": account_number,
    }

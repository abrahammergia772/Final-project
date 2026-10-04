# =============================================================================
# Wolaita Sodo Hospital — routers/reports.py
# POST /reports/generate
# Writes a narrative from hospital totals and the rows the page already loaded,
# then saves that narrative in Supabase. Not mounted behind the AI permission:
# nurse and reception have report pages without the AI permission.
# =============================================================================
import logging
import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db import insert_row, list_rows
from groq_client import write_report
from permissions import DENIED, granted
from security import current_user

router = APIRouter(tags=["Reports"])
log = logging.getLogger("mediq.reports")

_TOTALS = (
    ("patients", "patients"),
    ("appointments", "appointments"),
    ("prescriptions", "prescriptions"),
    ("lab_results", "lab results"),
    ("inventory", "inventory items"),
    ("beds", "beds"),
    ("complaints", "complaints"),
    ("bills", "bills"),
)


class ReportRow(BaseModel):
    item: str = ""
    detail: str = ""
    status: str = ""
    date: str = ""


class ReportRequest(BaseModel):
    title: str = "Hospital report"
    period: str = ""
    rows: list[ReportRow] = Field(default_factory=list)


def _clip(value, limit: int = 80) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split())
    if "@" in text:
        return "[email]"
    return text[:limit]


def _status_counts(items: list) -> str:
    counts = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        status = _clip(item.get("status") or "unspecified", 24) or "unspecified"
        counts[status] = counts.get(status, 0) + 1
    if not counts:
        return "no status breakdown"
    parts = [status + " " + str(count) for status, count in list(counts.items())[:6]]
    return ", ".join(parts)


def _hospital_facts() -> list:
    lines = []
    for endpoint, label in _TOTALS:
        result = list_rows(endpoint, limit=200)
        items = result.get("items") or []
        if not result.get("ok") and not items:
            continue
        lines.append(label + ": " + str(len(items)) + " records (" + _status_counts(items) + ")")
    return lines


def _row_facts(rows: list) -> list:
    lines = []
    for row in rows[:40]:
        item = _clip(row.item)
        detail = _clip(row.detail)
        status = _clip(row.status, 30)
        when = _clip(row.date, 20)
        bits = [part for part in (item, detail, status, when) if part and part != "[email]"]
        if bits:
            lines.append("row: " + " | ".join(bits))
    return lines


@router.post("/reports/generate")
def generate_report(req: ReportRequest, user=Depends(current_user)):
    role = str(user.get("role") or "")
    if not (granted(role, "reports") or granted(role, "ai")):
        raise HTTPException(status_code=403, detail=DENIED)
    title = _clip(req.title or "Hospital report", 120) or "Hospital report"
    period = _clip(req.period or "the selected period", 80)
    facts = ["Report title: " + title, "Period: " + period, "Requested by role: " + (role or "staff")]
    if granted(role, "reports"):
        facts.extend(_hospital_facts())
    submitted = _row_facts(req.rows or [])
    facts.append("Rows sent by the page: " + str(len(submitted)))
    facts.extend(submitted[:40])
    if len(facts) <= 4:
        facts.append("No hospital totals or page rows were available.")
    narrative, source = write_report(title, period, "\n".join(facts))
    if not narrative:
        narrative = (
            title + " for " + period + ". "
            "The written narrative service was unavailable, so this report keeps the counted records only. "
            + " ".join(facts[3:8])
            + " These figures come from the hospital records already loaded. A clinician or manager should review the source table before acting."
        )
        source = "local"
    doc_id = "RP-" + secrets.token_hex(4).upper()
    saved = insert_row("documents", {
        "id": doc_id,
        "patient": "",
        "type": "Hospital Report",
        "title": title,
        "date": date.today().isoformat(),
        "size": str(len(narrative)) + " chars",
        "uploaded_by": user.get("name") or user.get("email") or role,
        "summary": narrative[:240],
        "narrative": narrative,
        "period": period,
        "format": "Narrative",
        "explained_by": source,
    })
    document_id = ""
    stored = False
    error = ""
    if saved.get("ok"):
        stored = True
        document_id = (saved.get("row") or {}).get("id") or doc_id
    else:
        error = saved.get("error") or "Could not save the report"
        log.warning("report save failed")
    return {
        "ok": stored,
        "saved": stored,
        "document_id": document_id,
        "title": title,
        "period": period,
        "narrative": narrative,
        "source": source,
        "error": error,
    }

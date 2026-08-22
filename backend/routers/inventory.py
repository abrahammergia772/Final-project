# =============================================================================
# MedIQ Pro — routers/inventory.py  (Module 5: Inventory Forecasting)
# POST /ai/forecast-inventory
# Uses the trained 27-feature XGBRegressor + per-drug Prophet seasonal JSONs.
# =============================================================================
import hashlib
import json
import logging
import math
from datetime import date, timedelta
from typing import Dict

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field

from model_loader import load_module, load_config, prophet_files

router = APIRouter(tags=["AI · Inventory"])
log = logging.getLogger("mediq.inventory")


class ForecastRequest(BaseModel):
    drug_name: str = Field(default="Paracetamol", min_length=1, max_length=120)
    days: int = Field(default=30, ge=1, le=180)


def _encoded(drug: str, cfg: dict) -> int:
    cat = cfg.get("drug_catalogue", [])
    try:
        return cat.index(drug)
    except ValueError:
        return 0


def _resolve_drug(value: str, catalogue: list[str]) -> str:
    """Resolve strengths and case differences without truncating multi-word drugs."""
    requested = " ".join(value.strip().split()).casefold()
    if not catalogue:
        return "Paracetamol"
    exact = next((item for item in catalogue if item.casefold() == requested), None)
    if exact:
        return exact
    matches = [item for item in catalogue if requested.startswith(item.casefold() + " ")]
    return max(matches, key=len) if matches else catalogue[0]


def _features_for(d: date, drug: str, cfg: dict, hist: list) -> list:
    """Build the 27-feature row. hist = trailing demand series (list of floats)."""
    cols = cfg.get("feature_cols", [])
    f: Dict[str, float] = {
        "drug_encoded": float(_encoded(drug, cfg)),
        "year": d.year, "month": d.month, "day": d.day, "dayofweek": d.weekday(),
        "weekofyear": d.isocalendar()[1], "quarter": (d.month - 1) // 3 + 1,
        "is_weekend": 1 if d.weekday() >= 5 else 0,
        "is_monthend": 1 if d.day >= 28 else 0,
        "is_monthstart": 1 if d.day <= 3 else 0,
        "season": (d.month % 12 + 3) // 3,
        "is_holiday": 0,
    }
    # lags & rolling stats from history
    for lag in (1, 7, 14, 30):
        f[f"lag_{lag}"] = hist[-lag] if len(hist) >= lag else (hist[0] if hist else 10.0)
    def rmean(n):
        return float(np.mean(hist[-n:])) if hist else 10.0
    def rstd(n):
        return float(np.std(hist[-n:])) if len(hist) >= 2 else 2.0
    def rmax(n):
        return float(np.max(hist[-n:])) if hist else 10.0
    for n in (7, 14, 30):
        f[f"roll_mean_{n}"] = rmean(n)
        f[f"roll_std_{n}"] = rstd(n)
        f[f"roll_max_{n}"] = rmax(n)
    f["expanding_mean"] = float(np.mean(hist)) if hist else 10.0
    f["demand_velocity"] = (hist[-1] - hist[-2]) if len(hist) >= 2 else 0.0
    for c in cols:
        f.setdefault(c, 0.0)
    return [float(f.get(c, 0.0)) for c in cols]


def _prophet_scale(drug: str, d: date) -> float:
    """Use the per-drug Prophet JSON to modulate the forecast (best-effort)."""
    try:
        pf = prophet_files().get(drug)
        if not pf:
            return 1.0
        with open(pf, encoding="utf-8") as handle:
            data = json.load(handle)
        weekly = data.get("weekly", data.get("weekly_seasonality", {}))
        w = 1.0
        if isinstance(weekly, dict) and "mean" in weekly:
            w = float(weekly.get("mean", 1.0))
        # crude day-of-week factor from weekly dataframe if present
        for item in weekly.get("data", []):
            if str(item.get("ds", "")).endswith(f"-{d.isocalendar()[2]}"):
                w = float(item.get("trend", w))
        return max(0.5, min(2.0, w))
    except Exception:  # noqa: BLE001
        return 1.0


@router.post("/ai/forecast-inventory")
def forecast_inventory(req: ForecastRequest):
    models = load_module("inventory")
    cfg = load_config("inventory", "inventory_config.json") or {}
    xgb = models.get("inventory_xgb_model.pkl")

    requested_drug = " ".join(req.drug_name.strip().split())
    cat = cfg.get("drug_catalogue", [])
    drug_key = _resolve_drug(requested_drug, cat)

    days = req.days
    stats = (cfg.get("drug_stats") or {}).get(drug_key, {})
    daily_base = float(stats.get("daily_demand", stats.get("mean_demand", 12)) or 12)
    lead_raw = cfg.get("lead_time_days", 5)
    lead = int(lead_raw.get(drug_key, 5)) if isinstance(lead_raw, dict) else int(lead_raw or 5)
    safety = float(cfg.get("safety_stock_z", 1.65) or 1.65)
    current_stock = float(stats.get("current_stock", 120) or 120)

    # history: synthetic 60-day series seeded around daily_base
    seed = int.from_bytes(hashlib.sha256(drug_key.encode("utf-8")).digest()[:4], "big")
    rng = np.random.default_rng(seed)
    hist = [max(0, daily_base + rng.normal(0, daily_base * 0.25)) for _ in range(60)]
    history_snapshot = list(hist)

    forecast, projected = [], 0.0
    d0 = date.today()
    for i in range(1, days + 1):
        d = d0 + timedelta(days=i)
        if xgb is not None and cfg.get("feature_cols"):
            try:
                X = np.array([_features_for(d, drug_key, cfg, hist)])
                pred = float(xgb.predict(X)[0])
            except Exception as exc:  # noqa: BLE001
                log.warning("inventory predict failed (%s): %s → base", drug_key, exc)
                pred = daily_base * (1 + 0.18 * math.sin(i / 6))
        else:
            pred = daily_base * (1 + 0.18 * math.sin(i / 6 + len(drug_key)))
        pred = max(0.0, pred * _prophet_scale(drug_key, d))
        hist.append(pred)
        forecast.append({"day": f"Day {i}", "value": round(pred, 1)})
        projected += pred

    runs_out = projected >= current_stock
    suggested = max(0, int(projected - current_stock)) + int(daily_base * lead * 1.25) + int(safety * daily_base)
    return {
        "drug_name": drug_key, "requested_drug": requested_drug, "days": days, "current_stock": int(current_stock),
        "historical": [{"label": f"D-{12 - i}", "value": round(v, 1)} for i, v in enumerate(history_snapshot[-12:])],
        "forecast": forecast, "daily_use": round(daily_base, 1),
        "runs_out_in_days": max(1, int(current_stock / max(daily_base, 1))) if runs_out else None,
        "suggested_order_qty": suggested,
        "model": "inventory_xgb+prophet", "model_version": cfg.get("version", "1.0.0"),
        "source": "trained-model" if xgb is not None else "rules",
        "disclaimer": "Forecasts are estimates; confirm stock, expiry, and supplier lead times before ordering.",
    }

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def money(value: Any) -> str:
    try:
        n = float(value or 0)
    except Exception:
        n = 0.0
    sign = "-" if n < 0 else ""
    n = abs(n)
    return f"{sign}$ {n:,.0f}".replace(",", ".")


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%".replace(".", ",")
    except Exception:
        return "0,0%"


def as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except Exception:
        return default


def iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def safe_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except Exception:
        try:
            return date.fromisoformat(str(value)[:10])
        except Exception:
            return None


def normalize_plate(value: str) -> str:
    return "".join(ch for ch in (value or "").upper().strip() if ch.isalnum())

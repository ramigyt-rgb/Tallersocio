from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Iterable
import pandas as pd

from utils import as_float, safe_date


PRODUCTION_STAGES = [
    "Esperando", "Desarme", "Chapa", "Preparación", "Pintura",
    "Armado", "Control de calidad", "Listo para entregar", "Entregado"
]


def business_days(start: date, end: date) -> int:
    if end < start:
        return 0
    d = start
    total = 0
    while d <= end:
        if d.weekday() < 5:
            total += 1
        d += timedelta(days=1)
    return total


def month_bounds(today: date) -> tuple[date, date]:
    last = monthrange(today.year, today.month)[1]
    return date(today.year, today.month, 1), date(today.year, today.month, last)


def _sum(rows: Iterable[dict], field: str, predicate=lambda r: True) -> float:
    return sum(as_float(r.get(field)) for r in rows if predicate(r))


def workshop_snapshot(repo, today: date, settings: dict) -> dict:
    leads = repo.list_rows("leads")
    quotes = repo.list_rows("quotes")
    ots = repo.list_rows("work_orders")
    moves = repo.list_rows("financial_movements")
    insurance = repo.list_rows("insurance_jobs")
    purchases = repo.list_rows("material_movements")

    m0, m1 = month_bounds(today)

    def in_month(row, fields=("movement_date", "date", "created_at", "delivery_date")):
        for f in fields:
            d = safe_date(row.get(f))
            if d:
                return m0 <= d <= m1
        return False

    active = [o for o in ots if o.get("stage") not in {"Entregado", "Cancelado"} and not o.get("archived")]
    deliveries_today = [o for o in ots if safe_date(o.get("promised_date")) == today and o.get("stage") != "Entregado"]
    scheduled_today = [o for o in ots if safe_date(o.get("appointment_date")) == today and o.get("stage") in {"Esperando", "Ingreso"}]
    pending_quotes = [q for q in quotes if q.get("status") in {"Borrador", "Enviada", "Seguimiento"}]

    inflow = _sum(moves, "amount", lambda r: r.get("direction") == "Ingreso" and in_month(r))
    outflow = _sum(moves, "amount", lambda r: r.get("direction") == "Egreso" and in_month(r))
    available_cash = _sum(moves, "amount", lambda r: r.get("direction") == "Ingreso" and r.get("status") == "Pagado") - _sum(moves, "amount", lambda r: r.get("direction") == "Egreso" and r.get("status") == "Pagado")
    receivable = _sum(moves, "amount", lambda r: r.get("direction") == "Ingreso" and r.get("status") == "Pendiente")
    payable = _sum(moves, "amount", lambda r: r.get("direction") == "Egreso" and r.get("status") == "Pendiente")
    paint_payable = _sum(moves, "amount", lambda r: r.get("direction") == "Egreso" and r.get("status") == "Pendiente" and str(r.get("category", "")).lower() in {"pinturería", "pintureria", "materiales"})

    completed_month = [o for o in ots if safe_date(o.get("delivery_date")) and m0 <= safe_date(o.get("delivery_date")) <= m1]
    if not completed_month:
        # mientras el taller empieza, usa OTs activas creadas en el mes como estimación operativa.
        completed_month = [o for o in ots if in_month(o, ("created_at",)) and not o.get("archived")]

    revenue = _sum(completed_month, "agreed_amount")
    direct_cost = sum(
        as_float(o.get("actual_material_cost")) + as_float(o.get("parts_cost")) + as_float(o.get("outsourcing_cost"))
        for o in completed_month
    )
    contribution = revenue - direct_cost

    monthly_fixed = as_float(settings.get("monthly_fixed_costs", 0))
    elapsed_bdays = max(1, business_days(m0, min(today, m1)))
    total_bdays = max(1, business_days(m0, m1))
    fixed_accrued = monthly_fixed * (elapsed_bdays / total_bdays)
    operating = contribution - fixed_accrued
    reserve_rate = as_float(settings.get("reserve_rate", 0.0))
    distributable = max(0.0, operating * (1 - reserve_rate))

    target = as_float(settings.get("distributable_target", 6_666_667))
    target_acc = target * (elapsed_bdays / total_bdays)
    deviation = distributable - target_acc
    remaining_bdays = business_days(today + timedelta(days=1), m1)
    needed_daily = max(0, target - distributable) / max(1, remaining_bdays)
    projection = distributable / elapsed_bdays * total_bdays if elapsed_bdays else 0

    insured_exposure = sum(as_float(x.get("capital_financed")) for x in insurance if x.get("collection_status") != "Cobrado")
    insurance_limit = as_float(settings.get("insurance_capital_limit", 3_000_000))

    late_ots = [o for o in active if safe_date(o.get("promised_date")) and safe_date(o.get("promised_date")) < today]
    next_week_end = today + timedelta(days=7)
    next_week_jobs = [o for o in active if safe_date(o.get("promised_date")) and today <= safe_date(o.get("promised_date")) <= next_week_end]
    capacity_slots = max(1, int(as_float(settings.get("weekly_capacity_cars", 8), 8)))
    capacity = min(1.5, len(next_week_jobs) / capacity_slots)

    return {
        "active_cars": len(active),
        "deliveries_today": len(deliveries_today),
        "scheduled_today": len(scheduled_today),
        "pending_quotes": len(pending_quotes),
        "late_ots": len(late_ots),
        "cash": available_cash,
        "receivable": receivable,
        "payable": payable,
        "paint_payable": paint_payable,
        "monthly_inflow": inflow,
        "monthly_outflow": outflow,
        "revenue": revenue,
        "direct_cost": direct_cost,
        "contribution": contribution,
        "fixed_accrued": fixed_accrued,
        "operating": operating,
        "distributable": distributable,
        "target": target,
        "target_acc": target_acc,
        "deviation": deviation,
        "remaining_bdays": remaining_bdays,
        "needed_daily": needed_daily,
        "projection": projection,
        "tech_share": distributable * as_float(settings.get("technical_share", .60), .60),
        "owner_share": distributable * as_float(settings.get("owner_share", .40), .40),
        "insurance_exposure": insured_exposure,
        "insurance_limit": insurance_limit,
        "insurance_usage": insured_exposure / insurance_limit if insurance_limit else 0,
        "capacity": capacity,
        "active_orders": active,
        "late_orders": late_ots,
    }


def quote_totals(items: pd.DataFrame, settings: dict) -> dict:
    if items is None or items.empty:
        return {"labor_hours": 0, "estimated_cost": 0, "floor": 0, "target": 0, "days": 0}

    df = items.copy()
    numeric = ["horas_chapa", "horas_preparacion", "horas_armado", "panos", "materiales", "repuestos", "tercerizaciones"]
    for c in numeric:
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    labor_cost_h = as_float(settings.get("labor_cost_per_hour", 18000))
    paint_cost_panel = as_float(settings.get("paint_cost_per_panel", 55000))
    difficulty_map = {"Baja": 1.0, "Media": 1.10, "Alta": 1.25, "Muy alta": 1.45}
    if "dificultad" not in df.columns:
        df["dificultad"] = "Media"

    labor_hours = float((df["horas_chapa"] + df["horas_preparacion"] + df["horas_armado"]).sum())
    labor_cost = 0.0
    paint_cost = 0.0
    extras = 0.0
    for _, r in df.iterrows():
        mult = difficulty_map.get(str(r.get("dificultad", "Media")), 1.10)
        row_hours = as_float(r["horas_chapa"]) + as_float(r["horas_preparacion"]) + as_float(r["horas_armado"])
        labor_cost += row_hours * labor_cost_h * mult
        paint_cost += as_float(r["panos"]) * paint_cost_panel * mult
        extras += as_float(r["materiales"]) + as_float(r["repuestos"]) + as_float(r["tercerizaciones"])

    estimated_cost = labor_cost + paint_cost + extras
    floor_margin = as_float(settings.get("floor_margin", .25))
    target_margin = as_float(settings.get("target_margin", .40))
    floor = estimated_cost / max(.05, 1 - floor_margin)
    target = estimated_cost / max(.05, 1 - target_margin)
    hours_per_day = as_float(settings.get("productive_hours_per_day", 7), 7)
    days = max(1, round(labor_hours / max(1, hours_per_day) + float(df["panos"].sum()) * .35))
    return {"labor_hours": labor_hours, "estimated_cost": estimated_cost, "floor": floor, "target": target, "days": days}

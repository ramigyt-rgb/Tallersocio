from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from core import (
    PRODUCTION_STAGES, as_float, business_days_elapsed, business_days_in_month, business_days_remaining,
    clamp, in_month, month_range, parse_date, safe_div
)


def quote_item_cost(item: dict, settings: dict) -> dict:
    chapa_h = as_float(item.get("chapa_hours"))
    prep_h = as_float(item.get("prep_hours"))
    paint_h = as_float(item.get("paint_hours"))
    assembly_h = as_float(item.get("assembly_hours"))
    panels = as_float(item.get("panels"))
    difficulty = item.get("difficulty", "Media")
    diff_factor = {"Baja": 0.92, "Media": 1.0, "Alta": 1.18, "Especial": 1.35}.get(difficulty, 1.0)

    labor = chapa_h * as_float(settings.get("labor_hour_cost"))
    prep = prep_h * as_float(settings.get("prep_hour_cost"))
    paint_labor = paint_h * as_float(settings.get("paint_hour_cost"))
    assembly = assembly_h * as_float(settings.get("assembly_hour_cost"))
    panel_paint = panels * as_float(settings.get("paint_panel_cost"))
    materials = as_float(item.get("materials_estimated"))
    parts = as_float(item.get("parts_estimated"))
    outsource = as_float(item.get("outsourcing_estimated"))
    base = labor + prep + paint_labor + assembly + panel_paint + materials + parts + outsource
    total = base * diff_factor
    return {
        "labor_cost": labor,
        "prep_cost": prep,
        "paint_labor_cost": paint_labor,
        "assembly_cost": assembly,
        "panel_paint_cost": panel_paint,
        "materials_cost": materials,
        "parts_cost": parts,
        "outsourcing_cost": outsource,
        "difficulty_factor": diff_factor,
        "cost": total,
        "hours": chapa_h + prep_h + paint_h + assembly_h,
    }


def quote_totals(items: list[dict], settings: dict, manual_costs: float = 0.0) -> dict:
    detail = [quote_item_cost(x, settings) for x in items]
    cost = sum(x["cost"] for x in detail) + as_float(manual_costs)
    floor_margin = clamp(as_float(settings.get("floor_margin_pct")), 0, 0.95)
    target_margin = clamp(as_float(settings.get("target_margin_pct")), 0, 0.95)
    price_floor = cost / (1 - floor_margin) if cost else 0.0
    price_target = cost / (1 - target_margin) if cost else 0.0
    hours = sum(x["hours"] for x in detail)
    return {
        "estimated_cost": cost,
        "price_floor": price_floor,
        "price_target": price_target,
        "estimated_hours": hours,
        "items_detail": detail,
    }


def actual_material_cost(work_order_id: str, material_moves: list[dict]) -> float:
    return sum(
        as_float(x.get("qty")) * as_float(x.get("unit_cost"))
        for x in material_moves
        if x.get("work_order_id") == work_order_id and x.get("move_type") == "Consumo"
    )


def work_order_cost(ot: dict, material_moves: list[dict]) -> float:
    return (
        actual_material_cost(str(ot.get("id")), material_moves)
        + as_float(ot.get("parts_actual"))
        + as_float(ot.get("outsourcing_actual"))
        + as_float(ot.get("other_direct_actual"))
        + as_float(ot.get("labor_actual_cost"))
    )


def work_order_margin(ot: dict, material_moves: list[dict]) -> dict:
    revenue = as_float(ot.get("agreed_amount"))
    direct = work_order_cost(ot, material_moves)
    margin = revenue - direct
    return {"revenue": revenue, "direct_cost": direct, "margin": margin, "margin_pct": safe_div(margin, revenue)}


def current_stock(material_id: str, moves: list[dict]) -> float:
    qty = 0.0
    for x in moves:
        if x.get("material_id") != material_id:
            continue
        t = x.get("move_type")
        q = as_float(x.get("qty"))
        if t in ("Compra", "Ajuste +"):
            qty += q
        elif t in ("Consumo", "Ajuste -"):
            qty -= q
    return qty


def finance_summary(moves: list[dict], target_date: date | None = None) -> dict:
    target_date = target_date or date.today()
    paid = [x for x in moves if x.get("status") == "Pagado" and not x.get("voided")]
    pending = [x for x in moves if x.get("status") == "Pendiente" and not x.get("voided")]
    cash = defaultdict(float)
    for x in paid:
        sign = 1 if x.get("direction") == "Ingreso" else -1
        cash[x.get("account") or "Otro"] += sign * as_float(x.get("amount"))
    receivable = sum(as_float(x.get("amount")) for x in pending if x.get("direction") == "Ingreso")
    payable = sum(as_float(x.get("amount")) for x in pending if x.get("direction") == "Egreso")
    month_in = sum(as_float(x.get("amount")) for x in paid if x.get("direction") == "Ingreso" and in_month(x.get("movement_date"), target_date))
    month_out = sum(as_float(x.get("amount")) for x in paid if x.get("direction") == "Egreso" and in_month(x.get("movement_date"), target_date))
    overdue_ar = sum(as_float(x.get("amount")) for x in pending if x.get("direction") == "Ingreso" and parse_date(x.get("due_date")) and parse_date(x.get("due_date")) < target_date)
    overdue_ap = sum(as_float(x.get("amount")) for x in pending if x.get("direction") == "Egreso" and parse_date(x.get("due_date")) and parse_date(x.get("due_date")) < target_date)
    return {
        "cash_by_account": dict(cash), "cash_total": sum(cash.values()), "receivable": receivable, "payable": payable,
        "month_in": month_in, "month_out": month_out, "month_net": month_in - month_out,
        "overdue_receivable": overdue_ar, "overdue_payable": overdue_ap,
    }


def month_profit(work_orders: list[dict], material_moves: list[dict], settings: dict, target_date: date | None = None) -> dict:
    target_date = target_date or date.today()
    recognized = [x for x in work_orders if in_month(x.get("delivery_date"), target_date) and x.get("stage") == "Entregado" and not x.get("cancelled")]
    revenue = 0.0
    directs = 0.0
    for ot in recognized:
        m = work_order_margin(ot, material_moves)
        revenue += m["revenue"]
        directs += m["direct_cost"]
    contribution = revenue - directs
    business_days = business_days_in_month(target_date)
    elapsed = business_days_elapsed(target_date)
    fixed_full = as_float(settings.get("monthly_fixed_structure"))
    fixed_mtd = fixed_full * safe_div(elapsed, len(business_days))
    operating = contribution - fixed_mtd
    reserve = max(0.0, operating) * as_float(settings.get("reserve_pct"))
    distributable = operating - reserve
    return {
        "revenue": revenue, "directs": directs, "contribution": contribution, "fixed_mtd": fixed_mtd,
        "operating": operating, "reserve": reserve, "distributable": distributable,
        "technical_share": max(0.0, distributable) * as_float(settings.get("technical_share")),
        "business_share": max(0.0, distributable) * as_float(settings.get("business_share")),
        "recognized_count": len(recognized),
    }


def objective_status(work_orders: list[dict], material_moves: list[dict], settings: dict, target_date: date | None = None) -> dict:
    target_date = target_date or date.today()
    prof = month_profit(work_orders, material_moves, settings, target_date)
    target = as_float(settings.get("monthly_distributable_target"))
    days = business_days_in_month(target_date)
    elapsed = business_days_elapsed(target_date)
    remaining = business_days_remaining(target_date)
    accumulated_target = target * safe_div(elapsed, len(days))
    gap = prof["distributable"] - accumulated_target
    remaining_target = max(0.0, target - prof["distributable"])
    required_daily = safe_div(remaining_target, remaining)
    pace = safe_div(prof["distributable"], elapsed) if elapsed else 0.0
    projected = pace * len(days)
    return {
        **prof, "target": target, "accumulated_target": accumulated_target, "gap": gap,
        "remaining_days": remaining, "required_daily": required_daily, "projected": projected,
        "progress": safe_div(prof["distributable"], target),
    }


def pipeline_metrics(leads: list[dict], quotes: list[dict]) -> dict:
    lead_counts = Counter(x.get("status", "Nuevo") for x in leads)
    quoted = sum(1 for x in leads if x.get("status") in ("Cotizado", "Seguimiento", "Ganado", "Perdido"))
    won = sum(1 for x in leads if x.get("status") == "Ganado")
    lost = sum(1 for x in leads if x.get("status") == "Perdido")
    quote_values = sum(as_float(x.get("offered_price")) for x in quotes if x.get("status") in ("Enviado", "Seguimiento", "Aprobada"))
    return {
        "counts": dict(lead_counts), "total": len(leads), "quoted": quoted, "won": won, "lost": lost,
        "win_rate": safe_div(won, won + lost), "quote_pipeline_value": quote_values,
    }


def production_metrics(work_orders: list[dict], settings: dict, target_date: date | None = None) -> dict:
    target_date = target_date or date.today()
    active = [x for x in work_orders if x.get("stage") not in ("Entregado", "Cancelado") and not x.get("cancelled")]
    late = []
    due_today = []
    stage_counts = Counter()
    hours_open = 0.0
    for ot in active:
        stage = ot.get("stage", "Esperando")
        stage_counts[stage] += 1
        promised = parse_date(ot.get("promised_date"))
        if promised and promised < target_date:
            late.append(ot)
        if promised == target_date:
            due_today.append(ot)
        hours_open += as_float(ot.get("estimated_hours"))
    weekly_capacity = as_float(settings.get("weekly_capacity_hours"))
    capacity_pct = safe_div(hours_open, weekly_capacity) if weekly_capacity else 0.0
    return {"active": active, "late": late, "due_today": due_today, "stage_counts": dict(stage_counts), "open_hours": hours_open, "capacity_pct": capacity_pct}


def insurance_summary(jobs: list[dict], settings: dict, target_date: date | None = None) -> dict:
    target_date = target_date or date.today()
    open_jobs = [x for x in jobs if x.get("status") not in ("Cobrado", "Cancelado")]
    exposure = sum(as_float(x.get("capital_financed")) for x in open_jobs)
    limit_ = as_float(settings.get("insurance_capital_limit"))
    aged = []
    for j in open_jobs:
        start = parse_date(j.get("capital_start_date") or j.get("delivery_date") or j.get("authorization_date"))
        days = (target_date - start).days if start else 0
        if days >= 30:
            aged.append((j, days))
    collected = [x for x in jobs if x.get("status") == "Cobrado" and parse_date(x.get("real_collection_date"))]
    dso_vals = []
    for x in collected:
        a = parse_date(x.get("billing_date")) or parse_date(x.get("delivery_date"))
        b = parse_date(x.get("real_collection_date"))
        if a and b:
            dso_vals.append((b - a).days)
    return {
        "open_jobs": open_jobs, "exposure": exposure, "limit": limit_, "utilization": safe_div(exposure, limit_),
        "aged": aged, "avg_dso": safe_div(sum(dso_vals), len(dso_vals)) if dso_vals else 0.0,
    }


def alerts(state: dict, settings: dict, target_date: date | None = None) -> list[dict]:
    target_date = target_date or date.today()
    out: list[dict] = []
    ots = state.get("work_orders", [])
    prod = production_metrics(ots, settings, target_date)
    for ot in prod["late"]:
        days = (target_date - parse_date(ot.get("promised_date"))).days
        out.append({"severity": "critical", "title": f"OT #{int(ot.get('number', 0)):05d} atrasada", "detail": f"{ot.get('plate') or 'Sin patente'} · {days} día(s) fuera de fecha · etapa {ot.get('stage')}"})
    for ot in prod["due_today"]:
        if ot.get("stage") != "Listo para entregar":
            out.append({"severity": "warning", "title": f"Entrega comprometida hoy", "detail": f"OT #{int(ot.get('number', 0)):05d} · {ot.get('plate')} sigue en {ot.get('stage')}"})
    for lead in state.get("leads", []):
        fd = parse_date(lead.get("next_followup"))
        if fd and fd <= target_date and lead.get("status") not in ("Ganado", "Perdido"):
            out.append({"severity": "warning", "title": "Seguimiento comercial pendiente", "detail": f"{lead.get('name')} · {lead.get('car') or ''} · {lead.get('status')}"})
    moves = state.get("financial_moves", [])
    for x in moves:
        due = parse_date(x.get("due_date"))
        if x.get("status") == "Pendiente" and due and due < target_date and not x.get("voided"):
            kind = "cobro" if x.get("direction") == "Ingreso" else "pago"
            out.append({"severity": "critical" if x.get("direction") == "Egreso" else "warning", "title": f"{kind.capitalize()} vencido", "detail": f"{x.get('counterparty') or x.get('category')} · ${as_float(x.get('amount')):,.0f}"})
    ins = insurance_summary(state.get("insurance_jobs", []), settings, target_date)
    if ins["limit"] and ins["utilization"] >= 0.80:
        out.append({"severity": "critical" if ins["utilization"] >= 1 else "warning", "title": "Cupo de seguros comprometido", "detail": f"Exposición {ins['utilization']*100:.0f}% del límite"})
    # stock alerts
    moves_m = state.get("material_moves", [])
    for m in state.get("material_catalog", []):
        from domain import current_stock  # local to avoid import cycles if refactored
        stock = current_stock(m.get("id"), moves_m)
        minimum = as_float(m.get("min_stock"))
        if m.get("active", True) and minimum > 0 and stock <= minimum:
            out.append({"severity": "warning", "title": "Stock bajo", "detail": f"{m.get('name')} · actual {stock:g} {m.get('unit','u')} · mínimo {minimum:g}"})
    order = {"critical": 0, "warning": 1, "info": 2}
    return sorted(out, key=lambda x: order.get(x.get("severity"), 9))

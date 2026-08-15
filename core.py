from __future__ import annotations

from datetime import date, datetime, timedelta
import base64
import calendar
import io
import json
import math
import re
import uuid
from typing import Any, Iterable

APP_NAME = "Taller OS"
APP_VERSION = "3.0 ULTRA"
DATA_FILE = "taller_os_data.json"

LEAD_STATES = ["Nuevo", "Contactado", "Cotizado", "Seguimiento", "Ganado", "Perdido"]
LEAD_SOURCES = ["QR / tarjeta", "Instagram", "Google", "Referido", "Aseguradora", "WhatsApp", "Facebook", "Cartelería", "Otro"]
LOSS_REASONS = ["Precio", "Demora", "No respondió", "Otro taller", "No arregla", "Financiación", "Otro"]
QUOTE_STATES = ["Borrador", "Enviado", "Seguimiento", "Aprobada", "Rechazada", "Vencida"]
PRODUCTION_STAGES = ["Esperando", "Desarme", "Chapa", "Preparación", "Pintura", "Armado", "Control de calidad", "Listo para entregar", "Entregado"]
PRIORITIES = ["Baja", "Normal", "Alta", "Urgente"]
DAMAGE_TYPES = ["Abolladura", "Rayón", "Golpe", "Óxido", "Rotura", "Desalineación", "Reemplazo", "Repintado", "Otro"]
DIFFICULTIES = ["Baja", "Media", "Alta", "Especial"]
ACCOUNTS = ["Caja", "Banco", "Mercado Pago", "Otro"]
MOVE_STATUS = ["Pagado", "Pendiente"]
MOVE_DIRECTIONS = ["Ingreso", "Egreso"]
FIN_CATEGORIES_IN = ["Cobro cliente", "Anticipo cliente", "Aporte socio", "Reintegro", "Otro ingreso"]
FIN_CATEGORIES_OUT = ["Pinturería", "Materiales", "Repuestos", "Tercerización", "Alquiler", "Servicios", "Impuestos", "Sueldos", "Retiro socio", "Herramientas", "Otro egreso"]
MATERIAL_MOVE_TYPES = ["Compra", "Consumo", "Ajuste +", "Ajuste -"]
QC_ITEMS = [
    "Terminación de chapa", "Preparación / nivelado", "Color y tono", "Barniz / brillo", "Sin polvo o inclusiones",
    "Armado y encastres", "Luces / accesorios", "Limpieza final", "Daños preexistentes documentados", "Prueba funcional"
]
ROLE_PERMISSIONS = {
    "Dueño": ["*"],
    "Socio técnico": ["hoy", "crm", "cotizador", "agenda", "ordenes", "produccion", "calidad", "materiales", "seguros", "reportes"],
    "Administración": ["hoy", "crm", "cotizador", "agenda", "ordenes", "materiales", "finanzas", "objetivos", "seguros", "proveedores", "reportes"],
    "Operario": ["hoy", "ordenes", "produccion", "calidad", "materiales"],
    "Solo lectura": ["hoy", "crm", "cotizador", "agenda", "ordenes", "produccion", "calidad", "materiales", "finanzas", "objetivos", "seguros", "proveedores", "reportes"],
}

DEFAULT_SETTINGS = {
    "business_name": "Taller OS",
    "currency": "ARS",
    "monthly_distributable_target": 6_666_667.0,
    "technical_share": 0.60,
    "business_share": 0.40,
    "monthly_fixed_structure": 0.0,
    "reserve_pct": 0.0,
    "labor_hour_cost": 0.0,
    "paint_hour_cost": 0.0,
    "paint_panel_cost": 0.0,
    "prep_hour_cost": 0.0,
    "assembly_hour_cost": 0.0,
    "floor_margin_pct": 0.25,
    "target_margin_pct": 0.40,
    "commercial_discount_max_pct": 0.10,
    "weekly_capacity_hours": 0.0,
    "insurance_capital_limit": 3_000_000.0,
    "default_quote_valid_days": 7,
    "default_payment_terms_days": 0,
    "wip_limit_chapa": 3,
    "wip_limit_pintura": 2,
    "wip_limit_armado": 3,
    "vat_pct": 0.0,
    "last_backup_at": None,
}

TABLES = [
    "leads", "quotes", "work_orders", "appointments", "material_catalog", "material_moves",
    "financial_moves", "insurance_jobs", "suppliers", "qc_checks", "audit_log", "users"
]


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def uid(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_date(value: Any) -> date | None:
    if value in (None, "", "None"):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except Exception:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        except Exception:
            return None


def money(value: Any, decimals: int = 0) -> str:
    n = as_float(value)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if decimals:
        s = f"{n:,.{decimals}f}"
    else:
        s = f"{n:,.0f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}$ {s}"


def pct(value: Any, digits: int = 1) -> str:
    return f"{as_float(value) * 100:.{digits}f}%".replace(".", ",")


def num(value: Any, digits: int = 1) -> str:
    n = as_float(value)
    return f"{n:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normalize_plate(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def business_days_in_month(d: date) -> list[date]:
    _, days = calendar.monthrange(d.year, d.month)
    return [date(d.year, d.month, i) for i in range(1, days + 1) if date(d.year, d.month, i).weekday() < 5]


def business_days_elapsed(d: date) -> int:
    return len([x for x in business_days_in_month(d) if x <= d])


def business_days_remaining(d: date) -> int:
    return len([x for x in business_days_in_month(d) if x > d])


def month_range(d: date) -> tuple[date, date]:
    start = date(d.year, d.month, 1)
    end = date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
    return start, end


def in_month(value: Any, d: date) -> bool:
    x = parse_date(value)
    return bool(x and x.year == d.year and x.month == d.month)


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def encode_uploads(files: Iterable[Any] | None, max_each_mb: float = 6.0) -> list[dict]:
    out: list[dict] = []
    max_bytes = int(max_each_mb * 1024 * 1024)
    for f in files or []:
        data = f.getvalue()
        if len(data) > max_bytes:
            continue
        out.append({
            "name": getattr(f, "name", "archivo"),
            "type": getattr(f, "type", "application/octet-stream"),
            "size": len(data),
            "data": base64.b64encode(data).decode("ascii"),
        })
    return out


def decode_upload(item: dict) -> bytes:
    return base64.b64decode(item.get("data", ""))


def deep_json_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def month_name_es(month: int) -> str:
    names = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return names[month] if 1 <= month <= 12 else ""


def human_days(delta: int) -> str:
    if delta == 0:
        return "hoy"
    if delta == 1:
        return "mañana"
    if delta == -1:
        return "ayer"
    return f"en {delta} días" if delta > 0 else f"hace {abs(delta)} días"

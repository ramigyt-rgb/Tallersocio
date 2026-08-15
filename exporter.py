from __future__ import annotations

import io
import json
import pandas as pd

from core import TABLES


def export_excel(state: dict) -> bytes:
    buff = io.BytesIO()
    with pd.ExcelWriter(buff, engine="openpyxl") as writer:
        pd.DataFrame([state.get("settings", {})]).to_excel(writer, index=False, sheet_name="Configuracion")
        mapping = {
            "leads":"Leads", "quotes":"Cotizaciones", "work_orders":"Ordenes", "appointments":"Agenda",
            "material_catalog":"Materiales", "material_moves":"Mov_materiales", "financial_moves":"Finanzas",
            "insurance_jobs":"Seguros", "suppliers":"Proveedores", "qc_checks":"Control_calidad", "audit_log":"Auditoria", "users":"Usuarios"
        }
        for table in TABLES:
            rows = state.get(table, [])
            normalized = []
            for row in rows:
                r = dict(row)
                for k, v in list(r.items()):
                    if isinstance(v, (list, dict)):
                        r[k] = json.dumps(v, ensure_ascii=False)
                normalized.append(r)
            pd.DataFrame(normalized).to_excel(writer, index=False, sheet_name=mapping.get(table, table)[:31])
    return buff.getvalue()

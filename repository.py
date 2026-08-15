from __future__ import annotations

from datetime import datetime
import uuid

import streamlit as st

from demo_data import demo_seed


TABLES = {
    "leads", "quotes", "work_orders", "materials", "material_movements",
    "financial_movements", "insurance_jobs", "audit_log", "settings", "app_users"
}


class RepositoryError(RuntimeError):
    pass


class BaseRepository:
    mode = "local_demo"

    def list_rows(self, table: str) -> list[dict]:
        raise NotImplementedError

    def insert(self, table: str, payload: dict, actor: dict | None = None, audit_description: str | None = None) -> dict:
        raise NotImplementedError

    def update(self, table: str, row_id: str, payload: dict, actor: dict | None = None, audit_description: str | None = None) -> dict:
        raise NotImplementedError

    def next_number(self, table: str, field: str = "number", start: int = 1) -> int:
        rows = self.list_rows(table)
        values = []
        for row in rows:
            try:
                values.append(int(row.get(field, 0)))
            except (TypeError, ValueError):
                pass
        return max(values, default=start - 1) + 1

    def get_settings(self) -> dict:
        rows = self.list_rows("settings")
        return rows[0] if rows else {}

    def audit(self, actor: dict | None, action: str, entity: str, entity_id: str, description: str) -> None:
        actor = actor or {}
        self.insert(
            "audit_log",
            {
                "actor_user_id": actor.get("id"),
                "actor_name": actor.get("full_name") or actor.get("username") or "Sistema",
                "action": action,
                "entity": entity,
                "entity_id": str(entity_id),
                "description": description,
            },
            actor=None,
            audit_description=None,
        )

    def upload_files(self, files, folder: str) -> list[str]:
        # En esta versión visual no se persisten archivos. Se conserva el nombre
        # para que el flujo pueda probarse de punta a punta.
        return [getattr(f, "name", "archivo") for f in (files or [])]


class LocalDemoRepository(BaseRepository):
    """Repositorio temporal en memoria de la sesión de Streamlit.

    No usa servicios externos ni archivos locales como persistencia.
    Sirve exclusivamente para recorrer y probar Taller OS antes de conectar
    Google Sheets en una etapa posterior.
    """

    mode = "local_demo"

    def __init__(self):
        if "taller_local_demo" not in st.session_state:
            st.session_state["taller_local_demo"] = demo_seed()
        self.data = st.session_state["taller_local_demo"]

    def list_rows(self, table: str) -> list[dict]:
        if table not in TABLES:
            raise RepositoryError(f"Sección no permitida: {table}")
        return list(self.data.get(table, []))

    def insert(self, table: str, payload: dict, actor: dict | None = None, audit_description: str | None = None) -> dict:
        if table not in TABLES:
            raise RepositoryError(f"Sección no permitida: {table}")
        row = dict(payload)
        row.setdefault("id", str(uuid.uuid4()))
        row.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
        self.data.setdefault(table, []).insert(0, row)
        if audit_description and table != "audit_log":
            self.audit(actor, "CREÓ", table.upper(), row["id"], audit_description)
        return row

    def update(self, table: str, row_id: str, payload: dict, actor: dict | None = None, audit_description: str | None = None) -> dict:
        if table not in TABLES:
            raise RepositoryError(f"Sección no permitida: {table}")
        for row in self.data.get(table, []):
            if str(row.get("id")) == str(row_id):
                row.update(payload)
                row["updated_at"] = datetime.now().isoformat(timespec="seconds")
                if audit_description and table != "audit_log":
                    self.audit(actor, "MODIFICÓ", table.upper(), row_id, audit_description)
                return row
        raise RepositoryError(f"No se encontró el registro {row_id}")


def get_repository(cfg=None) -> BaseRepository:
    if "repo" not in st.session_state or getattr(st.session_state["repo"], "mode", None) != "local_demo":
        st.session_state["repo"] = LocalDemoRepository()
    return st.session_state["repo"]

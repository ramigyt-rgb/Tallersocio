from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from core import DATA_FILE, DEFAULT_SETTINGS, TABLES, deep_json_copy, now_iso, uid


class StoreError(RuntimeError):
    pass


def _empty_state() -> dict:
    return {
        "schema_version": 3,
        "settings": deep_json_copy(DEFAULT_SETTINGS),
        **{table: [] for table in TABLES},
    }


class LocalJsonStore:
    """Persistencia plana local. No usa SQL ni una base de datos.

    Está deliberadamente aislada detrás de esta clase para poder reemplazarla por
    Google Sheets sin tocar las pantallas ni la lógica de negocio.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or DATA_FILE)
        self._ensure()

    def _ensure(self) -> None:
        if not self.path.exists():
            self._atomic_write(_empty_state())
            return
        try:
            state = self._read()
            changed = False
            for table in TABLES:
                if table not in state:
                    state[table] = []
                    changed = True
            defaults = deep_json_copy(DEFAULT_SETTINGS)
            defaults.update(state.get("settings") or {})
            if defaults != state.get("settings"):
                state["settings"] = defaults
                changed = True
            if changed:
                self._atomic_write(state)
        except Exception as exc:
            raise StoreError(f"No se pudo abrir {self.path.name}: {exc}") from exc

    def _read(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _atomic_write(self, state: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix="taller_os_", suffix=".tmp", dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp_name, self.path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def state(self) -> dict:
        return self._read()

    def list(self, table: str) -> list[dict]:
        state = self._read()
        return deep_json_copy(state.get(table, []))

    def get(self, table: str, row_id: str) -> dict | None:
        for row in self.list(table):
            if str(row.get("id")) == str(row_id):
                return row
        return None

    def settings(self) -> dict:
        state = self._read()
        merged = deep_json_copy(DEFAULT_SETTINGS)
        merged.update(state.get("settings") or {})
        return merged

    def save_settings(self, patch: dict, actor: dict | None = None) -> dict:
        state = self._read()
        current = deep_json_copy(DEFAULT_SETTINGS)
        current.update(state.get("settings") or {})
        current.update(patch)
        state["settings"] = current
        self._append_audit(state, actor, "UPDATE", "settings", "settings", "Actualizó parámetros generales del taller")
        self._atomic_write(state)
        return deep_json_copy(current)

    def insert(self, table: str, payload: dict, actor: dict | None = None, description: str | None = None) -> dict:
        if table not in TABLES:
            raise StoreError(f"Tabla desconocida: {table}")
        state = self._read()
        row = deep_json_copy(payload)
        row.setdefault("id", uid(table[:3]))
        row.setdefault("created_at", now_iso())
        row["updated_at"] = now_iso()
        state[table].append(row)
        if table != "audit_log":
            self._append_audit(state, actor, "CREATE", table, str(row["id"]), description or f"Creó registro en {table}")
        self._atomic_write(state)
        return deep_json_copy(row)

    def update(self, table: str, row_id: str, patch: dict, actor: dict | None = None, description: str | None = None) -> dict:
        if table not in TABLES:
            raise StoreError(f"Tabla desconocida: {table}")
        state = self._read()
        for idx, row in enumerate(state[table]):
            if str(row.get("id")) == str(row_id):
                before = deep_json_copy(row)
                row.update(deep_json_copy(patch))
                row["updated_at"] = now_iso()
                state[table][idx] = row
                if table != "audit_log":
                    changed = [k for k in patch if before.get(k) != row.get(k)]
                    detail = description or (f"Modificó {table}: " + ", ".join(changed[:8]))
                    self._append_audit(state, actor, "UPDATE", table, str(row_id), detail)
                self._atomic_write(state)
                return deep_json_copy(row)
        raise StoreError(f"No se encontró el registro {row_id} en {table}.")

    def bulk_replace(self, state: dict, actor: dict | None = None) -> None:
        cleaned = _empty_state()
        cleaned["schema_version"] = max(3, int(state.get("schema_version", 3)))
        settings = deep_json_copy(DEFAULT_SETTINGS)
        settings.update(state.get("settings") or {})
        cleaned["settings"] = settings
        for table in TABLES:
            rows = state.get(table, [])
            cleaned[table] = rows if isinstance(rows, list) else []
        self._append_audit(cleaned, actor, "IMPORT", "system", "snapshot", "Importó un respaldo completo")
        self._atomic_write(cleaned)

    def reset(self, actor: dict | None = None) -> None:
        state = _empty_state()
        self._append_audit(state, actor, "RESET", "system", "all", "Reinició todos los datos operativos")
        self._atomic_write(state)

    def next_number(self, table: str, field: str = "number", start: int = 1) -> int:
        nums = []
        for row in self.list(table):
            try:
                nums.append(int(row.get(field, 0)))
            except Exception:
                pass
        return max(nums, default=start - 1) + 1

    def snapshot_bytes(self) -> bytes:
        return json.dumps(self._read(), ensure_ascii=False, indent=2).encode("utf-8")

    def _append_audit(self, state: dict, actor: dict | None, action: str, entity: str, entity_id: str, description: str) -> None:
        actor = actor or {}
        state.setdefault("audit_log", []).append({
            "id": uid("aud"),
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "actor_id": actor.get("id", "owner"),
            "actor_name": actor.get("full_name", "Dueño"),
            "actor_role": actor.get("role", "Dueño"),
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "description": description,
        })

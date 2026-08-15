from __future__ import annotations

ROLE_PERMISSIONS = {
    "Dueño": {"*"},
    "Socio técnico": {"hoy","captacion","cotizador","ordenes","produccion","materiales","objetivos","seguros","auditoria"},
    "Administración": {"hoy","captacion","cotizador","ordenes","produccion","materiales","finanzas","objetivos","seguros","auditoria"},
    "Operario": {"hoy","ordenes","produccion","materiales"},
    "Solo lectura": {"hoy","captacion","ordenes","produccion","materiales","finanzas","objetivos","seguros","auditoria"},
}


def can(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or permission in perms


def can_write(role: str) -> bool:
    return role not in {"Solo lectura"}

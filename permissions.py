from core import ROLE_PERMISSIONS


def can(role: str, page: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, [])
    return "*" in perms or page in perms

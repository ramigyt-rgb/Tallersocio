from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Configuración local de Taller OS.

    En esta versión no existe ninguna conexión a base de datos.
    La app usa datos de demostración en memoria para poder recorrerla completa.
    """
    mode: str = "local_demo"


def get_config() -> AppConfig:
    return AppConfig()

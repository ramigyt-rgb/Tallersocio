from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import streamlit as st

st.set_page_config(
    page_title="Taller OS",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import get_config
from theme import apply_theme
from repository import get_repository, RepositoryError, BaseRepository
from auth import require_login
from permissions import can
import view_hoy as hoy
import view_captacion as captacion
import view_cotizador as cotizador
import view_ordenes as ordenes
import view_produccion as produccion
import view_materiales as materiales
import view_finanzas as finanzas
import view_objetivos as objetivos
import view_seguros as seguros
import view_auditoria as auditoria
import view_configuracion as configuracion


class ReadOnlyRepo:
    """Wrapper para conservar el esquema de permisos de la app."""
    def __init__(self, inner: BaseRepository):
        self.inner = inner
        self.mode = inner.mode

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def insert(self, *args, **kwargs):
        raise RepositoryError("Tu rol es Solo lectura: no puede crear registros.")

    def update(self, *args, **kwargs):
        raise RepositoryError("Tu rol es Solo lectura: no puede modificar registros.")

    def upload_files(self, *args, **kwargs):
        raise RepositoryError("Tu rol es Solo lectura: no puede subir archivos.")


def main():
    apply_theme()
    cfg = get_config()
    base_repo = get_repository(cfg)
    user = require_login(base_repo)
    role = user.get("role", "Dueño")
    repo = ReadOnlyRepo(base_repo) if role == "Solo lectura" else base_repo
    settings = base_repo.get_settings()

    with st.sidebar:
        st.markdown("# Taller OS")
        st.caption("Sistema operativo del taller")
        st.markdown('<span class="mode-demo">VISTA DEMO · SIN BASE</span>', unsafe_allow_html=True)
        st.write("")
        st.caption(f'Vista: **{user.get("full_name", "Dueño")}**')
        st.caption(f'Rol: **{role}**')
        st.divider()

        pages = [
            ("hoy", "◉  HOY"),
            ("captacion", "◎  Captación"),
            ("cotizador", "▧  Cotizador"),
            ("ordenes", "▤  Órdenes de trabajo"),
            ("produccion", "▦  Producción"),
            ("materiales", "◫  Materiales"),
            ("finanzas", "$  Caja y finanzas"),
            ("objetivos", "↗  Objetivo diario"),
            ("seguros", "◇  Seguros"),
            ("auditoria", "≡  Auditoría"),
        ]
        allowed = [(key, label) for key, label in pages if can(role, key)]
        if role == "Dueño":
            allowed.append(("configuracion", "⚙  Configuración"))

        labels = [label for _, label in allowed]
        selected_label = st.radio("Navegación", labels, label_visibility="collapsed")
        selected = {label: key for key, label in allowed}[selected_label]

    renderers = {
        "hoy": hoy.render,
        "captacion": captacion.render,
        "cotizador": cotizador.render,
        "ordenes": ordenes.render,
        "produccion": produccion.render,
        "materiales": materiales.render,
        "finanzas": finanzas.render,
        "objetivos": objetivos.render,
        "seguros": seguros.render,
        "auditoria": auditoria.render,
        "configuracion": configuracion.render,
    }

    try:
        renderers[selected](repo, user, settings)
    except RepositoryError as exc:
        st.error(str(exc))

    st.divider()
    st.caption(
        "Vista de demostración: podés recorrer, cargar y modificar datos durante la sesión. "
        "Por ahora no hay ninguna base conectada. La persistencia con Google Sheets la integramos después."
    )


if __name__ == "__main__":
    main()

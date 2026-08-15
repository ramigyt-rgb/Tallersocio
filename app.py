from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import streamlit as st

st.set_page_config(page_title="Taller OS", page_icon="🛠️", layout="wide", initial_sidebar_state="expanded")

from core import APP_NAME, APP_VERSION
from store import LocalJsonStore, StoreError
from theme import apply_theme
from permissions import can

import view_hoy
import view_crm
import view_cotizador
import view_agenda
import view_ordenes
import view_produccion
import view_calidad
import view_materiales
import view_finanzas
import view_objetivos
import view_seguros
import view_proveedores
import view_reportes
import view_auditoria
import view_configuracion
import view_datos


PAGES = [
    ("hoy", "◉  HOY", view_hoy.render),
    ("crm", "◎  Captación & CRM", view_crm.render),
    ("cotizador", "▧  Cotizador PRO", view_cotizador.render),
    ("agenda", "◷  Agenda & capacidad", view_agenda.render),
    ("ordenes", "▤  Órdenes de trabajo", view_ordenes.render),
    ("produccion", "▦  Producción", view_produccion.render),
    ("calidad", "✓  Control de calidad", view_calidad.render),
    ("materiales", "◫  Materiales & stock", view_materiales.render),
    ("finanzas", "$  Caja & finanzas", view_finanzas.render),
    ("objetivos", "↗  Objetivos & reparto", view_objetivos.render),
    ("seguros", "◇  Seguros", view_seguros.render),
    ("proveedores", "◈  Proveedores", view_proveedores.render),
    ("reportes", "▥  Reportes & rentabilidad", view_reportes.render),
    ("auditoria", "≡  Auditoría", view_auditoria.render),
    ("configuracion", "⚙  Configuración", view_configuracion.render),
    ("datos", "⇄  Centro de datos", view_datos.render),
]


def _actor() -> dict:
    # Acceso directo por ahora. La capa de permisos ya está lista para conectar
    # autenticación cuando se defina la fuente de usuarios.
    return {"id": "owner", "full_name": "Dueño", "role": "Dueño"}


def main():
    apply_theme()
    try:
        store = LocalJsonStore()
    except StoreError as exc:
        st.error(str(exc))
        st.stop()

    actor = _actor()
    settings = store.settings()

    with st.sidebar:
        st.markdown(f'<div class="tos-brand">{APP_NAME}<small>{APP_VERSION}</small></div>', unsafe_allow_html=True)
        st.caption("Sistema operativo integral del taller")
        st.markdown('<span class="tos-badge">OPERACIÓN REAL · ARCHIVO LOCAL</span>', unsafe_allow_html=True)
        st.write("")
        st.caption(f"Sesión: **{actor['full_name']}** · {actor['role']}")
        st.divider()
        allowed = [(key, label, renderer) for key, label, renderer in PAGES if can(actor["role"], key)]
        labels = [x[1] for x in allowed]
        selected_label = st.radio("Navegación", labels, label_visibility="collapsed")
        selected = next(x for x in allowed if x[1] == selected_label)
        st.divider()
        st.caption("Persistencia actual")
        st.markdown("**taller_os_data.json**")
        st.caption("La app está desacoplada para migrar esta capa a Google Sheets más adelante.")

    try:
        selected[2](store, actor, settings)
    except StoreError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error("Se produjo un error al procesar esta pantalla.")
        with st.expander("Detalle técnico"):
            st.exception(exc)


if __name__ == "__main__":
    main()

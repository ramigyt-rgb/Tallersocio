from __future__ import annotations

import streamlit as st


DEMO_OWNER = {
    "id": "local-owner",
    "username": "dueno",
    "full_name": "Dueño",
    "role": "Dueño",
    "active": True,
}


def current_user() -> dict:
    return st.session_state.get("user", DEMO_OWNER)


def require_login(repo=None) -> dict:
    """Acceso directo mientras Taller OS está en etapa visual/demo."""
    st.session_state["user"] = DEMO_OWNER
    return DEMO_OWNER


def logout_button() -> None:
    # Sin autenticación por ahora. Se mantiene la función para no romper app.py.
    return None

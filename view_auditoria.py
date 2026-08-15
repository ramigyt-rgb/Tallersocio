from __future__ import annotations

import pandas as pd
import streamlit as st

from theme import page_title
from ui import empty_state


def render(store, actor, settings):
    page_title("Auditoría", "Quién hizo qué, cuándo y sobre qué registro. Este historial no se edita desde la interfaz.")
    rows=store.list("audit_log")
    if not rows:
        empty_state("Sin eventos todavía","Cada alta, modificación, anulación, importación o cambio de configuración genera una traza automática.")
        return
    df=pd.DataFrame(rows)
    c1,c2,c3=st.columns(3)
    actor_filter=c1.multiselect("Actor",sorted(df["actor_name"].dropna().unique().tolist())) if "actor_name" in df else []
    entity_filter=c2.multiselect("Entidad",sorted(df["entity"].dropna().unique().tolist())) if "entity" in df else []
    action_filter=c3.multiselect("Acción",sorted(df["action"].dropna().unique().tolist())) if "action" in df else []
    if actor_filter: df=df[df["actor_name"].isin(actor_filter)]
    if entity_filter: df=df[df["entity"].isin(entity_filter)]
    if action_filter: df=df[df["action"].isin(action_filter)]
    if "created_at" in df: df=df.sort_values("created_at",ascending=False)
    st.dataframe(df[[c for c in ["created_at","actor_name","actor_role","action","entity","entity_id","description"] if c in df.columns]],hide_index=True,width="stretch")
    st.caption(f"{len(df)} evento(s) mostrados. No existe acción de borrado de auditoría en Taller OS.")

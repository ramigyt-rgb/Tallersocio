from __future__ import annotations

import pandas as pd
import streamlit as st

from theme import page_title


def render(repo,user,settings):
    page_title("Auditoría", "Quién hizo qué, cuándo y sobre qué registro. La transparencia es parte del sistema.")
    rows=repo.list_rows("audit_log")
    if not rows:
        st.info("Todavía no hay eventos de auditoría.")
        return
    df=pd.DataFrame(rows)
    keep=[c for c in ["created_at","actor_name","action","entity","entity_id","description"] if c in df.columns]
    if "created_at" in df.columns:
        df=df.sort_values("created_at",ascending=False)
    st.dataframe(df[keep],use_container_width=True,hide_index=True)
    st.caption("En producción, además del historial de la app, la base bloquea el DELETE de movimientos financieros mediante un trigger SQL.")

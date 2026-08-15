from __future__ import annotations

from datetime import date
import streamlit as st

from theme import page_title
from metrics import PRODUCTION_STAGES
from utils import money, safe_date


def render(repo, user, settings):
    page_title("Producción", "Tablero vivo: qué está pasando, qué falta y qué vehículo corre riesgo de atraso.")
    ots = [o for o in repo.list_rows("work_orders") if not o.get("archived") and o.get("stage") != "Entregado"]
    today = date.today()
    for row_start in range(0, len(PRODUCTION_STAGES)-1, 4):
        stages = PRODUCTION_STAGES[row_start:row_start+4]
        cols = st.columns(len(stages))
        for col, stage in zip(cols, stages):
            with col:
                items = [o for o in ots if o.get("stage") == stage]
                st.markdown(f"#### {stage} · {len(items)}")
                for o in items:
                    promised = safe_date(o.get("promised_date"))
                    late = promised and promised < today
                    delta = (promised - today).days if promised else None
                    balance = float(o.get("agreed_amount") or 0)-float(o.get("paid_amount") or 0)
                    st.markdown(
                        f'<div class="tos-stage-card"><div class="plate">{o.get("plate") or "SIN PATENTE"}</div>'
                        f'<div class="car">{o.get("car") or "—"}</div><br>'
                        f'<span class="tos-pill">OT #{int(o.get("number",0)):05d}</span> '
                        f'<span class="tos-pill">Saldo {money(balance)}</span><br><br>'
                        f'<div class="tos-muted">Prometido: {promised or "—"} {"· ATRASADO" if late else (f"· {delta} días" if delta is not None else "")}</div></div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("### Movimiento rápido")
    if ots:
        labels = {f'#{int(o.get("number",0)):05d} · {o.get("plate")} · {o.get("stage")}':o for o in ots}
        chosen = st.selectbox("OT", list(labels.keys()), key="prod_ot")
        ot = labels[chosen]
        current = ot.get("stage")
        idx = PRODUCTION_STAGES.index(current) if current in PRODUCTION_STAGES else 0
        c1,c2 = st.columns([2,1])
        new_stage = c1.selectbox("Mover a", PRODUCTION_STAGES, index=min(idx+1,len(PRODUCTION_STAGES)-1), key="prod_stage")
        missing = c2.text_input("Qué falta / bloqueo", value="")
        if st.button("Actualizar producción", type="primary"):
            notes = (ot.get("notes") or "")
            if missing.strip():
                notes = (notes + f"\nBloqueo: {missing.strip()}").strip()
            payload={"stage":new_stage,"notes":notes}
            if new_stage=="Entregado" and not ot.get("delivery_date"):
                payload["delivery_date"]=today.isoformat()
            repo.update("work_orders", ot["id"], payload, user, f"Movió OT #{int(ot.get('number',0)):05d} de {current} a {new_stage}")
            st.success("Producción actualizada.")
            st.rerun()
    else:
        st.info("No hay autos activos.")

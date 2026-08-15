from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from core import as_float, business_days_elapsed, business_days_in_month, money, month_name_es
from domain import objective_status, month_profit
from theme import page_title
from ui import progress


def render(store, actor, settings):
    today=date.today(); ots=store.list("work_orders"); mats=store.list("material_moves")
    obj=objective_status(ots,mats,settings,today)
    page_title("Objetivos & reparto", "El objetivo se mide sobre utilidad distribuible, no sobre facturación bruta.")

    st.markdown(f"### {month_name_es(today.month)} {today.year}")
    a,b,c,d=st.columns(4)
    a.metric("Objetivo utilidad distribuible",money(obj["target"]))
    b.metric("Real acumulado",money(obj["distributable"]),delta=money(obj["gap"]))
    c.metric("Proyección cierre",money(obj["projected"]))
    d.metric("Ritmo necesario",money(obj["required_daily"])+" / día")
    progress(obj["progress"])
    st.caption(f"Quedan {obj['remaining_days']} días hábiles. Objetivo acumulado al día: {money(obj['accumulated_target'])}.")

    st.markdown("### Puente económico")
    rows=[
        ("Facturación entregada",obj["revenue"]),
        ("− Costos directos reales",-obj["directs"]),
        ("= Margen de contribución",obj["contribution"]),
        ("− Estructura proporcional acumulada",-obj["fixed_mtd"]),
        ("= Resultado operativo",obj["operating"]),
        ("− Reserva",-obj["reserve"]),
        ("= Utilidad distribuible",obj["distributable"]),
    ]
    st.dataframe(pd.DataFrame(rows,columns=["Concepto","Monto"]),hide_index=True,width="stretch",column_config={"Monto":st.column_config.NumberColumn(format="$ %.0f")})

    st.markdown("### Distribución")
    c1,c2=st.columns(2)
    c1.markdown(f'''<div class="tos-card"><div class="tos-kicker">SOCIO TÉCNICO · {as_float(settings.get('technical_share'))*100:.0f}%</div><div class="tos-big">{money(max(0,obj['technical_share']))}</div><div class="tos-muted">Objetivo teórico del mes: {money(as_float(settings.get('monthly_distributable_target'))*as_float(settings.get('technical_share')))}</div></div>''',unsafe_allow_html=True)
    c2.markdown(f'''<div class="tos-card"><div class="tos-kicker">SOCIO EMPRESARIO · {as_float(settings.get('business_share'))*100:.0f}%</div><div class="tos-big">{money(max(0,obj['business_share']))}</div><div class="tos-muted">Objetivo teórico del mes: {money(as_float(settings.get('monthly_distributable_target'))*as_float(settings.get('business_share')))}</div></div>''',unsafe_allow_html=True)

    st.markdown("### Simulador de cierre")
    c1,c2,c3=st.columns(3)
    extra_revenue=c1.number_input("Facturación adicional a entregar",min_value=0.0,step=100000.0)
    direct_pct=c2.slider("Costo directo estimado",0,90,30,1)/100
    extra_fixed=c3.number_input("Gastos de estructura adicionales",min_value=0.0,step=50000.0)
    contribution=extra_revenue*(1-direct_pct)
    future_operating=obj["operating"]+contribution-extra_fixed
    reserve=max(0,future_operating)*as_float(settings.get("reserve_pct"))
    future_dist=future_operating-reserve
    a,b,c=st.columns(3); a.metric("Distribuible proyectada",money(future_dist)); b.metric("Socio técnico",money(max(0,future_dist)*as_float(settings.get("technical_share")))); c.metric("Socio empresario",money(max(0,future_dist)*as_float(settings.get("business_share"))))

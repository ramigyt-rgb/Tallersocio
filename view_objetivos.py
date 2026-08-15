from __future__ import annotations

from datetime import date
import streamlit as st

from theme import page_title
from metrics import workshop_snapshot
from utils import money


def render(repo, user, settings):
    page_title("Objetivo diario", "No mide sólo facturación: baja hasta utilidad distribuible y recalcula el ritmo necesario cada día.")
    snap=workshop_snapshot(repo,date.today(),settings)

    st.markdown("### Objetivo del mes")
    a,b,c=st.columns(3)
    a.metric("Utilidad distribuible objetivo",money(snap["target"]))
    b.metric(f'Socio técnico · {float(settings.get("technical_share",.6))*100:.0f}%',money(snap["target"]*float(settings.get("technical_share",.6))))
    c.metric(f'Socio empresario · {float(settings.get("owner_share",.4))*100:.0f}%',money(snap["target"]*float(settings.get("owner_share",.4))))

    st.markdown("### Resultado acumulado")
    rows=[
        ("Facturación / trabajos computados",snap["revenue"]),
        ("− Materiales + repuestos + terceros",-snap["direct_cost"]),
        ("= Margen de contribución",snap["contribution"]),
        ("− Estructura proporcional acumulada",-snap["fixed_accrued"]),
        ("= Resultado operativo",snap["operating"]),
        (f'− Reserva {float(settings.get("reserve_rate",0))*100:.0f}%',-(max(0,snap["operating"])*float(settings.get("reserve_rate",0)))),
        ("= Utilidad distribuible",snap["distributable"]),
    ]
    for label,val in rows:
        c1,c2=st.columns([3,1])
        c1.write(label)
        c2.markdown(f'**{money(val)}**')
        st.divider()

    a,b,c,d=st.columns(4)
    a.metric("Objetivo acumulado",money(snap["target_acc"]))
    b.metric("Real acumulado",money(snap["distributable"]),delta=money(snap["deviation"]))
    c.metric("Días hábiles restantes",snap["remaining_bdays"])
    d.metric("Nuevo ritmo necesario",money(snap["needed_daily"]) + "/día")

    st.markdown("### Distribución si cerráramos hoy")
    a,b=st.columns(2)
    a.metric("60% socio técnico",money(snap["tech_share"]))
    b.metric("40% socio empresario",money(snap["owner_share"]))
    st.caption("Los porcentajes se leen desde Configuración; si cambian, el tablero se recalcula automáticamente.")

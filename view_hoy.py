from __future__ import annotations

from datetime import date
import streamlit as st

from theme import page_title, flow_strip
from metrics import workshop_snapshot
from utils import money


def render(repo, user, settings):
    today = date.today()
    snap = workshop_snapshot(repo, today, settings)
    page_title("HOY", today.strftime("%A %d de %B de %Y").capitalize())
    flow_strip()

    a,b,c,d = st.columns(4)
    a.metric("Autos activos", snap["active_cars"])
    b.metric("Entregas hoy", snap["deliveries_today"])
    c.metric("Ingresos programados", snap["scheduled_today"])
    d.metric("Presupuestos pendientes", snap["pending_quotes"])

    a,b,c,d = st.columns(4)
    a.metric("Objetivo acumulado", money(snap["target_acc"]))
    a.caption("Utilidad distribuible objetivo a esta altura del mes")
    b.metric("Real acumulado", money(snap["distributable"]), delta=money(snap["deviation"]))
    b.caption("Luego de directos, estructura acumulada y reserva")
    c.metric("Capacidad próxima semana", f'{snap["capacity"]*100:.0f}%')
    c.caption("Carga proyectada contra capacidad configurada")
    d.metric("Caja disponible", money(snap["cash"]))
    d.caption("Ingresos cobrados menos egresos pagados/cargados")

    st.markdown("### Pulso del negocio")
    x,y,z = st.columns(3)
    with x:
        st.markdown('<div class="tos-card">', unsafe_allow_html=True)
        st.caption("POR COBRAR")
        st.markdown(f'### {money(snap["receivable"])}')
        st.caption(f'Cuenta pinturería / materiales: {money(snap["paint_payable"])}')
        st.markdown('</div>', unsafe_allow_html=True)
    with y:
        st.markdown('<div class="tos-card">', unsafe_allow_html=True)
        st.caption("PROYECCIÓN UTILIDAD MES")
        cls = "tos-good" if snap["projection"] >= snap["target"] else "tos-warn"
        st.markdown(f'<div class="tos-big {cls}">{money(snap["projection"])}</div>', unsafe_allow_html=True)
        st.caption(f'Objetivo: {money(snap["target"])}')
        st.markdown('</div>', unsafe_allow_html=True)
    with z:
        st.markdown('<div class="tos-card">', unsafe_allow_html=True)
        st.caption("SEGUROS · CAPITAL EXPUESTO")
        usage = snap["insurance_usage"]
        cls = "tos-bad" if usage >= 1 else "tos-warn" if usage >= .8 else "tos-good"
        st.markdown(f'<div class="tos-big {cls}">{money(snap["insurance_exposure"])}</div>', unsafe_allow_html=True)
        st.caption(f'{usage*100:.0f}% de {money(snap["insurance_limit"])}')
        st.markdown('</div>', unsafe_allow_html=True)

    remaining = snap["remaining_bdays"]
    if snap["needed_daily"] > 0:
        st.markdown(
            f'<div class="tos-alert"><b>Ritmo necesario.</b> Quedan {remaining} días hábiles y necesitamos generar <b>{money(snap["needed_daily"])}</b> de utilidad distribuible por día para alcanzar el objetivo.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.success("El objetivo mensual ya está cubierto con el resultado acumulado.")

    if snap["late_orders"]:
        st.markdown("### Atención inmediata")
        for o in snap["late_orders"][:5]:
            st.error(f'OT #{int(o.get("number",0)):05d} · {o.get("plate","—")} · {o.get("car","—")} · prometido {o.get("promised_date","—")}', icon="⏱️")

from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from core import money, month_name_es, parse_date, as_float
from domain import alerts, finance_summary, insurance_summary, objective_status, pipeline_metrics, production_metrics, work_order_margin
from theme import page_title, flow_strip
from ui import alert_box, empty_state, progress


def render(store, actor, settings):
    today = date.today()
    state = store.state()
    ots = state["work_orders"]
    leads = state["leads"]
    quotes = state["quotes"]
    moves = state["financial_moves"]
    mats = state["material_moves"]
    ins_jobs = state["insurance_jobs"]

    page_title("HOY", f"{today.strftime('%A %d/%m/%Y')} · lectura ejecutiva y operativa del taller")
    flow_strip()

    prod = production_metrics(ots, settings, today)
    fin = finance_summary(moves, today)
    obj = objective_status(ots, mats, settings, today)
    pipe = pipeline_metrics(leads, quotes)
    ins = insurance_summary(ins_jobs, settings, today)

    appointments_today = [x for x in state["appointments"] if parse_date(x.get("start_date")) == today and x.get("status") != "Cancelado"]
    quote_pending = [q for q in quotes if q.get("status") in ("Borrador", "Enviado", "Seguimiento")]

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Autos activos", len(prod["active"]), delta=f"{len(prod['late'])} atrasados" if prod["late"] else "Sin atrasos")
    c2.metric("Entregas hoy", len(prod["due_today"]))
    c3.metric("Agenda hoy", len(appointments_today))
    c4.metric("Presupuestos abiertos", len(quote_pending), delta=money(pipe["quote_pipeline_value"]))
    c5.metric("Caja disponible", money(fin["cash_total"]))
    c6.metric("Por cobrar", money(fin["receivable"]), delta=f"Vencido {money(fin['overdue_receivable'])}" if fin["overdue_receivable"] else None)

    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        target = obj["target"]
        real = obj["distributable"]
        gap = obj["gap"]
        cls = "tos-ok" if gap >= 0 else "tos-bad"
        st.markdown(
            f'''<div class="tos-hero"><div class="label">Objetivo · {month_name_es(today.month)} {today.year}</div>
            <div class="value">{money(real)}</div><div class="sub">Utilidad distribuible acumulada · objetivo mensual {money(target)}</div>
            <div class="sub">Objetivo acumulado al día: {money(obj['accumulated_target'])} · Desvío: <b>{money(gap)}</b></div></div>''',
            unsafe_allow_html=True,
        )
        st.write("")
        progress(obj["progress"])
        a,b,c = st.columns(3)
        a.metric("Días hábiles restantes", obj["remaining_days"])
        b.metric("Ritmo necesario", money(obj["required_daily"]) + "/día")
        b.caption("Para llegar a la utilidad distribuible objetivo.")
        c.metric("Proyección al cierre", money(obj["projected"]))

    with right:
        st.markdown("### Radar de riesgo")
        alert_list = alerts(state, settings, today)
        if alert_list:
            for a in alert_list[:7]:
                alert_box(a["title"], a["detail"], a["severity"])
            if len(alert_list) > 7:
                st.caption(f"+ {len(alert_list)-7} alertas adicionales en los módulos correspondientes.")
        else:
            empty_state("Sin alertas críticas", "No hay vencimientos, atrasos ni mínimos disparados con los datos actuales.")

    st.markdown("### Operación en curso")
    if prod["active"]:
        rows=[]
        for ot in prod["active"]:
            m=work_order_margin(ot,mats)
            promised=parse_date(ot.get("promised_date"))
            rows.append({
                "OT":f"#{int(ot.get('number',0)):05d}","Patente":ot.get("plate"),"Vehículo":ot.get("car"),"Etapa":ot.get("stage"),
                "Prioridad":ot.get("priority","Normal"),"Prometido":promised,"Monto":m["revenue"],"Costo real":m["direct_cost"],"Margen actual":m["margin"],
                "Estado fecha":"ATRASADO" if promised and promised<today else "En término"
            })
        df=pd.DataFrame(rows)
        st.dataframe(df,width="stretch",hide_index=True,column_config={
            "Monto":st.column_config.NumberColumn(format="$ %.0f"),"Costo real":st.column_config.NumberColumn(format="$ %.0f"),"Margen actual":st.column_config.NumberColumn(format="$ %.0f")
        })
    else:
        empty_state("No hay autos activos", "Creá una OT o convertí una cotización aprobada para comenzar a poblar producción.")

    st.markdown("### Pulso comercial y financiero")
    a,b,c,d = st.columns(4)
    a.metric("Leads abiertos", sum(1 for x in leads if x.get("status") not in ("Ganado","Perdido")))
    b.metric("Conversión cerrados", f"{pipe['win_rate']*100:.1f}%")
    c.metric("Por pagar", money(fin["payable"]), delta=f"Vencido {money(fin['overdue_payable'])}" if fin["overdue_payable"] else None)
    d.metric("Capital en seguros", money(ins["exposure"]), delta=f"{ins['utilization']*100:.0f}% del cupo" if ins["limit"] else "Cupo sin configurar")

    if not any(len(state[t]) for t in ["leads","quotes","work_orders","financial_moves"]):
        st.info("La aplicación está vacía a propósito: no contiene datos demo. Empezá por Captación & CRM o por una Orden de Trabajo directa.")

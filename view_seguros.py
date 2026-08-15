from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from core import as_float, money, parse_date
from domain import insurance_summary
from theme import page_title
from ui import empty_state, progress


def render(store, actor, settings):
    page_title("Seguros", "Control separado de capital inmovilizado, autorización, facturación, cobranza, margen y cupo máximo de exposición.")
    jobs=store.list("insurance_jobs"); ots=store.list("work_orders")
    summary=insurance_summary(jobs,settings)
    a,b,c,d=st.columns(4)
    a.metric("Cupo máximo",money(summary["limit"]))
    b.metric("Capital expuesto",money(summary["exposure"]),delta=f"{summary['utilization']*100:.0f}% utilizado" if summary["limit"] else "Sin límite")
    c.metric("Disponible",money(max(0,summary["limit"]-summary["exposure"])))
    d.metric("DSO promedio",f"{summary['avg_dso']:.1f} días")
    if summary["limit"]: progress(summary["utilization"],good_at=.7)
    if summary["utilization"]>=1: st.error("Cupo excedido: no conviene financiar nuevos trabajos de seguros sin liberar capital.")
    elif summary["utilization"]>=.8: st.warning("Cupo de seguros por encima del 80%.")

    tabs=st.tabs(["Cartera","Nuevo trabajo seguro","Cobranza & aging","Rentabilidad"])
    with tabs[0]:
        if jobs:
            rows=[]
            for j in jobs:
                start=parse_date(j.get("capital_start_date") or j.get("authorization_date")); days=(date.today()-start).days if start and j.get("status")!="Cobrado" else 0
                rows.append({"Aseguradora":j.get("insurer"),"Siniestro":j.get("claim_number"),"OT":j.get("ot_number"),"Patente":j.get("plate"),"Estado":j.get("status"),"Aprobado":j.get("approved_amount"),"Capital financiado":j.get("capital_financed"),"Días inmovilizado":days,"Cobro estimado":parse_date(j.get("estimated_collection_date")),"Cobro real":parse_date(j.get("real_collection_date"))})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={"Aprobado":st.column_config.NumberColumn(format="$ %.0f"),"Capital financiado":st.column_config.NumberColumn(format="$ %.0f")})
        else: empty_state("Sin trabajos de aseguradoras","La cartera de seguros se mantiene separada de particulares para medir el capital que queda inmovilizado.")

    with tabs[1]:
        available_ots=[o for o in ots if not o.get("cancelled")]
        with st.form("new_insurance",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            insurer=c1.text_input("Aseguradora *")
            claim=c2.text_input("N° siniestro / autorización")
            ot=c3.selectbox("OT relacionada",[None]+available_ots,format_func=lambda x:"— Sin OT todavía —" if x is None else f"#{int(x.get('number',0)):05d} · {x.get('plate')}")
            c1,c2,c3,c4=st.columns(4)
            auth=c1.date_input("Fecha autorización",value=date.today())
            approved=c2.number_input("Monto aprobado",min_value=0.0,step=10000.0)
            materials=c3.number_input("Costo materiales",min_value=0.0,step=5000.0)
            capital=c4.number_input("Capital financiado por ustedes",min_value=0.0,step=10000.0)
            c1,c2,c3=st.columns(3)
            delivery=c1.date_input("Entrega estimada",value=date.today()+timedelta(days=7))
            billing=c2.date_input("Facturación estimada",value=date.today()+timedelta(days=7))
            collection=c3.date_input("Cobro estimado",value=date.today()+timedelta(days=45))
            notes=st.text_area("Condiciones / observaciones")
            ok=st.form_submit_button("Registrar trabajo de seguro",type="primary",width="stretch")
        if ok:
            projected=summary["exposure"]+capital
            if not insurer.strip() or approved<=0: st.error("Aseguradora y monto aprobado son obligatorios.")
            elif summary["limit"] and projected>summary["limit"]:
                st.error(f"Este trabajo llevaría la exposición a {money(projected)}, por encima del cupo de {money(summary['limit'])}.")
            else:
                store.insert("insurance_jobs",{"insurer":insurer.strip(),"claim_number":claim.strip(),"work_order_id":ot.get("id") if ot else None,"ot_number":f"#{int(ot.get('number',0)):05d}" if ot else None,"plate":ot.get("plate") if ot else None,"authorization_date":auth.isoformat(),"approved_amount":approved,"material_cost":materials,"capital_financed":capital,"capital_start_date":auth.isoformat(),"delivery_date":delivery.isoformat(),"billing_date":billing.isoformat(),"estimated_collection_date":collection.isoformat(),"real_collection_date":None,"status":"Autorizado","notes":notes.strip()},actor,f"Registró seguro {insurer.strip()} · {money(approved)}")
                st.success("Trabajo de seguro registrado."); st.rerun()

    with tabs[2]:
        open_jobs=[j for j in jobs if j.get("status") not in ("Cobrado","Cancelado")]
        if open_jobs:
            sel=st.selectbox("Trabajo",open_jobs,format_func=lambda j:f"{j.get('insurer')} · {j.get('plate') or j.get('claim_number')} · {money(j.get('approved_amount'))}")
            c1,c2=st.columns(2)
            status=c1.selectbox("Estado",["Autorizado","En reparación","Entregado","Facturado","Cobrado"],index=["Autorizado","En reparación","Entregado","Facturado","Cobrado"].index(sel.get("status")) if sel.get("status") in ["Autorizado","En reparación","Entregado","Facturado","Cobrado"] else 0)
            real_date=c2.date_input("Fecha real de cobro",value=date.today())
            if st.button("Actualizar seguro",type="primary"):
                patch={"status":status}
                if status=="Cobrado": patch["real_collection_date"]=real_date.isoformat()
                store.update("insurance_jobs",sel["id"],patch,actor,f"Actualizó seguro {sel.get('insurer')} a {status}")
                st.rerun()
        else: empty_state("Sin cobranza pendiente","No hay capital de seguros abierto.")
        if summary["aged"]:
            st.markdown("#### Aging > 30 días")
            for j,days in summary["aged"]: st.warning(f"{j.get('insurer')} · {j.get('plate') or j.get('claim_number')} · {days} días · {money(j.get('capital_financed'))}")

    with tabs[3]:
        if jobs:
            rows=[]
            for j in jobs:
                revenue=as_float(j.get("approved_amount")); materials=as_float(j.get("material_cost")); capital=as_float(j.get("capital_financed")); margin=revenue-materials
                rows.append({"Aseguradora":j.get("insurer"),"Patente":j.get("plate"),"Aprobado":revenue,"Materiales":materials,"Margen antes otros directos":margin,"Margen %":margin/revenue*100 if revenue else 0,"Capital financiado":capital})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={k:st.column_config.NumberColumn(format="$ %.0f") for k in ["Aprobado","Materiales","Margen antes otros directos","Capital financiado"]}|{"Margen %":st.column_config.NumberColumn(format="%.1f%%")})
        else: empty_state("Sin datos de rentabilidad","Los trabajos de seguro registrados alimentan esta comparación.")

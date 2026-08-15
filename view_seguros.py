from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from theme import page_title
from metrics import workshop_snapshot
from utils import money, safe_date


def render(repo,user,settings):
    page_title("Seguros", "Separado de particulares: mide capital financiado, días de caja inmovilizada, margen y fecha real de cobro.")
    jobs=repo.list_rows("insurance_jobs")
    ots=repo.list_rows("work_orders")
    snap=workshop_snapshot(repo,date.today(),settings)

    a,b,c=st.columns(3)
    a.metric("Cupo máximo de capital",money(snap["insurance_limit"]))
    b.metric("Actualmente expuesto",money(snap["insurance_exposure"]))
    usage=snap["insurance_usage"]
    c.metric("Cupo utilizado",f"{usage*100:.0f}%",delta=f'{money(max(0,snap["insurance_limit"]-snap["insurance_exposure"]))} libre')
    st.progress(min(1.0,usage))
    if usage>=1:
        st.error("Cupo agotado: aceptar más trabajos financiados aumenta el riesgo de caja.")
    elif usage>=.8:
        st.warning("Cupo de seguros en zona amarilla: revisar antes de aceptar nuevos trabajos grandes.")

    tabs=st.tabs(["Cartera","Nuevo trabajo de seguro","Cobranza"])
    with tabs[0]:
        if jobs:
            df=pd.DataFrame(jobs)
            today=date.today()
            def days(row):
                start=safe_date(row.get("delivery_date")) or safe_date(row.get("authorization_date"))
                end=safe_date(row.get("actual_collection_date")) or today
                return (end-start).days if start else 0
            df["dias_inmovilizados"]=df.apply(days,axis=1)
            keep=[c for c in ["insurer","work_order_id","approved_amount","material_cost","capital_financed","margin","collection_status","estimated_collection_date","actual_collection_date","dias_inmovilizados"] if c in df.columns]
            st.dataframe(df[keep],use_container_width=True,hide_index=True,column_config={
                "approved_amount":st.column_config.NumberColumn("Aprobado",format="$ %.0f"),"material_cost":st.column_config.NumberColumn("Materiales",format="$ %.0f"),
                "capital_financed":st.column_config.NumberColumn("Capital financiado",format="$ %.0f"),"margin":st.column_config.NumberColumn("Margen",format="$ %.0f")})
        else:
            st.info("No hay trabajos de aseguradora.")

    with tabs[1]:
        with st.form("new_insurance",clear_on_submit=True):
            insurer=st.text_input("Aseguradora *")
            active=[o for o in ots if o.get("stage")!="Entregado"]
            labels=["— Sin asociar —"]+[f'#{int(o.get("number",0)):05d} · {o.get("plate")} · {o.get("car")}' for o in active]
            sel=st.selectbox("OT",labels)
            c1,c2,c3=st.columns(3)
            auth=c1.date_input("Fecha autorización")
            approved=c2.number_input("Monto aprobado",min_value=0.0,step=10000.0)
            materials=c3.number_input("Costo materiales",min_value=0.0,step=10000.0)
            c1,c2,c3=st.columns(3)
            capital=c1.number_input("Capital financiado por nosotros",min_value=0.0,step=10000.0)
            margin=c2.number_input("Margen esperado",min_value=0.0,step=10000.0)
            est=c3.date_input("Fecha estimada cobro")
            notes=st.text_area("Observaciones")
            ok=st.form_submit_button("Registrar trabajo de seguro",type="primary",use_container_width=True)
        if ok:
            if not insurer.strip():
                st.error("Indicá la aseguradora.")
            elif snap["insurance_exposure"]+capital>snap["insurance_limit"]:
                st.error("Este trabajo supera el cupo de capital configurado. Podés aumentar el cupo en Configuración si la decisión es consciente.")
            else:
                ot_id="" if sel=="— Sin asociar —" else active[labels.index(sel)-1]["id"]
                repo.insert("insurance_jobs",{"work_order_id":ot_id,"insurer":insurer.strip(),"authorization_date":auth.isoformat(),"approved_amount":approved,
                    "material_cost":materials,"capital_financed":capital,"delivery_date":None,"invoice_date":None,"estimated_collection_date":est.isoformat(),
                    "actual_collection_date":None,"collection_status":"Pendiente","margin":margin,"notes":notes.strip()},user,f"Registró trabajo de {insurer.strip()} · capital expuesto {money(capital)}")
                st.success("Trabajo de seguro registrado.")
                st.rerun()

    with tabs[2]:
        open_jobs=[j for j in jobs if j.get("collection_status")!="Cobrado"]
        if open_jobs:
            labels={f'{j.get("insurer")} · {money(j.get("approved_amount"))} · {j.get("collection_status")}':j for j in open_jobs}
            chosen=st.selectbox("Trabajo",list(labels.keys()))
            job=labels[chosen]
            c1,c2=st.columns(2)
            new_status=c1.selectbox("Estado",["Pendiente","Entregado","Facturado","Cobrado"],index=["Pendiente","Entregado","Facturado","Cobrado"].index(job.get("collection_status")) if job.get("collection_status") in ["Pendiente","Entregado","Facturado","Cobrado"] else 0)
            invoice=c2.date_input("Fecha facturación",value=safe_date(job.get("invoice_date")) or date.today())
            if st.button("Actualizar cobranza",type="primary"):
                payload={"collection_status":new_status}
                if new_status in {"Facturado","Cobrado"}: payload["invoice_date"]=invoice.isoformat()
                if new_status=="Cobrado": payload["actual_collection_date"]=date.today().isoformat()
                repo.update("insurance_jobs",job["id"],payload,user,f"Actualizó cobranza de {job.get('insurer')} a {new_status}")
                st.success("Cobranza actualizada.")
                st.rerun()
        else:
            st.success("No hay trabajos de seguros pendientes de cobro.")

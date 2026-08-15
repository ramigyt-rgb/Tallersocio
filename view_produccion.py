from __future__ import annotations

from datetime import date, datetime
import pandas as pd
import streamlit as st

from core import PRODUCTION_STAGES, money, parse_date, as_float
from domain import production_metrics, work_order_margin
from theme import page_title, flow_strip
from ui import empty_state, stage_card


def render(store, actor, settings):
    page_title("Producción", "Kanban operativo, WIP, atrasos, bloqueos y movimiento controlado de cada vehículo.")
    flow_strip("PRODUCCIÓN")
    ots=store.list("work_orders")
    mats=store.list("material_moves")
    active=[o for o in ots if o.get("stage")!="Entregado" and not o.get("cancelled")]
    metrics=production_metrics(ots,settings)

    a,b,c,d=st.columns(4)
    a.metric("WIP activo",len(active))
    b.metric("Atrasados",len(metrics["late"]))
    c.metric("Horas comprometidas",f"{metrics['open_hours']:.1f} h")
    d.metric("Carga / capacidad",f"{metrics['capacity_pct']*100:.0f}%" if as_float(settings.get("weekly_capacity_hours")) else "Sin configurar")

    tabs=st.tabs(["Tablero","Mover trabajo","Bloqueos","Performance"])
    with tabs[0]:
        if not active:
            empty_state("Producción vacía","Las OT activas se organizan automáticamente por etapa.")
        else:
            # 3 columnas por fila para que cada tarjeta conserve legibilidad.
            for start in range(0,len(PRODUCTION_STAGES)-1,3):
                stages=PRODUCTION_STAGES[start:start+3]
                cols=st.columns(len(stages))
                for col,stage in zip(cols,stages):
                    with col:
                        items=[o for o in active if o.get("stage")==stage]
                        limit={"Chapa":int(settings.get("wip_limit_chapa",3)),"Pintura":int(settings.get("wip_limit_pintura",2)),"Armado":int(settings.get("wip_limit_armado",3))}.get(stage)
                        title=f"{stage} · {len(items)}"+(f" / {limit}" if limit else "")
                        st.markdown(f"#### {title}")
                        if limit and len(items)>limit: st.error("WIP por encima del límite configurado.")
                        for o in items:
                            promised=parse_date(o.get("promised_date")); late=bool(promised and promised<date.today())
                            balance=as_float(o.get("agreed_amount"))-as_float(o.get("paid_amount"))
                            stage_card(o,balance,late)
                            if o.get("blocker"): st.caption(f"⛔ {o.get('blocker')}")

    with tabs[1]:
        if not active: empty_state("Sin trabajos para mover","Creá una OT primero.")
        else:
            sel=st.selectbox("OT",active,format_func=lambda o:f"#{int(o.get('number',0)):05d} · {o.get('plate')} · {o.get('stage')}")
            current=sel.get("stage","Esperando"); idx=PRODUCTION_STAGES.index(current) if current in PRODUCTION_STAGES else 0
            c1,c2,c3=st.columns(3)
            new_stage=c1.selectbox("Nueva etapa",PRODUCTION_STAGES,index=min(idx+1,len(PRODUCTION_STAGES)-1))
            blocker=c2.text_input("Bloqueo / qué falta",value=sel.get("blocker") or "")
            percent=c3.slider("Avance técnico estimado",0,100,int(sel.get("progress_pct") or 0),5)
            notes=st.text_area("Parte / observación de producción",value=sel.get("production_notes") or "")
            if st.button("Actualizar producción",type="primary",width="stretch"):
                patch={"stage":new_stage,"blocker":blocker.strip(),"progress_pct":percent,"production_notes":notes.strip(),"last_stage_change":datetime.now().replace(microsecond=0).isoformat()}
                if new_stage=="Entregado":
                    qc=[x for x in store.list("qc_checks") if x.get("work_order_id")==sel.get("id")]
                    latest=qc[-1] if qc else None
                    if not latest or latest.get("result")!="Aprobado":
                        st.error("No se puede entregar: la OT necesita un Control de Calidad aprobado.")
                        st.stop()
                    patch["delivery_date"]=date.today().isoformat(); patch["progress_pct"]=100
                store.update("work_orders",sel["id"],patch,actor,f"Movió OT #{int(sel.get('number',0)):05d} de {current} a {new_stage}")
                if new_stage=="Entregado":
                    balance=max(0.0,as_float(sel.get("agreed_amount"))-as_float(sel.get("paid_amount")))
                    fin_moves=store.list("financial_moves")
                    already=any(x.get("work_order_id")==sel.get("id") and x.get("direction")=="Ingreso" and x.get("status")=="Pendiente" and not x.get("voided") for x in fin_moves)
                    if balance>0 and not already:
                        from datetime import timedelta
                        due=date.today()+timedelta(days=int(settings.get("default_payment_terms_days",0)))
                        store.insert("financial_moves",{
                            "movement_date":date.today().isoformat(),"direction":"Ingreso","category":"Cobro cliente","account":"Caja",
                            "amount":balance,"status":"Pendiente","due_date":due.isoformat(),"paid_date":None,
                            "counterparty":sel.get("customer_name"),"work_order_id":sel.get("id"),
                            "notes":f"Saldo final OT #{int(sel.get('number',0)):05d}","voided":False
                        },actor,f"Generó cuenta a cobrar por saldo de OT #{int(sel.get('number',0)):05d}")
                st.success("Producción actualizada."); st.rerun()

    with tabs[2]:
        blocked=[o for o in active if (o.get("blocker") or "").strip()]
        if blocked:
            rows=[]
            for o in blocked:
                promised=parse_date(o.get("promised_date")); days=(promised-date.today()).days if promised else None
                rows.append({"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Etapa":o.get("stage"),"Bloqueo":o.get("blocker"),"Prometido":promised,"Días a compromiso":days})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
        else: empty_state("Sin bloqueos declarados","Cuando una OT quede esperando repuesto, material, cliente o tercero, registralo desde Mover trabajo.")

    with tabs[3]:
        delivered=[o for o in ots if o.get("stage")=="Entregado" and parse_date(o.get("entry_date")) and parse_date(o.get("delivery_date"))]
        if delivered:
            rows=[]
            for o in delivered:
                cycle=(parse_date(o.get("delivery_date"))-parse_date(o.get("entry_date"))).days
                promised=parse_date(o.get("promised_date")); ontime=bool(not promised or parse_date(o.get("delivery_date"))<=promised)
                m=work_order_margin(o,mats)
                rows.append({"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Días ciclo":cycle,"En fecha":ontime,"Margen %":m["margin_pct"]*100})
            df=pd.DataFrame(rows)
            a,b,c=st.columns(3); a.metric("Ciclo promedio",f"{df['Días ciclo'].mean():.1f} días"); b.metric("Entregas en fecha",f"{df['En fecha'].mean()*100:.1f}%"); c.metric("Margen promedio",f"{df['Margen %'].mean():.1f}%")
            st.dataframe(df,hide_index=True,width="stretch",column_config={"Margen %":st.column_config.NumberColumn(format="%.1f%%")})
        else: empty_state("Todavía no hay ciclos cerrados","Al entregar trabajos, esta pantalla empieza a medir velocidad y cumplimiento real.")

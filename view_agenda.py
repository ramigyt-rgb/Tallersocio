from __future__ import annotations

from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

from core import PRIORITIES, as_float, parse_date
from theme import page_title
from ui import empty_state


def render(store, actor, settings):
    page_title("Agenda & capacidad", "Turnos, visitas, ingresos, entregas y carga futura del taller en una sola agenda.")
    appointments=store.list("appointments")
    ots=store.list("work_orders")
    tabs=st.tabs(["Agenda","Nuevo turno","Capacidad próxima","Compromisos de OT"])

    with tabs[0]:
        if appointments:
            df=pd.DataFrame(appointments)
            df["start_date"]=pd.to_datetime(df["start_date"],errors="coerce")
            df=df.sort_values(["start_date","start_time"])
            st.dataframe(df[[c for c in ["start_date","start_time","type","customer_name","plate","title","duration_hours","status","priority"] if c in df.columns]],hide_index=True,width="stretch",
                column_config={"duration_hours":st.column_config.NumberColumn("Horas",format="%.1f")})
            future=[x for x in appointments if parse_date(x.get("start_date")) and parse_date(x.get("start_date"))>=date.today() and x.get("status")!="Cancelado"]
            if future:
                sel=st.selectbox("Gestionar turno",future,format_func=lambda x:f"{x.get('start_date')} {x.get('start_time','')} · {x.get('title')} · {x.get('plate') or ''}")
                c1,c2=st.columns(2)
                status=c1.selectbox("Estado",["Programado","Confirmado","Realizado","Cancelado"],index=["Programado","Confirmado","Realizado","Cancelado"].index(sel.get("status")) if sel.get("status") in ["Programado","Confirmado","Realizado","Cancelado"] else 0)
                if c2.button("Actualizar turno",type="primary"):
                    store.update("appointments",sel["id"],{"status":status},actor,f"Actualizó turno {sel.get('title')} a {status}"); st.rerun()
        else: empty_state("Agenda vacía","Programá una visita, ingreso, entrega o tarea interna.")

    with tabs[1]:
        with st.form("new_appt",clear_on_submit=True):
            c1,c2,c3,c4=st.columns(4)
            d=c1.date_input("Fecha",value=date.today())
            t=c2.time_input("Hora",value=datetime.now().replace(minute=0,second=0,microsecond=0).time())
            typ=c3.selectbox("Tipo",["Visita a vehículo","Ingreso","Entrega","Seguimiento","Producción","Proveedor","Administrativo","Otro"])
            priority=c4.selectbox("Prioridad",PRIORITIES,index=1)
            c1,c2,c3=st.columns(3)
            customer=c1.text_input("Cliente")
            plate=c2.text_input("Patente")
            hours=c3.number_input("Duración / carga estimada (h)",min_value=0.0,step=.5)
            title=st.text_input("Título *")
            notes=st.text_area("Notas")
            ok=st.form_submit_button("Programar",type="primary",width="stretch")
        if ok:
            if not title.strip(): st.error("El título es obligatorio.")
            else:
                store.insert("appointments",{"start_date":d.isoformat(),"start_time":t.strftime("%H:%M"),"type":typ,"priority":priority,"customer_name":customer.strip(),"plate":plate.strip().upper(),"duration_hours":hours,"title":title.strip(),"notes":notes.strip(),"status":"Programado"},actor,f"Programó {typ}: {title.strip()}")
                st.success("Turno programado."); st.rerun()

    with tabs[2]:
        start=date.today(); end=start+timedelta(days=13)
        future=[x for x in appointments if parse_date(x.get("start_date")) and start<=parse_date(x.get("start_date"))<=end and x.get("status")!="Cancelado"]
        days=[]
        weekly=as_float(settings.get("weekly_capacity_hours"))
        daily_cap=weekly/5 if weekly else 0
        for i in range(14):
            d=start+timedelta(days=i)
            if d.weekday()>=5: continue
            load=sum(as_float(x.get("duration_hours")) for x in future if parse_date(x.get("start_date"))==d)
            days.append({"Fecha":d,"Carga h":load,"Capacidad h":daily_cap,"Ocupación %":load/daily_cap*100 if daily_cap else 0})
        df=pd.DataFrame(days)
        st.dataframe(df,width="stretch",hide_index=True,column_config={"Ocupación %":st.column_config.ProgressColumn(min_value=0,max_value=120,format="%.0f%%")})
        if not weekly: st.warning("Configurá horas productivas semanales para que la ocupación sea significativa.")

    with tabs[3]:
        pending=[o for o in ots if o.get("stage")!="Entregado" and not o.get("cancelled")]
        if pending:
            rows=[{"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Cliente":o.get("customer_name"),"Etapa":o.get("stage"),"Ingreso":parse_date(o.get("entry_date")),"Prometido":parse_date(o.get("promised_date")),"Horas est.":o.get("estimated_hours",0)} for o in pending]
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
        else: empty_state("Sin compromisos productivos","Las fechas prometidas de las OT se consolidan acá.")

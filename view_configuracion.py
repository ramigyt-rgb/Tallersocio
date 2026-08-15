from __future__ import annotations

import pandas as pd
import streamlit as st

from core import DEFAULT_SETTINGS, ROLE_PERMISSIONS, as_float, money
from theme import page_title


def render(store, actor, settings):
    page_title("Configuración", "Parámetros centrales del negocio. Los cambios afectan cálculos futuros y quedan auditados.")
    tabs=st.tabs(["Economía","Cotizador","Capacidad","Seguros","Usuarios & permisos"])

    with tabs[0]:
        with st.form("settings_econ"):
            c1,c2=st.columns(2)
            monthly_target=c1.number_input("Objetivo mensual de utilidad distribuible",min_value=0.0,value=as_float(settings.get("monthly_distributable_target")),step=100000.0)
            fixed=c2.number_input("Estructura fija mensual",min_value=0.0,value=as_float(settings.get("monthly_fixed_structure")),step=50000.0)
            c1,c2,c3=st.columns(3)
            technical=c1.number_input("Socio técnico %",min_value=0.0,max_value=100.0,value=as_float(settings.get("technical_share"))*100,step=1.0)
            business=c2.number_input("Socio empresario %",min_value=0.0,max_value=100.0,value=as_float(settings.get("business_share"))*100,step=1.0)
            reserve=c3.number_input("Reserva % del resultado operativo positivo",min_value=0.0,max_value=100.0,value=as_float(settings.get("reserve_pct"))*100,step=1.0)
            ok=st.form_submit_button("Guardar economía",type="primary",width="stretch")
        if ok:
            if abs((technical+business)-100)>0.01: st.error("La distribución entre socios debe sumar 100%.")
            else:
                store.save_settings({"monthly_distributable_target":monthly_target,"monthly_fixed_structure":fixed,"technical_share":technical/100,"business_share":business/100,"reserve_pct":reserve/100},actor); st.success("Parámetros económicos actualizados."); st.rerun()

    with tabs[1]:
        with st.form("settings_quote"):
            c1,c2,c3=st.columns(3)
            labor=c1.number_input("Costo hora chapa",min_value=0.0,value=as_float(settings.get("labor_hour_cost")),step=1000.0)
            prep=c2.number_input("Costo hora preparación",min_value=0.0,value=as_float(settings.get("prep_hour_cost")),step=1000.0)
            paint_h=c3.number_input("Costo hora pintura",min_value=0.0,value=as_float(settings.get("paint_hour_cost")),step=1000.0)
            c1,c2,c3=st.columns(3)
            assembly=c1.number_input("Costo hora armado/desarme",min_value=0.0,value=as_float(settings.get("assembly_hour_cost")),step=1000.0)
            panel=c2.number_input("Costo pintura por paño",min_value=0.0,value=as_float(settings.get("paint_panel_cost")),step=1000.0)
            valid=c3.number_input("Validez cotización (días)",min_value=1,value=int(settings.get("default_quote_valid_days",7)),step=1)
            c1,c2,c3=st.columns(3)
            floor=c1.number_input("Margen piso %",min_value=0.0,max_value=95.0,value=as_float(settings.get("floor_margin_pct"))*100,step=1.0)
            target=c2.number_input("Margen objetivo %",min_value=0.0,max_value=95.0,value=as_float(settings.get("target_margin_pct"))*100,step=1.0)
            discount=c3.number_input("Descuento comercial máximo %",min_value=0.0,max_value=100.0,value=as_float(settings.get("commercial_discount_max_pct"))*100,step=1.0)
            ok=st.form_submit_button("Guardar cotizador",type="primary",width="stretch")
        if ok:
            if floor>=target: st.error("El margen objetivo debería ser mayor al margen piso.")
            else:
                store.save_settings({"labor_hour_cost":labor,"prep_hour_cost":prep,"paint_hour_cost":paint_h,"assembly_hour_cost":assembly,"paint_panel_cost":panel,"default_quote_valid_days":valid,"floor_margin_pct":floor/100,"target_margin_pct":target/100,"commercial_discount_max_pct":discount/100},actor); st.success("Cotizador actualizado."); st.rerun()

    with tabs[2]:
        with st.form("settings_capacity"):
            weekly=st.number_input("Horas productivas disponibles por semana",min_value=0.0,value=as_float(settings.get("weekly_capacity_hours")),step=1.0)
            c1,c2,c3=st.columns(3)
            wip_chapa=c1.number_input("WIP máximo Chapa",min_value=1,value=int(settings.get("wip_limit_chapa",3)),step=1)
            wip_paint=c2.number_input("WIP máximo Pintura",min_value=1,value=int(settings.get("wip_limit_pintura",2)),step=1)
            wip_arm=c3.number_input("WIP máximo Armado",min_value=1,value=int(settings.get("wip_limit_armado",3)),step=1)
            ok=st.form_submit_button("Guardar capacidad",type="primary",width="stretch")
        if ok:
            store.save_settings({"weekly_capacity_hours":weekly,"wip_limit_chapa":wip_chapa,"wip_limit_pintura":wip_paint,"wip_limit_armado":wip_arm},actor); st.success("Capacidad actualizada."); st.rerun()

    with tabs[3]:
        with st.form("settings_ins"):
            limit_=st.number_input("Cupo máximo de capital para seguros",min_value=0.0,value=as_float(settings.get("insurance_capital_limit")),step=100000.0)
            ok=st.form_submit_button("Guardar cupo",type="primary",width="stretch")
        if ok: store.save_settings({"insurance_capital_limit":limit_},actor); st.success("Cupo actualizado."); st.rerun()

    with tabs[4]:
        st.markdown("#### Matriz de permisos preparada")
        rows=[]
        pages=["hoy","crm","cotizador","agenda","ordenes","produccion","calidad","materiales","finanzas","objetivos","seguros","proveedores","reportes","auditoria","configuracion","datos"]
        for role,perms in ROLE_PERMISSIONS.items():
            rows.append({"Rol":role,**{p:("Sí" if "*" in perms or p in perms else "—") for p in pages}})
        st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
        st.info("El acceso actual entra directo como Dueño para que puedas trabajar y evaluar el sistema. La autenticación puede conectarse a la misma fuente que definamos para usuarios cuando integremos Google Sheets.")

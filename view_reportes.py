from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from core import as_float, money, parse_date, in_month
from domain import work_order_margin, pipeline_metrics, finance_summary
from exporter import export_excel
from theme import page_title
from ui import empty_state


def render(store, actor, settings):
    page_title("Reportes & rentabilidad", "Lectura gerencial: rentabilidad por auto, tiempos, captación, caja y exportación integral.")
    state=store.state(); ots=state["work_orders"]; mats=state["material_moves"]; leads=state["leads"]; quotes=state["quotes"]
    tabs=st.tabs(["Rentabilidad por OT","Unidad económica","Comercial","Productividad","Exportar"])

    with tabs[0]:
        if ots:
            rows=[]
            for o in ots:
                m=work_order_margin(o,mats)
                rows.append({"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Vehículo":o.get("car"),"Cliente":o.get("customer_name"),"Etapa":o.get("stage"),"Venta":m["revenue"],"Costo directo":m["direct_cost"],"Margen":m["margin"],"Margen %":m["margin_pct"]*100,"Ingreso":parse_date(o.get("entry_date")),"Entrega":parse_date(o.get("delivery_date"))})
            df=pd.DataFrame(rows).sort_values("Margen",ascending=False)
            st.dataframe(df,hide_index=True,width="stretch",column_config={k:st.column_config.NumberColumn(format="$ %.0f") for k in ["Venta","Costo directo","Margen"]}|{"Margen %":st.column_config.NumberColumn(format="%.1f%%")})
            c1,c2,c3=st.columns(3)
            c1.metric("Venta registrada",money(df["Venta"].sum()))
            c2.metric("Margen acumulado",money(df["Margen"].sum()))
            c3.metric("Margen ponderado",f"{df['Margen'].sum()/df['Venta'].sum()*100:.1f}%" if df["Venta"].sum() else "0,0%")
        else: empty_state("Sin OT para analizar","La rentabilidad se calcula con el monto acordado y costos reales imputados.")

    with tabs[1]:
        delivered=[o for o in ots if o.get("stage")=="Entregado"]
        if delivered:
            rows=[]
            for o in delivered:
                m=work_order_margin(o,mats); cycle=None
                if parse_date(o.get("entry_date")) and parse_date(o.get("delivery_date")): cycle=(parse_date(o.get("delivery_date"))-parse_date(o.get("entry_date"))).days
                rows.append({"Vehículo":o.get("car"),"Patente":o.get("plate"),"Venta":m["revenue"],"Costo directo":m["direct_cost"],"Margen":m["margin"],"Días ciclo":cycle,"Margen/día":m["margin"]/max(1,cycle or 1)})
            df=pd.DataFrame(rows)
            st.dataframe(df,hide_index=True,width="stretch",column_config={k:st.column_config.NumberColumn(format="$ %.0f") for k in ["Venta","Costo directo","Margen","Margen/día"]})
            st.caption("Margen/día ayuda a detectar trabajos que parecen rentables pero ocupan demasiada capacidad.")
        else: empty_state("Todavía no hay trabajos entregados","La unidad económica se vuelve mucho más útil cuando existen ciclos cerrados.")

    with tabs[2]:
        p=pipeline_metrics(leads,quotes)
        a,b,c,d=st.columns(4); a.metric("Leads",p["total"]); b.metric("Ganados",p["won"]); c.metric("Conversión",f"{p['win_rate']*100:.1f}%"); d.metric("Pipeline cotizado",money(p["quote_pipeline_value"]))
        if leads:
            df=pd.DataFrame(leads)
            source=df.groupby("source",dropna=False).agg(Leads=("id","count"),Ganados=("status",lambda x:(x=="Ganado").sum()),Perdidos=("status",lambda x:(x=="Perdido").sum())).reset_index()
            denom=source["Ganados"]+source["Perdidos"]
            source["Conversión %"]=(source["Ganados"].div(denom.where(denom.ne(0),1))*100).where(denom.ne(0),0).astype(float)
            st.dataframe(source,hide_index=True,width="stretch",column_config={"Conversión %":st.column_config.NumberColumn(format="%.1f%%")})
            st.bar_chart(source.set_index("source")["Leads"])
        else: empty_state("Sin captación todavía","Los canales empiezan a compararse cuando cargues leads reales.")

    with tabs[3]:
        delivered=[o for o in ots if parse_date(o.get("entry_date")) and parse_date(o.get("delivery_date"))]
        if delivered:
            rows=[]
            for o in delivered:
                entry=parse_date(o.get("entry_date")); delivery=parse_date(o.get("delivery_date")); promised=parse_date(o.get("promised_date")); cycle=(delivery-entry).days
                rows.append({"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Días ciclo":cycle,"En fecha":not promised or delivery<=promised,"Horas estimadas":as_float(o.get("estimated_hours"))})
            df=pd.DataFrame(rows)
            a,b,c=st.columns(3); a.metric("Ciclo promedio",f"{df['Días ciclo'].mean():.1f} días"); b.metric("Cumplimiento",f"{df['En fecha'].mean()*100:.1f}%"); c.metric("OT entregadas",len(df))
            st.dataframe(df,hide_index=True,width="stretch")
        else: empty_state("Sin ciclos productivos cerrados","Entregas y fechas prometidas alimentan productividad y cumplimiento.")

    with tabs[4]:
        excel=export_excel(state)
        st.download_button("Descargar libro Excel completo",data=excel,file_name=f"Taller_OS_{date.today().isoformat()}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",type="primary",width="stretch")
        st.caption("Incluye hojas separadas para configuración, leads, cotizaciones, OT, agenda, materiales, finanzas, seguros, proveedores, calidad, auditoría y usuarios.")

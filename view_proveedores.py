from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from core import as_float, money, parse_date
from theme import page_title
from ui import empty_state


def render(store, actor, settings):
    page_title("Proveedores", "Pinturerías, repuesteros y terceros con condiciones, cuenta corriente y concentración de compras.")
    suppliers=store.list("suppliers"); fin=store.list("financial_moves"); mm=store.list("material_moves")
    tabs=st.tabs(["Directorio","Nuevo proveedor","Cuenta corriente","Compras por proveedor"])
    with tabs[0]:
        if suppliers:
            rows=[]
            for s in suppliers:
                pending=sum(as_float(x.get("amount")) for x in fin if x.get("supplier_id")==s.get("id") and x.get("direction")=="Egreso" and x.get("status")=="Pendiente" and not x.get("voided"))
                rows.append({"Proveedor":s.get("name"),"Rubro":s.get("category"),"Contacto":s.get("contact"),"WhatsApp":s.get("whatsapp"),"Plazo días":s.get("payment_terms_days"),"Límite crédito":s.get("credit_limit"),"Cuenta pendiente":pending,"Activo":s.get("active",True)})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={"Límite crédito":st.column_config.NumberColumn(format="$ %.0f"),"Cuenta pendiente":st.column_config.NumberColumn(format="$ %.0f")})
        else: empty_state("Sin proveedores","Creá pinturerías, repuesteros y tercerizados para controlar compras y cuentas.")
    with tabs[1]:
        with st.form("new_supplier",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            name=c1.text_input("Proveedor *"); category=c2.selectbox("Rubro",["Pinturería","Repuestos","Tercerización","Herramientas","Servicios","Otro"]); contact=c3.text_input("Contacto")
            c1,c2,c3=st.columns(3)
            whatsapp=c1.text_input("WhatsApp"); terms=c2.number_input("Plazo habitual (días)",min_value=0,step=1); limit_=c3.number_input("Límite de crédito",min_value=0.0,step=50000.0)
            notes=st.text_area("Condiciones / descuentos / observaciones")
            ok=st.form_submit_button("Crear proveedor",type="primary",width="stretch")
        if ok:
            if not name.strip(): st.error("El nombre es obligatorio.")
            else:
                store.insert("suppliers",{"name":name.strip(),"category":category,"contact":contact.strip(),"whatsapp":whatsapp.strip(),"payment_terms_days":terms,"credit_limit":limit_,"notes":notes.strip(),"active":True},actor,f"Creó proveedor {name.strip()}"); st.rerun()
    with tabs[2]:
        if suppliers:
            sel=st.selectbox("Proveedor",suppliers,format_func=lambda s:s.get("name"))
            rows=[x for x in fin if x.get("supplier_id")==sel.get("id") and not x.get("voided")]
            pending=sum(as_float(x.get("amount")) for x in rows if x.get("status")=="Pendiente" and x.get("direction")=="Egreso")
            paid=sum(as_float(x.get("amount")) for x in rows if x.get("status")=="Pagado" and x.get("direction")=="Egreso")
            a,b,c=st.columns(3); a.metric("Pendiente",money(pending)); b.metric("Pagado histórico",money(paid)); c.metric("Crédito disponible",money(max(0,as_float(sel.get("credit_limit"))-pending)) if as_float(sel.get("credit_limit")) else "Sin límite")
            if rows: st.dataframe(pd.DataFrame(rows)[[c for c in ["movement_date","category","amount","status","due_date","notes"] if c in pd.DataFrame(rows).columns]],hide_index=True,width="stretch",column_config={"amount":st.column_config.NumberColumn(format="$ %.0f")})
        else: empty_state("Sin proveedores","No hay cuentas corrientes para mostrar.")
    with tabs[3]:
        if suppliers and mm:
            rows=[]
            for s in suppliers:
                purchases=[x for x in mm if x.get("supplier_id")==s.get("id") and x.get("move_type")=="Compra"]
                total=sum(as_float(x.get("qty"))*as_float(x.get("unit_cost")) for x in purchases)
                rows.append({"Proveedor":s.get("name"),"Compras":len(purchases),"Monto":total})
            df=pd.DataFrame(rows).sort_values("Monto",ascending=False)
            st.dataframe(df,hide_index=True,width="stretch",column_config={"Monto":st.column_config.NumberColumn(format="$ %.0f")})
            if df["Monto"].sum()>0:
                df["Participación %"]=df["Monto"]/df["Monto"].sum()*100
                st.bar_chart(df.set_index("Proveedor")["Monto"])
        else: empty_state("Sin compras suficientes","A medida que registres compras se verá concentración y volumen por proveedor.")

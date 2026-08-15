from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from core import MATERIAL_MOVE_TYPES, as_float, money
from domain import current_stock, actual_material_cost
from theme import page_title
from ui import empty_state


def render(store, actor, settings):
    page_title("Materiales & stock", "Compra, stock, consumo por OT, costo real y aprendizaje progresivo de cuánto consume cada tipo de trabajo.")
    catalog=store.list("material_catalog")
    moves=store.list("material_moves")
    suppliers=store.list("suppliers")
    ots=store.list("work_orders")
    tabs=st.tabs(["Stock","Nuevo material","Registrar movimiento","Consumo por OT","Compras & aprendizaje"])

    with tabs[0]:
        if catalog:
            rows=[]
            for m in catalog:
                stock=current_stock(m["id"],moves); minimum=as_float(m.get("min_stock")); last_cost=as_float(m.get("last_unit_cost"))
                rows.append({"Material":m.get("name"),"Categoría":m.get("category"),"Unidad":m.get("unit"),"Stock":stock,"Mínimo":minimum,"Estado":"REPOSICIÓN" if minimum>0 and stock<=minimum else "OK","Últ. costo unit.":last_cost,"Valor stock":stock*last_cost})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={"Últ. costo unit.":st.column_config.NumberColumn(format="$ %.0f"),"Valor stock":st.column_config.NumberColumn(format="$ %.0f")})
            total=sum(current_stock(m["id"],moves)*as_float(m.get("last_unit_cost")) for m in catalog)
            low=sum(1 for m in catalog if as_float(m.get("min_stock"))>0 and current_stock(m["id"],moves)<=as_float(m.get("min_stock")))
            a,b=st.columns(2); a.metric("Valor estimado de stock",money(total)); b.metric("Ítems en reposición",low)
        else: empty_state("Catálogo vacío","Creá materiales antes de registrar compras o consumos.")

    with tabs[1]:
        with st.form("new_material",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            name=c1.text_input("Material *",placeholder="Primer / Masilla / Lija P400")
            category=c2.selectbox("Categoría",["Pintura","Preparación","Abrasivos","Consumibles","Protección","Soldadura","Limpieza","Otro"])
            unit=c3.selectbox("Unidad",["u","kg","g","L","ml","m","m²","rollo","kit"])
            c1,c2,c3=st.columns(3)
            min_stock=c1.number_input("Stock mínimo",min_value=0.0,step=.5)
            sku=c2.text_input("Código / SKU")
            notes=c3.text_input("Marca / detalle")
            ok=st.form_submit_button("Crear material",type="primary",width="stretch")
        if ok:
            if not name.strip(): st.error("El nombre es obligatorio.")
            else:
                store.insert("material_catalog",{"name":name.strip(),"category":category,"unit":unit,"min_stock":min_stock,"sku":sku.strip(),"notes":notes.strip(),"last_unit_cost":0.0,"active":True},actor,f"Creó material {name.strip()}"); st.success("Material creado."); st.rerun()

    with tabs[2]:
        if not catalog: empty_state("Primero creá un material","El movimiento necesita un artículo del catálogo.")
        else:
            with st.form("material_move",clear_on_submit=True):
                c1,c2,c3=st.columns(3)
                mat=c1.selectbox("Material",catalog,format_func=lambda m:f"{m.get('name')} · {current_stock(m['id'],moves):g} {m.get('unit')}")
                typ=c2.selectbox("Movimiento",MATERIAL_MOVE_TYPES)
                qty=c3.number_input("Cantidad",min_value=0.0,step=.1)
                c1,c2,c3=st.columns(3)
                unit_cost=c1.number_input("Costo unitario $",min_value=0.0,value=as_float(mat.get("last_unit_cost")),step=100.0)
                supplier=c2.selectbox("Proveedor",[None]+suppliers,format_func=lambda x:"—" if x is None else x.get("name"))
                active_ots=[o for o in ots if o.get("stage")!="Entregado" and not o.get("cancelled")]
                ot=c3.selectbox("Imputar a OT",[None]+active_ots,format_func=lambda x:"— Sin OT —" if x is None else f"#{int(x.get('number',0)):05d} · {x.get('plate')}")
                notes=st.text_input("Concepto / observación")
                ok=st.form_submit_button("Registrar movimiento",type="primary",width="stretch")
            if ok:
                if qty<=0: st.error("La cantidad debe ser mayor a cero.")
                elif typ=="Consumo" and current_stock(mat["id"],moves)<qty:
                    st.error("Stock insuficiente. Registrá la compra o un ajuste antes de consumir.")
                else:
                    store.insert("material_moves",{"movement_date":date.today().isoformat(),"material_id":mat["id"],"move_type":typ,"qty":qty,"unit_cost":unit_cost,"supplier_id":supplier.get("id") if supplier else None,"work_order_id":ot.get("id") if ot else None,"notes":notes.strip()},actor,f"{typ} {qty:g} {mat.get('unit')} de {mat.get('name')}")
                    if typ=="Compra" and unit_cost>0: store.update("material_catalog",mat["id"],{"last_unit_cost":unit_cost},actor,f"Actualizó costo de {mat.get('name')} a {money(unit_cost)}")
                    if typ=="Compra" and supplier:
                        total=qty*unit_cost
                        store.insert("financial_moves",{"movement_date":date.today().isoformat(),"direction":"Egreso","category":"Materiales","account":"Caja","amount":total,"status":"Pendiente","due_date":date.today().isoformat(),"paid_date":None,"counterparty":supplier.get("name"),"supplier_id":supplier.get("id"),"work_order_id":ot.get("id") if ot else None,"notes":f"Compra {mat.get('name')}","voided":False},actor,f"Generó cuenta por pagar a {supplier.get('name')} por compra de materiales")
                    st.success("Movimiento registrado."); st.rerun()

    with tabs[3]:
        if not ots: empty_state("Sin OT","Los consumos se agrupan automáticamente por trabajo.")
        else:
            rows=[]
            for o in ots:
                cost=actual_material_cost(o.get("id"),moves); count=sum(1 for x in moves if x.get("work_order_id")==o.get("id") and x.get("move_type")=="Consumo")
                estimated=as_float(o.get("estimated_material_cost"))
                if count or o.get("stage")!="Entregado": rows.append({"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Vehículo":o.get("car"),"Consumos":count,"Materiales estimados":estimated,"Costo materiales real":cost,"Desvío materiales":cost-estimated if estimated else 0.0,"Monto trabajo":o.get("agreed_amount",0),"Materiales / venta %":cost/as_float(o.get("agreed_amount"))*100 if as_float(o.get("agreed_amount")) else 0})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={"Materiales estimados":st.column_config.NumberColumn(format="$ %.0f"),"Costo materiales real":st.column_config.NumberColumn(format="$ %.0f"),"Desvío materiales":st.column_config.NumberColumn(format="$ %.0f"),"Monto trabajo":st.column_config.NumberColumn(format="$ %.0f"),"Materiales / venta %":st.column_config.NumberColumn(format="%.1f%%")})

    with tabs[4]:
        purchases=[x for x in moves if x.get("move_type")=="Compra"]
        if purchases:
            mat_map={m["id"]:m for m in catalog}; sup_map={s["id"]:s for s in suppliers}
            rows=[]
            for x in purchases:
                rows.append({"Fecha":x.get("movement_date"),"Material":mat_map.get(x.get("material_id"),{}).get("name"),"Proveedor":sup_map.get(x.get("supplier_id"),{}).get("name"),"Cantidad":x.get("qty"),"Costo unit.":x.get("unit_cost"),"Total":as_float(x.get("qty"))*as_float(x.get("unit_cost"))})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={"Costo unit.":st.column_config.NumberColumn(format="$ %.0f"),"Total":st.column_config.NumberColumn(format="$ %.0f")})
        else: empty_state("Sin compras registradas","El historial va a permitir comparar proveedores y evolución de costos.")

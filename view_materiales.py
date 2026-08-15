from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from theme import page_title
from utils import money


def render(repo, user, settings):
    page_title("Materiales", "Compras, stock, consumo por trabajo y diferencia entre lo estimado y lo real.")
    materials = repo.list_rows("materials")
    moves = repo.list_rows("material_movements")
    ots = repo.list_rows("work_orders")
    tabs = st.tabs(["Stock", "Registrar movimiento", "Consumo por OT", "Aprendizaje"])

    with tabs[0]:
        if materials:
            df = pd.DataFrame(materials)
            df["alerta"] = df.apply(lambda r: "REPOSICIÓN" if float(r.get("stock") or 0) <= float(r.get("min_stock") or 0) else "OK", axis=1)
            st.dataframe(df[[c for c in ["name","stock","unit","min_stock","avg_unit_cost","supplier","alerta"] if c in df.columns]], use_container_width=True, hide_index=True,
                         column_config={"avg_unit_cost":st.column_config.NumberColumn("Costo prom.", format="$ %.0f")})
        else:
            st.info("Cargá los materiales críticos para empezar a aprender consumos.")

    with tabs[1]:
        with st.form("mat_move", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            kind = c1.selectbox("Tipo", ["Compra","Consumo","Ajuste +","Ajuste -"])
            material = c2.text_input("Material *")
            supplier = c3.text_input("Proveedor")
            c1,c2,c3 = st.columns(3)
            qty = c1.number_input("Cantidad", min_value=0.0, step=.1)
            unit = c2.selectbox("Unidad", ["u","kg","g","L","ml","m","pack"])
            amount = c3.number_input("Monto total", min_value=0.0, step=1000.0)
            ot_labels = ["— Sin OT —"] + [f'#{int(o.get("number",0)):05d} · {o.get("plate")}' for o in ots if o.get("stage") != "Entregado"]
            ot_sel = st.selectbox("Trabajo relacionado", ot_labels)
            estimated = st.number_input("Consumo estimado $", min_value=0.0, step=1000.0)
            notes = st.text_area("Notas")
            ok = st.form_submit_button("Registrar movimiento", type="primary", use_container_width=True)
        if ok:
            if not material.strip() or qty <= 0:
                st.error("Indicá material y cantidad.")
            else:
                ot_id = ""
                if ot_sel != "— Sin OT —":
                    idx=ot_labels.index(ot_sel)-1
                    active=[o for o in ots if o.get("stage") != "Entregado"]
                    ot_id=active[idx]["id"]
                repo.insert("material_movements", {"movement_date":date.today().isoformat(),"type":kind,"material":material.strip(),"supplier":supplier.strip(),
                    "quantity":qty,"unit":unit,"amount":amount,"work_order_id":ot_id,"estimated_consumption":estimated,"actual_consumption":amount if kind=="Consumo" else 0,"notes":notes.strip()},
                    user, f"Registró {kind.lower()} de {material.strip()} · {money(amount)}")
                # Crea/actualiza stock resumido.
                existing = next((m for m in materials if str(m.get("name","")).lower()==material.strip().lower()), None)
                delta = qty if kind in {"Compra","Ajuste +"} else -qty
                if existing:
                    new_stock=max(0,float(existing.get("stock") or 0)+delta)
                    payload={"stock":new_stock,"unit":unit}
                    if kind=="Compra" and qty:
                        payload["avg_unit_cost"]=amount/qty
                        payload["supplier"]=supplier.strip()
                    repo.update("materials", existing["id"], payload, user, f"Actualizó stock {material.strip()} a {new_stock:g} {unit}")
                else:
                    repo.insert("materials", {"name":material.strip(),"stock":max(0,delta),"unit":unit,"min_stock":0,"avg_unit_cost": amount/qty if kind=="Compra" and qty else 0,"supplier":supplier.strip()}, user, f"Creó material {material.strip()}")
                if kind=="Consumo" and ot_id and amount:
                    ot = next((o for o in ots if str(o.get("id")) == str(ot_id)), None)
                    if ot:
                        repo.update("work_orders", ot_id, {"actual_material_cost": float(ot.get("actual_material_cost") or 0) + amount}, user, f"Sumó consumo real de materiales a OT #{int(ot.get('number',0)):05d}")
                if kind=="Compra" and amount:
                    repo.insert("financial_movements", {"movement_date":date.today().isoformat(),"direction":"Egreso","type":"Compra material","account":"Caja","category":"Pinturería",
                        "amount":amount,"status":"Pendiente","due_date":None,"paid_date":None,"counterparty":supplier.strip(),"work_order_id":ot_id,"notes":material.strip()}, user, f"Cargó compra de materiales {money(amount)}")
                st.success("Movimiento registrado.")
                st.rerun()

    with tabs[2]:
        cons=[m for m in moves if m.get("type")=="Consumo"]
        if cons:
            df=pd.DataFrame(cons)
            df["diferencia"] = pd.to_numeric(df.get("actual_consumption",0),errors="coerce").fillna(0)-pd.to_numeric(df.get("estimated_consumption",0),errors="coerce").fillna(0)
            st.dataframe(df[[c for c in ["movement_date","material","work_order_id","estimated_consumption","actual_consumption","diferencia","notes"] if c in df.columns]],use_container_width=True,hide_index=True,
                         column_config={"estimated_consumption":st.column_config.NumberColumn("Estimado",format="$ %.0f"),"actual_consumption":st.column_config.NumberColumn("Real",format="$ %.0f"),"diferencia":st.column_config.NumberColumn("Diferencia",format="$ %.0f")})
        else:
            st.info("Cuando registres consumos por OT, acá vas a ver dónde se escapa material.")

    with tabs[3]:
        cons=[m for m in moves if m.get("type")=="Consumo" and float(m.get("actual_consumption") or 0)>0]
        if cons:
            df=pd.DataFrame(cons)
            grp=df.groupby("material",as_index=False).agg(trabajos=("id","count"),consumo_promedio=("actual_consumption","mean"),consumo_total=("actual_consumption","sum"))
            st.dataframe(grp,use_container_width=True,hide_index=True,column_config={"consumo_promedio":st.column_config.NumberColumn("Promedio/trabajo",format="$ %.0f"),"consumo_total":st.column_config.NumberColumn("Total",format="$ %.0f")})
            st.caption("Esta base es la que progresivamente puede alimentar el costo automático del cotizador.")
        else:
            st.info("Todavía no hay muestra suficiente para aprender consumos.")

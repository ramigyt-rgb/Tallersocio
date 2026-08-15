from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from theme import page_title
from metrics import PRODUCTION_STAGES
from utils import money, normalize_plate


def render(repo, user, settings):
    page_title("Órdenes de trabajo", "Ingreso formal del vehículo, alcance acordado, anticipo, daños preexistentes y trazabilidad.")
    rows = repo.list_rows("work_orders")
    tabs = st.tabs(["OT activas", "Nueva OT", "Ficha / actualización"])

    with tabs[0]:
        active = [r for r in rows if not r.get("archived") and r.get("stage") != "Entregado"]
        if active:
            df = pd.DataFrame(active)
            keep = [c for c in ["number","plate","car","customer_name","stage","appointment_date","promised_date","agreed_amount","advance","paid_amount"] if c in df.columns]
            st.dataframe(df[keep], use_container_width=True, hide_index=True, column_config={
                "agreed_amount":st.column_config.NumberColumn("Monto", format="$ %.0f"),
                "advance":st.column_config.NumberColumn("Anticipo", format="$ %.0f"),
                "paid_amount":st.column_config.NumberColumn("Cobrado", format="$ %.0f"),
            })
        else:
            st.info("No hay OTs activas.")

    with tabs[1]:
        with st.form("new_ot", clear_on_submit=True):
            c1,c2,c3 = st.columns(3)
            customer = c1.text_input("Cliente *")
            whatsapp = c2.text_input("WhatsApp")
            plate = c3.text_input("Patente *")
            c1,c2 = st.columns(2)
            car = c1.text_input("Auto / versión *")
            km = c2.number_input("Kilometraje", min_value=0, step=100)
            c1,c2,c3 = st.columns(3)
            fuel = c1.selectbox("Combustible", ["Reserva","1/4","1/2","3/4","Lleno"])
            appointment = c2.date_input("Fecha ingreso / turno", value=date.today())
            promised = c3.date_input("Fecha prometida", value=date.today())
            scope = st.text_area("Qué se va a hacer *")
            excluded = st.text_area("Qué NO se va a hacer")
            preexisting = st.text_area("Daños preexistentes")
            c1,c2,c3 = st.columns(3)
            amount = c1.number_input("Monto acordado", min_value=0.0, step=10000.0)
            advance = c2.number_input("Anticipo", min_value=0.0, step=10000.0)
            stage = c3.selectbox("Estado inicial", ["Esperando","Desarme","Chapa"])
            photos = st.file_uploader("Fotos de ingreso", type=["jpg","jpeg","png","webp"], accept_multiple_files=True)
            accepted = st.checkbox("Cliente acepta alcance, exclusiones y estado de ingreso")
            notes = st.text_area("Observaciones")
            ok = st.form_submit_button("Crear orden de trabajo", type="primary", use_container_width=True)
        if ok:
            if not all([customer.strip(), plate.strip(), car.strip(), scope.strip()]) or not accepted:
                st.error("Completá cliente, patente, auto, alcance y aceptación.")
            else:
                n = repo.next_number("work_orders", start=1)
                paths = repo.upload_files(photos, f"work_orders/{n:05d}") if photos else []
                created_ot = repo.insert("work_orders", {
                    "number":n,"customer_name":customer.strip(),"whatsapp":whatsapp.strip(),"car":car.strip(),"plate":normalize_plate(plate),
                    "km":km,"fuel":fuel,"stage":stage,"appointment_date":appointment.isoformat(),"promised_date":promised.isoformat(),"delivery_date":None,
                    "agreed_amount":amount,"advance":advance,"paid_amount":advance,"actual_material_cost":0,"parts_cost":0,"outsourcing_cost":0,
                    "scope":scope.strip(),"excluded_scope":excluded.strip(),"preexisting_damage":preexisting.strip(),"photos":paths,"notes":notes.strip(),"archived":False,
                }, user, f"Creó OT #{n:05d} · {normalize_plate(plate)} · {money(amount)}")
                if advance:
                    repo.insert("financial_movements", {
                        "movement_date":date.today().isoformat(),"direction":"Ingreso","type":"Anticipo cliente","account":"Caja","category":"Cobros",
                        "amount":advance,"status":"Pagado","due_date":None,"paid_date":date.today().isoformat(),"counterparty":customer.strip(),"work_order_id":created_ot.get("id"),"notes":f"Anticipo OT #{n:05d}",
                    }, user, f"Registró anticipo {money(advance)} de OT #{n:05d}")
                st.success(f"OT #{n:05d} creada.")
                st.rerun()

    with tabs[2]:
        if not rows:
            st.info("No hay OTs para consultar.")
            return
        labels = {f'#{int(r.get("number",0)):05d} · {r.get("plate")} · {r.get("car")}': r for r in rows if not r.get("archived")}
        chosen = st.selectbox("Orden", list(labels.keys()))
        ot = labels[chosen]
        a,b,c,d = st.columns(4)
        a.metric("Monto", money(ot.get("agreed_amount")))
        b.metric("Cobrado", money(ot.get("paid_amount")))
        c.metric("Saldo", money(float(ot.get("agreed_amount") or 0)-float(ot.get("paid_amount") or 0)))
        d.metric("Etapa", ot.get("stage","—"))
        st.write(f'**Alcance:** {ot.get("scope") or "—"}')
        st.write(f'**No incluido:** {ot.get("excluded_scope") or "—"}')
        st.write(f'**Daños preexistentes:** {ot.get("preexisting_damage") or "—"}')
        c1,c2,c3 = st.columns(3)
        new_stage = c1.selectbox("Etapa", PRODUCTION_STAGES, index=PRODUCTION_STAGES.index(ot.get("stage")) if ot.get("stage") in PRODUCTION_STAGES else 0)
        promised = c2.date_input("Fecha prometida", value=pd.to_datetime(ot.get("promised_date")).date() if ot.get("promised_date") else date.today())
        paid = c3.number_input("Total cobrado acumulado", min_value=0.0, value=float(ot.get("paid_amount") or 0), step=10000.0)
        notes = st.text_area("Observaciones", value=ot.get("notes") or "")
        if st.button("Guardar cambios", type="primary"):
            payload={"stage":new_stage,"promised_date":promised.isoformat(),"paid_amount":paid,"notes":notes}
            if new_stage=="Entregado" and not ot.get("delivery_date"):
                payload["delivery_date"]=date.today().isoformat()
            repo.update("work_orders", ot["id"], payload, user, f"Actualizó OT #{int(ot.get('number',0)):05d} · etapa {new_stage}")
            st.success("OT actualizada.")
            st.rerun()

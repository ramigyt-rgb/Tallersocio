from __future__ import annotations

import pandas as pd
import streamlit as st

from theme import page_title
from metrics import quote_totals
from utils import money, normalize_plate, as_float


BASE_ROWS = pd.DataFrame([
    {"pieza":"Paragolpes","tipo_dano":"Rayón / golpe leve","horas_chapa":2.0,"horas_preparacion":1.5,"panos":1.0,"horas_armado":1.0,"materiales":0.0,"repuestos":0.0,"tercerizaciones":0.0,"dificultad":"Media"}
])


def render(repo, user, settings):
    page_title("Cotizador", "El precio sale de una estructura: costo, piso, objetivo y precio ofrecido.")
    leads = [r for r in repo.list_rows("leads") if r.get("status") not in {"Ganado","Perdido"}]
    tabs = st.tabs(["Nueva cotización", "Historial"])

    with tabs[0]:
        c1,c2 = st.columns([1.1,2])
        with c1:
            if leads:
                choices = ["— Manual —"] + [f'{r.get("name")} · {r.get("plate") or r.get("car")}' for r in leads]
                sel = st.selectbox("Origen", choices)
                lead = None if sel == "— Manual —" else leads[choices.index(sel)-1]
            else:
                lead = None
            customer = st.text_input("Cliente", value=(lead or {}).get("name", ""))
            car = st.text_input("Auto", value=(lead or {}).get("car", ""))
            plate = st.text_input("Patente", value=(lead or {}).get("plate", ""))
            st.caption("Las tarifas internas se cambian desde Configuración, no en cada presupuesto.")
        with c2:
            st.markdown("#### Despiece técnico")
            edited = st.data_editor(
                BASE_ROWS,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "pieza": st.column_config.TextColumn("Pieza afectada"),
                    "tipo_dano": st.column_config.TextColumn("Tipo de daño"),
                    "horas_chapa": st.column_config.NumberColumn("Hs chapa", min_value=0.0, step=.5),
                    "horas_preparacion": st.column_config.NumberColumn("Hs prep.", min_value=0.0, step=.5),
                    "panos": st.column_config.NumberColumn("Paños", min_value=0.0, step=.5),
                    "horas_armado": st.column_config.NumberColumn("Hs D/A", min_value=0.0, step=.5),
                    "materiales": st.column_config.NumberColumn("Materiales $", min_value=0.0, step=1000.0),
                    "repuestos": st.column_config.NumberColumn("Repuestos $", min_value=0.0, step=1000.0),
                    "tercerizaciones": st.column_config.NumberColumn("Terceros $", min_value=0.0, step=1000.0),
                    "dificultad": st.column_config.SelectboxColumn("Dificultad", options=["Baja","Media","Alta","Muy alta"]),
                }, key="quote_editor"
            )

        totals = quote_totals(edited, settings)
        a,b,c,d = st.columns(4)
        a.metric("Costo estimado", money(totals["estimated_cost"]))
        b.metric("Precio piso", money(totals["floor"]))
        c.metric("Precio objetivo", money(totals["target"]))
        d.metric("Días estimados", totals["days"])
        offered = st.number_input("Precio ofrecido al cliente", min_value=0.0, value=float(round(totals["target"] / 1000) * 1000), step=10000.0)
        margin = (offered - totals["estimated_cost"]) / offered if offered else 0
        if offered < totals["floor"]:
            st.error(f"Precio debajo del piso. Margen estimado: {margin*100:.1f}%")
        elif offered < totals["target"]:
            st.warning(f"Precio viable, pero debajo del objetivo. Margen estimado: {margin*100:.1f}%")
        else:
            st.success(f"Precio en zona objetivo. Margen estimado: {margin*100:.1f}%")
        notes = st.text_area("Notas / condiciones")
        if st.button("Guardar cotización", type="primary", use_container_width=True):
            if not customer.strip():
                st.error("Indicá el cliente.")
            else:
                number = repo.next_number("quotes", start=1)
                row = repo.insert("quotes", {
                    "number": number, "lead_id": (lead or {}).get("id"), "customer_name": customer.strip(),
                    "car": car.strip(), "plate": normalize_plate(plate), "status":"Enviada",
                    "estimated_cost": totals["estimated_cost"], "floor_price":totals["floor"],
                    "target_price":totals["target"], "offered_price":offered, "estimated_days":totals["days"],
                    "items": edited.fillna(0).to_dict(orient="records"), "notes":notes.strip(),
                }, user, f"Creó cotización #{number:05d} · {customer.strip()} · {money(offered)}")
                if lead:
                    repo.update("leads", lead["id"], {"status":"Cotizado"}, user, f"Lead {lead.get('name')} pasó a Cotizado")
                st.success(f"Cotización #{number:05d} guardada.")
                st.rerun()

    with tabs[1]:
        quotes = repo.list_rows("quotes")
        if quotes:
            df = pd.DataFrame(quotes)
            keep = [c for c in ["number","customer_name","car","plate","status","estimated_cost","floor_price","target_price","offered_price","estimated_days","created_at"] if c in df.columns]
            st.dataframe(df[keep], use_container_width=True, hide_index=True, column_config={
                "estimated_cost":st.column_config.NumberColumn("Costo",format="$ %.0f"),
                "floor_price":st.column_config.NumberColumn("Piso",format="$ %.0f"),
                "target_price":st.column_config.NumberColumn("Objetivo",format="$ %.0f"),
                "offered_price":st.column_config.NumberColumn("Ofrecido",format="$ %.0f"),
            })
            candidates = [q for q in quotes if q.get("status") in {"Enviada","Seguimiento","Aprobada"}]
            if candidates:
                st.markdown("#### Aprobar y convertir en trabajo")
                labels = {f'#{int(q.get("number",0)):05d} · {q.get("customer_name")} · {money(q.get("offered_price"))}':q for q in candidates}
                chosen = st.selectbox("Cotización", list(labels.keys()), key="approve_quote")
                q = labels[chosen]
                c1,c2 = st.columns(2)
                appointment = c1.date_input("Turno")
                promised = c2.date_input("Fecha prometida")
                if st.button("Aprobar y crear OT", type="primary"):
                    n = repo.next_number("work_orders", start=1)
                    repo.insert("work_orders", {
                        "number":n,"customer_name":q.get("customer_name"),"whatsapp":"","car":q.get("car"),"plate":q.get("plate"),
                        "km":0,"fuel":"","stage":"Esperando","appointment_date":appointment.isoformat(),"promised_date":promised.isoformat(),
                        "delivery_date":None,"agreed_amount":q.get("offered_price",0),"advance":0,"paid_amount":0,"actual_material_cost":0,
                        "parts_cost":0,"outsourcing_cost":0,"scope":"Según cotización aprobada","excluded_scope":"","preexisting_damage":"",
                        "photos":[],"notes":f'Cotización #{int(q.get("number",0)):05d}',"archived":False,
                    }, user, f"Creó OT #{n:05d} desde cotización #{int(q.get('number',0)):05d}")
                    repo.update("quotes", q["id"], {"status":"Aprobada"}, user, f"Aprobó cotización #{int(q.get('number',0)):05d}")
                    if q.get("lead_id"):
                        repo.update("leads", q["lead_id"], {"status":"Ganado"}, user, "Lead convertido en trabajo")
                    st.success(f"OT #{n:05d} creada.")
                    st.rerun()
        else:
            st.info("Todavía no hay cotizaciones.")

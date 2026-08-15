from __future__ import annotations

import pandas as pd
import streamlit as st

from theme import page_title
from utils import normalize_plate


STATUSES = ["Nuevo", "Contactado", "Cotizado", "Seguimiento", "Ganado", "Perdido"]
LOST = ["", "Precio", "Demora", "No respondió", "Otro taller", "No arregla", "Otro"]
SOURCES = ["Instagram", "Google", "Tarjeta / QR", "Referido", "WhatsApp", "Aseguradora", "Otro"]


def render(repo, user, settings):
    page_title("Captación", "Cada consulta entra al sistema y deja aprendizaje, incluso cuando se pierde.")
    tabs = st.tabs(["Pipeline", "Nuevo lead", "Seguimiento y pérdidas"])
    rows = repo.list_rows("leads")

    with tabs[0]:
        counts = {s: sum(1 for r in rows if r.get("status") == s) for s in STATUSES}
        cols = st.columns(6)
        for c,s in zip(cols, STATUSES):
            c.metric(s, counts[s])
        if rows:
            df = pd.DataFrame(rows)
            keep = [c for c in ["name","whatsapp","car","plate","damage","source","need_visit","status","lost_reason","created_at"] if c in df.columns]
            st.dataframe(df[keep], use_container_width=True, hide_index=True)
        else:
            st.info("Todavía no hay leads.")

    with tabs[1]:
        with st.form("new_lead", clear_on_submit=True):
            c1,c2 = st.columns(2)
            name = c1.text_input("Nombre *")
            whatsapp = c2.text_input("WhatsApp *")
            c1,c2 = st.columns(2)
            car = c1.text_input("Auto / versión")
            plate = c2.text_input("Patente")
            damage = st.text_area("Daño / consulta *", height=90)
            c1,c2,c3 = st.columns(3)
            source = c1.selectbox("Cómo nos conoció", SOURCES)
            need_visit = c2.toggle("¿Hay que ir a verlo?")
            status = c3.selectbox("Estado inicial", STATUSES[:3])
            photos = st.file_uploader("Fotos", type=["jpg","jpeg","png","webp"], accept_multiple_files=True)
            notes = st.text_area("Observaciones")
            ok = st.form_submit_button("Crear lead", type="primary", use_container_width=True)
        if ok:
            if not name.strip() or not whatsapp.strip() or not damage.strip():
                st.error("Completá nombre, WhatsApp y daño.")
            else:
                paths = repo.upload_files(photos, "leads") if photos else []
                repo.insert("leads", {
                    "name": name.strip(), "whatsapp": whatsapp.strip(), "car": car.strip(),
                    "plate": normalize_plate(plate), "damage": damage.strip(), "source": source,
                    "need_visit": need_visit, "status": status, "lost_reason": "", "notes": notes.strip(),
                    "photos": paths,
                }, user, f"Creó lead {name.strip()} · {car.strip() or 'sin vehículo'}")
                st.success("Lead creado.")
                st.rerun()

    with tabs[2]:
        active = [r for r in rows if r.get("status") not in {"Ganado", "Perdido"}]
        if active:
            labels = {f'{r.get("name")} · {r.get("plate") or r.get("car")}': r for r in active}
            chosen = st.selectbox("Lead a actualizar", list(labels.keys()))
            lead = labels[chosen]
            c1,c2 = st.columns(2)
            status = c1.selectbox("Nuevo estado", STATUSES, index=STATUSES.index(lead.get("status")) if lead.get("status") in STATUSES else 0)
            lost = c2.selectbox("Motivo de pérdida", LOST, disabled=status != "Perdido")
            notes = st.text_area("Nota de seguimiento", value=lead.get("notes") or "")
            if st.button("Guardar seguimiento", type="primary"):
                if status == "Perdido" and not lost:
                    st.error("Indicá por qué se perdió.")
                else:
                    repo.update("leads", lead["id"], {"status":status,"lost_reason":lost,"notes":notes}, user, f"Actualizó lead {lead.get('name')} a {status}")
                    st.success("Seguimiento guardado.")
                    st.rerun()
        else:
            st.info("No hay leads abiertos para seguimiento.")

        lost_rows = [r for r in rows if r.get("status") == "Perdido"]
        if lost_rows:
            st.markdown("#### Por qué estamos perdiendo trabajos")
            s = pd.Series([r.get("lost_reason") or "Sin motivo" for r in lost_rows]).value_counts().rename_axis("Motivo").reset_index(name="Cantidad")
            st.dataframe(s, use_container_width=True, hide_index=True)

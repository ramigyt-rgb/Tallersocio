from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from core import LEAD_SOURCES, LEAD_STATES, LOSS_REASONS, encode_uploads, normalize_plate, parse_date
from domain import pipeline_metrics
from theme import page_title, flow_strip
from ui import empty_state


def _lead_label(x):
    return f"{x.get('name','Sin nombre')} · {x.get('plate') or 'sin patente'} · {x.get('status','Nuevo')}"


def render(store, actor, settings):
    page_title("Captación & CRM", "Cada consulta entra, se sigue, se cotiza y deja aprendizaje aunque se pierda.")
    flow_strip("LEAD")
    leads = store.list("leads")
    quotes = store.list("quotes")
    m = pipeline_metrics(leads, quotes)

    a,b,c,d,e = st.columns(5)
    a.metric("Leads", m["total"])
    b.metric("Abiertos", sum(1 for x in leads if x.get("status") not in ("Ganado","Perdido")))
    c.metric("Ganados", m["won"])
    d.metric("Perdidos", m["lost"])
    e.metric("Conversión", f"{m['win_rate']*100:.1f}%")

    tabs = st.tabs(["Pipeline", "Nuevo lead", "Ficha & seguimiento", "Análisis de captación"])
    with tabs[0]:
        if not leads:
            empty_state("Todavía no hay consultas", "El primer lead que cargues aparece acá y alimenta todo el embudo.")
        else:
            cols = st.columns(6)
            for col, status in zip(cols, LEAD_STATES):
                with col:
                    subset=[x for x in leads if x.get("status")==status]
                    st.markdown(f"#### {status} · {len(subset)}")
                    for x in subset[:15]:
                        st.markdown(f'''<div class="tos-stage"><div class="plate">{x.get('plate') or 'SIN PATENTE'}</div><div class="meta">{x.get('name')} · {x.get('car') or '—'}</div><div><span class="tos-pill">{x.get('source') or 'Sin fuente'}</span>{'<span class="tos-pill warn">IR A VER</span>' if x.get('needs_visit') else ''}</div><div class="meta">{x.get('damage') or 'Sin detalle'}</div></div>''',unsafe_allow_html=True)

    with tabs[1]:
        with st.form("new_lead", clear_on_submit=True):
            c1,c2,c3,c4=st.columns(4)
            name=c1.text_input("Nombre *")
            whatsapp=c2.text_input("WhatsApp")
            car=c3.text_input("Auto / modelo")
            plate=c4.text_input("Patente")
            c1,c2,c3=st.columns(3)
            source=c1.selectbox("Cómo nos conoció",LEAD_SOURCES)
            needs_visit=c2.checkbox("¿Hay que ir a verlo?")
            next_followup=c3.date_input("Próximo seguimiento", value=date.today()+timedelta(days=1))
            damage=st.text_area("Daño / consulta *", placeholder="Describí lo que se ve, piezas afectadas y cualquier detalle comercial relevante.")
            notes=st.text_area("Observaciones internas")
            photos=st.file_uploader("Fotos",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key="lead_photos")
            submitted=st.form_submit_button("Crear lead",type="primary",width="stretch")
        if submitted:
            if not name.strip() or not damage.strip():
                st.error("Nombre y daño/consulta son obligatorios.")
            else:
                store.insert("leads",{
                    "name":name.strip(),"whatsapp":whatsapp.strip(),"car":car.strip(),"plate":normalize_plate(plate),"source":source,
                    "needs_visit":needs_visit,"damage":damage.strip(),"notes":notes.strip(),"status":"Nuevo","loss_reason":None,
                    "next_followup":next_followup.isoformat(),"photos":encode_uploads(photos)
                },actor,f"Creó lead {name.strip()} · {normalize_plate(plate) or 'sin patente'}")
                st.success("Lead creado.")
                st.rerun()

    with tabs[2]:
        if not leads:
            empty_state("Sin leads para editar", "Creá una consulta primero.")
        else:
            selected=st.selectbox("Lead",leads,format_func=_lead_label)
            current=selected.get("status","Nuevo")
            c1,c2,c3=st.columns(3)
            status=c1.selectbox("Estado",LEAD_STATES,index=LEAD_STATES.index(current) if current in LEAD_STATES else 0)
            follow=c2.date_input("Próximo seguimiento",value=parse_date(selected.get("next_followup")) or date.today())
            visit=c3.checkbox("Requiere visita",value=bool(selected.get("needs_visit")))
            loss=None
            if status=="Perdido":
                loss=st.selectbox("Motivo de pérdida *",LOSS_REASONS,index=LOSS_REASONS.index(selected.get("loss_reason")) if selected.get("loss_reason") in LOSS_REASONS else 0)
            notes=st.text_area("Observaciones",value=selected.get("notes") or "",height=120)
            c1,c2=st.columns([1,2])
            if c1.button("Guardar cambios",type="primary",width="stretch"):
                if status=="Perdido" and not loss:
                    st.error("Registrá el motivo de pérdida.")
                else:
                    store.update("leads",selected["id"],{"status":status,"next_followup":follow.isoformat(),"needs_visit":visit,"loss_reason":loss,"notes":notes},actor,f"Actualizó lead {selected.get('name')} a {status}")
                    st.success("Lead actualizado.")
                    st.rerun()
            if selected.get("whatsapp"):
                digits=''.join(ch for ch in selected.get("whatsapp","") if ch.isdigit())
                c2.markdown(f"WhatsApp registrado: **{selected.get('whatsapp')}** · `https://wa.me/{digits}`")

    with tabs[3]:
        if leads:
            df=pd.DataFrame(leads)
            src=df.groupby("source",dropna=False).agg(Leads=("id","count"),Ganados=("status",lambda s:(s=="Ganado").sum()),Perdidos=("status",lambda s:(s=="Perdido").sum())).reset_index()
            denom=src["Ganados"]+src["Perdidos"]
            src["Conversión %"]=(src["Ganados"].div(denom.where(denom.ne(0),1))*100).where(denom.ne(0),0).astype(float)
            st.dataframe(src,width="stretch",hide_index=True,column_config={"Conversión %":st.column_config.NumberColumn(format="%.1f%%")})
            lost=[x for x in leads if x.get("status")=="Perdido"]
            if lost:
                lc=pd.Series([x.get("loss_reason") or "Sin motivo" for x in lost]).value_counts()
                st.bar_chart(lc)
        else:
            empty_state("Sin historia comercial todavía", "Cuando cierres oportunidades, acá vas a ver qué canal trae clientes y por qué se pierden presupuestos.")

from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from core import DAMAGE_TYPES, DIFFICULTIES, QUOTE_STATES, as_float, money, normalize_plate, parse_date
from domain import quote_totals
from theme import page_title, flow_strip
from ui import empty_state


def _ensure_builder():
    st.session_state.setdefault("quote_builder_items", [])


def _quote_label(q):
    return f"#{int(q.get('number',0)):05d} · {q.get('customer_name')} · {q.get('plate') or 'sin patente'} · {q.get('status')}"


def render(store, actor, settings):
    page_title("Cotizador PRO", "Costear antes de ofrecer: mano de obra, preparación, pintura, paños, materiales, repuestos, terceros y dificultad.")
    flow_strip("COTIZACIÓN")
    _ensure_builder()
    quotes=store.list("quotes")
    leads=store.list("leads")
    tabs=st.tabs(["Nueva cotización","Cotizaciones","Seguimiento comercial","Matriz de precios"])

    with tabs[0]:
        required_rates=["labor_hour_cost","prep_hour_cost","paint_hour_cost","assembly_hour_cost","paint_panel_cost"]
        if not any(as_float(settings.get(k)) for k in required_rates):
            st.warning("Los costos productivos están en $0. La cotización funciona, pero para que el precio piso/objetivo sea real configurá costos por hora y por paño en Configuración.")
        c1,c2,c3=st.columns(3)
        lead_opts=[None]+leads
        lead_sel=c1.selectbox("Partir desde un lead",lead_opts,format_func=lambda x:"— Cotización directa —" if x is None else f"{x.get('name')} · {x.get('plate') or 'sin patente'}")
        default_name=lead_sel.get("name","") if lead_sel else ""
        default_car=lead_sel.get("car","") if lead_sel else ""
        default_plate=lead_sel.get("plate","") if lead_sel else ""
        customer=c2.text_input("Cliente *",value=default_name,key="q_customer")
        car=c3.text_input("Vehículo",value=default_car,key="q_car")
        c1,c2,c3=st.columns(3)
        plate=c1.text_input("Patente",value=default_plate,key="q_plate")
        valid_until=c2.date_input("Válida hasta",value=date.today()+timedelta(days=int(settings.get("default_quote_valid_days",7))))
        commercial_notes=c3.text_input("Condición comercial",placeholder="Ej.: 50% anticipo / saldo entrega")

        st.markdown("### Reparaciones")
        with st.expander("+ Agregar reparación / pieza",expanded=not st.session_state.quote_builder_items):
            with st.form("quote_item_form",clear_on_submit=True):
                a,b,c=st.columns(3)
                piece=a.text_input("Pieza afectada *",placeholder="Paragolpes delantero")
                damage=b.selectbox("Tipo de daño",DAMAGE_TYPES)
                difficulty=c.selectbox("Dificultad",DIFFICULTIES,index=1)
                a,b,c,d=st.columns(4)
                chapa=a.number_input("Horas chapa",min_value=0.0,step=.5)
                prep=b.number_input("Horas preparación",min_value=0.0,step=.5)
                paint=c.number_input("Horas pintura",min_value=0.0,step=.5)
                assembly=d.number_input("Horas desarme/armado",min_value=0.0,step=.5)
                a,b,c,d=st.columns(4)
                panels=a.number_input("Paños",min_value=0.0,step=.5)
                materials=b.number_input("Materiales estimados $",min_value=0.0,step=1000.0)
                parts=c.number_input("Repuestos $",min_value=0.0,step=1000.0)
                outsource=d.number_input("Tercerizaciones $",min_value=0.0,step=1000.0)
                detail=st.text_input("Detalle técnico")
                add=st.form_submit_button("Agregar al presupuesto",type="primary",width="stretch")
            if add:
                if not piece.strip(): st.error("Indicá la pieza afectada.")
                else:
                    st.session_state.quote_builder_items.append({"piece":piece.strip(),"damage_type":damage,"difficulty":difficulty,"chapa_hours":chapa,"prep_hours":prep,"paint_hours":paint,"assembly_hours":assembly,"panels":panels,"materials_estimated":materials,"parts_estimated":parts,"outsourcing_estimated":outsource,"detail":detail.strip()})
                    st.rerun()

        items=st.session_state.quote_builder_items
        if items:
            rows=[]
            totals=quote_totals(items,settings)
            for i,it in enumerate(items):
                d=totals["items_detail"][i]
                rows.append({"#":i+1,"Pieza":it["piece"],"Daño":it["damage_type"],"Dificultad":it["difficulty"],"Horas":d["hours"],"Paños":it["panels"],"Costo estimado":d["cost"]})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={"Costo estimado":st.column_config.NumberColumn(format="$ %.0f")})
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Costo estimado",money(totals["estimated_cost"]))
            c2.metric("Precio piso",money(totals["price_floor"]),delta=f"Margen {as_float(settings.get('floor_margin_pct'))*100:.0f}%")
            c3.metric("Precio objetivo",money(totals["price_target"]),delta=f"Margen {as_float(settings.get('target_margin_pct'))*100:.0f}%")
            c4.metric("Horas estimadas",f"{totals['estimated_hours']:.1f} h")
            a,b,c=st.columns(3)
            offered=a.number_input("Precio ofrecido *",min_value=0.0,value=float(round(totals["price_target"],-3)) if totals["price_target"] else 0.0,step=5000.0)
            estimated_days=b.number_input("Días estimados",min_value=1,step=1,value=max(1,int((totals["estimated_hours"]+7.9)//8)))
            status=c.selectbox("Estado inicial",["Borrador","Enviado"])
            gross=offered-totals["estimated_cost"]
            margin_pct=gross/offered if offered else 0
            st.caption(f"Margen esperado: **{money(gross)} ({margin_pct*100:.1f}%)**")
            if totals["price_floor"] and offered < totals["price_floor"]:
                st.error(f"El precio ofrecido está por debajo del precio piso en {money(totals['price_floor']-offered)}.")
            c1,c2=st.columns([3,1])
            save=c1.button("Guardar cotización",type="primary",width="stretch")
            clear=c2.button("Vaciar reparaciones",width="stretch")
            if clear:
                st.session_state.quote_builder_items=[]; st.rerun()
            if save:
                if not customer.strip() or offered<=0:
                    st.error("Cliente y precio ofrecido son obligatorios.")
                else:
                    n=store.next_number("quotes")
                    q=store.insert("quotes",{
                        "number":n,"lead_id":lead_sel.get("id") if lead_sel else None,"customer_name":customer.strip(),"car":car.strip(),"plate":normalize_plate(plate),
                        "items":items,"estimated_cost":totals["estimated_cost"],"price_floor":totals["price_floor"],"price_target":totals["price_target"],"offered_price":offered,
                        "expected_margin":gross,"expected_margin_pct":margin_pct,"estimated_hours":totals["estimated_hours"],"estimated_days":estimated_days,"status":status,
                        "valid_until":valid_until.isoformat(),"commercial_notes":commercial_notes.strip(),"sent_date":date.today().isoformat() if status=="Enviado" else None
                    },actor,f"Creó cotización #{n:05d} por {money(offered)}")
                    if lead_sel:
                        store.update("leads",lead_sel["id"],{"status":"Cotizado" if status=="Borrador" else "Seguimiento","next_followup":(date.today()+timedelta(days=2)).isoformat()},actor,f"Vinculó lead a cotización #{n:05d}")
                    st.session_state.quote_builder_items=[]
                    st.success(f"Cotización #{n:05d} guardada.")
                    st.rerun()
        else:
            empty_state("Presupuesto sin reparaciones", "Agregá una pieza o reparación para que el motor calcule costos y precios.")

    with tabs[1]:
        if not quotes:
            empty_state("Todavía no hay cotizaciones", "Las cotizaciones guardadas aparecen acá con costo, piso, objetivo y margen esperado.")
        else:
            rows=[{"N°":f"#{int(q.get('number',0)):05d}","Cliente":q.get("customer_name"),"Patente":q.get("plate"),"Estado":q.get("status"),"Costo":q.get("estimated_cost"),"Piso":q.get("price_floor"),"Objetivo":q.get("price_target"),"Ofrecido":q.get("offered_price"),"Margen %":as_float(q.get("expected_margin_pct"))*100,"Válida hasta":parse_date(q.get("valid_until"))} for q in quotes]
            st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True,column_config={k:st.column_config.NumberColumn(format="$ %.0f") for k in ["Costo","Piso","Objetivo","Ofrecido"]}|{"Margen %":st.column_config.NumberColumn(format="%.1f%%")})
            sel=st.selectbox("Abrir cotización",quotes,format_func=_quote_label)
            c1,c2,c3=st.columns(3)
            new_status=c1.selectbox("Estado",QUOTE_STATES,index=QUOTE_STATES.index(sel.get("status")) if sel.get("status") in QUOTE_STATES else 0,key="q_status_edit")
            follow=c2.date_input("Próximo seguimiento",value=parse_date(sel.get("next_followup")) or (date.today()+timedelta(days=2)))
            new_offer=c3.number_input("Precio ofrecido",min_value=0.0,value=as_float(sel.get("offered_price")),step=5000.0,key="q_offer_edit")
            notes=st.text_area("Notas comerciales",value=sel.get("commercial_notes") or "")
            if st.button("Actualizar cotización",type="primary"):
                cost=as_float(sel.get("estimated_cost")); margin=new_offer-cost
                store.update("quotes",sel["id"],{"status":new_status,"next_followup":follow.isoformat(),"offered_price":new_offer,"expected_margin":margin,"expected_margin_pct":margin/new_offer if new_offer else 0,"commercial_notes":notes},actor,f"Actualizó cotización #{int(sel.get('number',0)):05d} a {new_status}")
                if sel.get("lead_id"):
                    mapped="Ganado" if new_status=="Aprobada" else ("Perdido" if new_status=="Rechazada" else "Seguimiento")
                    store.update("leads",sel["lead_id"],{"status":mapped,"next_followup":follow.isoformat()},actor,f"Sincronizó estado desde cotización #{int(sel.get('number',0)):05d}")
                st.success("Cotización actualizada."); st.rerun()

    with tabs[2]:
        open_q=[q for q in quotes if q.get("status") in ("Enviado","Seguimiento")]
        if open_q:
            rows=[]
            for q in open_q:
                sent=parse_date(q.get("sent_date") or q.get("created_at")); days=(date.today()-sent).days if sent else 0
                rows.append({"Cotización":f"#{int(q.get('number',0)):05d}","Cliente":q.get("customer_name"),"Patente":q.get("plate"),"Monto":q.get("offered_price"),"Días abierta":days,"Seguimiento":parse_date(q.get("next_followup")),"Estado":q.get("status")})
            st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True,column_config={"Monto":st.column_config.NumberColumn(format="$ %.0f")})
        else: empty_state("Sin presupuestos en seguimiento","Cuando envíes cotizaciones, esta bandeja te dice cuáles requieren acción comercial.")

    with tabs[3]:
        data=[
            ("Hora chapa",settings.get("labor_hour_cost")),("Hora preparación",settings.get("prep_hour_cost")),("Hora pintura",settings.get("paint_hour_cost")),
            ("Hora armado/desarme",settings.get("assembly_hour_cost")),("Pintura por paño",settings.get("paint_panel_cost")),("Margen piso",as_float(settings.get("floor_margin_pct"))*100),("Margen objetivo",as_float(settings.get("target_margin_pct"))*100)
        ]
        st.dataframe(pd.DataFrame(data,columns=["Parámetro","Valor"]),width="stretch",hide_index=True)
        st.caption("La matriz es centralizada. Modificarla en Configuración cambia los próximos cálculos sin alterar presupuestos históricos ya guardados.")

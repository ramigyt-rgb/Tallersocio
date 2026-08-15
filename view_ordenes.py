from __future__ import annotations

from datetime import date, timedelta
import base64
import pandas as pd
import streamlit as st

from core import PRIORITIES, PRODUCTION_STAGES, encode_uploads, decode_upload, money, normalize_plate, parse_date, as_float
from domain import work_order_margin
from theme import page_title, flow_strip
from ui import empty_state


def _label(o):
    return f"#{int(o.get('number',0)):05d} · {o.get('plate') or 'sin patente'} · {o.get('customer_name')} · {o.get('stage')}"


def _render_photos(items):
    if not items: return
    cols=st.columns(min(4,len(items)))
    for i,item in enumerate(items[:12]):
        try: cols[i%len(cols)].image(decode_upload(item),caption=item.get("name"),width="stretch")
        except Exception: pass


def render(store, actor, settings):
    page_title("Órdenes de trabajo", "Ingreso documentado, alcance cerrado, anticipo, saldo, compromiso de entrega y rentabilidad por OT.")
    flow_strip("INGRESO")
    ots=store.list("work_orders")
    quotes=store.list("quotes")
    mat_moves=store.list("material_moves")
    approved=[q for q in quotes if q.get("status")=="Aprobada" and not any(o.get("quote_id")==q.get("id") for o in ots)]
    tabs=st.tabs(["OT activas","Crear OT","Ficha completa","Historial"])

    with tabs[0]:
        active=[o for o in ots if o.get("stage")!="Entregado" and not o.get("cancelled")]
        if active:
            rows=[]
            for o in active:
                m=work_order_margin(o,mat_moves); promised=parse_date(o.get("promised_date")); balance=as_float(o.get("agreed_amount"))-as_float(o.get("paid_amount"))
                rows.append({"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Cliente":o.get("customer_name"),"Vehículo":o.get("car"),"Etapa":o.get("stage"),"Prioridad":o.get("priority"),"Prometido":promised,"Monto":o.get("agreed_amount"),"Cobrado":o.get("paid_amount"),"Saldo":balance,"Costo real":m["direct_cost"],"Margen actual":m["margin"],"Atrasada":bool(promised and promised<date.today())})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch",column_config={k:st.column_config.NumberColumn(format="$ %.0f") for k in ["Monto","Cobrado","Saldo","Costo real","Margen actual"]})
        else: empty_state("No hay órdenes activas","Creá una OT directa o convertí una cotización aprobada.")

    with tabs[1]:
        source=st.radio("Origen",["Desde cotización aprobada","OT directa"],horizontal=True,index=0 if approved else 1)
        q=None
        if source=="Desde cotización aprobada":
            if not approved:
                st.info("No hay cotizaciones aprobadas pendientes de convertir.")
            else:
                q=st.selectbox("Cotización",approved,format_func=lambda x:f"#{int(x.get('number',0)):05d} · {x.get('customer_name')} · {money(x.get('offered_price'))}")
        default_customer=q.get("customer_name","") if q else ""; default_car=q.get("car","") if q else ""; default_plate=q.get("plate","") if q else ""; default_amount=as_float(q.get("offered_price")) if q else 0; default_hours=as_float(q.get("estimated_hours")) if q else 0; default_days=int(q.get("estimated_days") or 3) if q else 3
        with st.form("create_ot"):
            c1,c2,c3,c4=st.columns(4)
            customer=c1.text_input("Cliente *",value=default_customer)
            whatsapp=c2.text_input("WhatsApp")
            car=c3.text_input("Vehículo *",value=default_car)
            plate=c4.text_input("Patente *",value=default_plate)
            c1,c2,c3,c4=st.columns(4)
            km=c1.number_input("Kilometraje",min_value=0,step=100)
            fuel=c2.selectbox("Combustible",["Reserva","1/4","1/2","3/4","Lleno","No indicado"])
            priority=c3.selectbox("Prioridad",PRIORITIES,index=1)
            entry=c4.date_input("Fecha ingreso",value=date.today())
            c1,c2,c3=st.columns(3)
            promised=c1.date_input("Fecha prometida",value=date.today()+timedelta(days=max(1,default_days)))
            amount=c2.number_input("Monto acordado *",min_value=0.0,value=default_amount,step=5000.0)
            advance=c3.number_input("Anticipo recibido",min_value=0.0,step=5000.0)
            included=st.text_area("Qué SE va a hacer *",value="\n".join(f"- {it.get('piece')}: {it.get('damage_type')}" for it in (q.get("items",[]) if q else [])))
            excluded=st.text_area("Qué NO se va a hacer / exclusiones")
            preexisting=st.text_area("Daños preexistentes")
            observations=st.text_area("Observaciones / aceptación")
            photos=st.file_uploader("Fotos de ingreso",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key="ot_new_photos")
            acceptance=st.checkbox("Cliente informado del alcance, exclusiones, monto y fecha prometida")
            ok=st.form_submit_button("Crear Orden de Trabajo",type="primary",width="stretch")
        if ok:
            if not customer.strip() or not car.strip() or not normalize_plate(plate) or not included.strip() or amount<=0 or not acceptance:
                st.error("Completá cliente, vehículo, patente, alcance, monto y aceptación.")
            elif advance>amount:
                st.error("El anticipo no puede superar el monto acordado.")
            else:
                n=store.next_number("work_orders")
                estimated_materials=sum(as_float(it.get("materials_estimated")) for it in (q.get("items",[]) if q else []))
                ot=store.insert("work_orders",{"number":n,"quote_id":q.get("id") if q else None,"lead_id":q.get("lead_id") if q else None,"customer_name":customer.strip(),"whatsapp":whatsapp.strip(),"car":car.strip(),"plate":normalize_plate(plate),"km_in":km,"fuel_in":fuel,"priority":priority,"entry_date":entry.isoformat(),"promised_date":promised.isoformat(),"agreed_amount":amount,"paid_amount":advance,"scope_included":included.strip(),"scope_excluded":excluded.strip(),"preexisting_damage":preexisting.strip(),"notes":observations.strip(),"acceptance":True,"photos_in":encode_uploads(photos),"stage":"Esperando","estimated_hours":default_hours,"estimated_direct_cost":as_float(q.get("estimated_cost")) if q else 0.0,"estimated_material_cost":estimated_materials,"expected_margin":as_float(q.get("expected_margin")) if q else 0.0,"parts_actual":0.0,"outsourcing_actual":0.0,"other_direct_actual":0.0,"labor_actual_cost":0.0,"blocker":"","delivery_date":None,"cancelled":False},actor,f"Creó OT #{n:05d} · {normalize_plate(plate)} · {money(amount)}")
                if q:
                    store.update("quotes",q["id"],{"status":"Aprobada","converted_ot_id":ot["id"]},actor,f"Convirtió cotización #{int(q.get('number',0)):05d} en OT #{n:05d}")
                    if q.get("lead_id"): store.update("leads",q["lead_id"],{"status":"Ganado"},actor,f"Lead ganado por OT #{n:05d}")
                if advance>0:
                    store.insert("financial_moves",{"movement_date":date.today().isoformat(),"direction":"Ingreso","category":"Anticipo cliente","account":"Caja","amount":advance,"status":"Pagado","due_date":None,"paid_date":date.today().isoformat(),"counterparty":customer.strip(),"work_order_id":ot["id"],"notes":f"Anticipo OT #{n:05d}","voided":False},actor,f"Registró anticipo de {money(advance)} para OT #{n:05d}")
                st.success(f"OT #{n:05d} creada."); st.rerun()

    with tabs[2]:
        if not ots: empty_state("Sin OT","Cuando crees la primera orden, su ficha integral aparece acá.")
        else:
            sel=st.selectbox("Orden de trabajo",ots,format_func=_label)
            m=work_order_margin(sel,mat_moves); balance=as_float(sel.get("agreed_amount"))-as_float(sel.get("paid_amount"))
            variance=m["direct_cost"]-as_float(sel.get("estimated_direct_cost")) if as_float(sel.get("estimated_direct_cost")) else 0.0
            a,b,c,d,e=st.columns(5); a.metric("Monto",money(sel.get("agreed_amount"))); b.metric("Cobrado",money(sel.get("paid_amount"))); c.metric("Saldo",money(balance)); d.metric("Margen actual",money(m["margin"]),delta=f"{m['margin_pct']*100:.1f}%"); e.metric("Desvío costo",money(variance),delta="vs cotizado" if as_float(sel.get("estimated_direct_cost")) else "sin estimación")
            c1,c2=st.columns(2)
            with c1:
                st.markdown("#### Ingreso y alcance")
                st.write(f"**Cliente:** {sel.get('customer_name')} · **Patente:** {sel.get('plate')} · **Vehículo:** {sel.get('car')}")
                st.write(f"**KM:** {sel.get('km_in',0):,.0f} · **Combustible:** {sel.get('fuel_in')} · **Ingreso:** {sel.get('entry_date')} · **Prometido:** {sel.get('promised_date')}")
                st.text_area("Incluido",value=sel.get("scope_included") or "",disabled=True)
                st.text_area("Excluido",value=sel.get("scope_excluded") or "",disabled=True)
                st.text_area("Daños preexistentes",value=sel.get("preexisting_damage") or "",disabled=True)
            with c2:
                st.markdown("#### Costos reales directos")
                parts=st.number_input("Repuestos reales",min_value=0.0,value=as_float(sel.get("parts_actual")),step=1000.0,key=f"parts_{sel['id']}")
                outsource=st.number_input("Tercerizaciones reales",min_value=0.0,value=as_float(sel.get("outsourcing_actual")),step=1000.0,key=f"outs_{sel['id']}")
                other=st.number_input("Otros directos",min_value=0.0,value=as_float(sel.get("other_direct_actual")),step=1000.0,key=f"other_{sel['id']}")
                labor=st.number_input("Costo mano de obra imputado",min_value=0.0,value=as_float(sel.get("labor_actual_cost")),step=1000.0,key=f"labor_{sel['id']}")
                if st.button("Guardar costos",type="primary",key=f"save_cost_{sel['id']}"):
                    store.update("work_orders",sel["id"],{"parts_actual":parts,"outsourcing_actual":outsource,"other_direct_actual":other,"labor_actual_cost":labor},actor,f"Actualizó costos reales OT #{int(sel.get('number',0)):05d}"); st.rerun()
            if sel.get("photos_in"):
                st.markdown("#### Fotos de ingreso"); _render_photos(sel.get("photos_in"))

    with tabs[3]:
        if ots:
            rows=[{"OT":f"#{int(o.get('number',0)):05d}","Cliente":o.get("customer_name"),"Patente":o.get("plate"),"Vehículo":o.get("car"),"Etapa":o.get("stage"),"Ingreso":parse_date(o.get("entry_date")),"Entrega":parse_date(o.get("delivery_date")),"Monto":o.get("agreed_amount"),"Cobrado":o.get("paid_amount")} for o in ots]
            st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True,column_config={"Monto":st.column_config.NumberColumn(format="$ %.0f"),"Cobrado":st.column_config.NumberColumn(format="$ %.0f")})
        else: empty_state("Sin historial","Todavía no hay órdenes registradas.")

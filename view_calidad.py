from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from core import QC_ITEMS, encode_uploads, decode_upload
from theme import page_title, flow_strip
from ui import empty_state


def render(store, actor, settings):
    page_title("Control de calidad", "Ningún auto se entrega sin checklist, hallazgos y aprobación final trazable.")
    flow_strip("CONTROL")
    ots=store.list("work_orders")
    checks=store.list("qc_checks")
    candidates=[o for o in ots if o.get("stage") in ("Control de calidad","Listo para entregar") and not o.get("cancelled")]
    tabs=st.tabs(["Pendientes de QC","Nueva inspección","Historial & retrabajos"])

    with tabs[0]:
        if candidates:
            rows=[]
            for o in candidates:
                q=[x for x in checks if x.get("work_order_id")==o.get("id")]
                last=q[-1] if q else None
                rows.append({"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Cliente":o.get("customer_name"),"Etapa":o.get("stage"),"Último QC":last.get("result") if last else "Sin inspección","Fecha":last.get("check_date") if last else None,"Hallazgos":last.get("findings") if last else ""})
            st.dataframe(pd.DataFrame(rows),hide_index=True,width="stretch")
        else: empty_state("No hay autos esperando control","Cuando una OT pase a Control de calidad aparecerá acá.")

    with tabs[1]:
        if not candidates: empty_state("Sin OT elegible","Mové una OT a Control de calidad para inspeccionarla.")
        else:
            sel=st.selectbox("OT a inspeccionar",candidates,format_func=lambda o:f"#{int(o.get('number',0)):05d} · {o.get('plate')} · {o.get('car')}")
            st.markdown("### Checklist")
            results={}
            cols=st.columns(2)
            for i,item in enumerate(QC_ITEMS):
                results[item]=cols[i%2].selectbox(item,["OK","Observado","No aplica"],key=f"qc_{sel['id']}_{i}")
            findings=st.text_area("Hallazgos / correcciones necesarias")
            rework_hours=st.number_input("Horas de retrabajo generadas",min_value=0.0,step=.5)
            photos=st.file_uploader("Fotos de control",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key=f"qc_photos_{sel['id']}")
            any_obs=any(v=="Observado" for v in results.values())
            suggested="Rechazado / retrabajo" if any_obs else "Aprobado"
            result=st.radio("Resultado final",["Aprobado","Rechazado / retrabajo"],index=1 if any_obs else 0,horizontal=True)
            if st.button("Cerrar control de calidad",type="primary",width="stretch"):
                if result=="Aprobado" and any_obs:
                    st.error("Hay ítems observados. Corregilos o cerrá como retrabajo.")
                elif result!="Aprobado" and not findings.strip():
                    st.error("Describí qué debe corregirse.")
                else:
                    store.insert("qc_checks",{"work_order_id":sel["id"],"check_date":date.today().isoformat(),"items":results,"findings":findings.strip(),"rework_hours":rework_hours,"result":result,"photos":encode_uploads(photos)},actor,f"QC {result} · OT #{int(sel.get('number',0)):05d}")
                    if result=="Aprobado": store.update("work_orders",sel["id"],{"stage":"Listo para entregar","blocker":""},actor,f"QC aprobado: OT #{int(sel.get('number',0)):05d} lista para entregar")
                    else: store.update("work_orders",sel["id"],{"stage":"Preparación","blocker":"Retrabajo por control de calidad","progress_pct":max(0,int(sel.get('progress_pct') or 90)-15)},actor,f"QC rechazado: OT #{int(sel.get('number',0)):05d} vuelve a retrabajo")
                    st.success("Control registrado."); st.rerun()

    with tabs[2]:
        if checks:
            ot_map={o.get("id"):o for o in ots}
            rows=[]
            for q in checks:
                o=ot_map.get(q.get("work_order_id"),{})
                rows.append({"Fecha":q.get("check_date"),"OT":f"#{int(o.get('number',0)):05d}","Patente":o.get("plate"),"Resultado":q.get("result"),"Retrabajo h":q.get("rework_hours",0),"Hallazgos":q.get("findings")})
            df=pd.DataFrame(rows)
            a,b,c=st.columns(3); a.metric("Controles",len(df)); b.metric("Aprobación primera pasada",f"{(df['Resultado']=='Aprobado').mean()*100:.1f}%"); c.metric("Horas retrabajo",f"{pd.to_numeric(df['Retrabajo h'],errors='coerce').fillna(0).sum():.1f} h")
            st.dataframe(df,hide_index=True,width="stretch")
        else: empty_state("Sin controles cerrados","El historial de calidad y retrabajos queda trazado acá.")

from __future__ import annotations

from datetime import date, datetime
import json
import streamlit as st

from core import DATA_FILE
from exporter import export_excel
from theme import page_title


def render(store, actor, settings):
    page_title("Centro de datos", "Respaldo, exportación y restauración. Sin SQL, sin Supabase y sin subcarpetas.")
    state=store.state()
    tabs=st.tabs(["Estado","Respaldar","Restaurar","Reinicio total"])

    with tabs[0]:
        st.markdown(f"**Archivo operativo actual:** `{DATA_FILE}`")
        cols=st.columns(4)
        cols[0].metric("Leads",len(state.get("leads",[])))
        cols[1].metric("Cotizaciones",len(state.get("quotes",[])))
        cols[2].metric("OT",len(state.get("work_orders",[])))
        cols[3].metric("Mov. financieros",len(state.get("financial_moves",[])))
        st.caption("Este archivo plano permite usar la app localmente ahora. No es una base de datos. Cuando integremos Google Sheets, se reemplaza solamente la capa store.py.")

    with tabs[1]:
        snapshot=store.snapshot_bytes()
        st.download_button("Descargar respaldo completo JSON",snapshot,file_name=f"Taller_OS_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",mime="application/json",type="primary",width="stretch")
        excel=export_excel(state)
        st.download_button("Descargar Excel de control",excel,file_name=f"Taller_OS_{date.today().isoformat()}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",width="stretch")
        st.caption("El JSON permite restaurar toda la aplicación, incluso listas internas y fotos codificadas. El Excel está pensado para análisis humano y migración futura.")

    with tabs[2]:
        uploaded=st.file_uploader("Seleccionar respaldo JSON",type=["json"])
        phrase=st.text_input("Escribí RESTAURAR para habilitar la importación")
        if st.button("Restaurar respaldo",type="primary",disabled=phrase!="RESTAURAR"):
            if not uploaded: st.error("Seleccioná un archivo.")
            else:
                try:
                    payload=json.loads(uploaded.getvalue().decode("utf-8"))
                    if not isinstance(payload,dict) or "settings" not in payload: raise ValueError("Formato no reconocido")
                    store.bulk_replace(payload,actor); st.success("Respaldo restaurado."); st.rerun()
                except Exception as exc: st.error(f"No se pudo restaurar: {exc}")

    with tabs[3]:
        st.error("Esta acción deja la aplicación operativamente vacía. No hay deshacer salvo que tengas un respaldo JSON.")
        phrase=st.text_input("Para reiniciar escribí: BORRAR TODO",key="reset_phrase")
        if st.button("Reiniciar todos los datos",disabled=phrase!="BORRAR TODO"):
            store.reset(actor); st.success("Datos reiniciados."); st.rerun()

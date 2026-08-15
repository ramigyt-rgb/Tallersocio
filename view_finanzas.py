from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from theme import page_title
from utils import money


def render(repo, user, settings):
    page_title("Caja y finanzas", "Todo visible: caja, banco, cobros, gastos, cuentas, aportes y retiros. Los movimientos no se eliminan: se corrigen con trazabilidad.")
    moves = repo.list_rows("financial_movements")
    ots = repo.list_rows("work_orders")
    tabs=st.tabs(["Resumen","Nuevo movimiento","Cuentas a cobrar / pagar","Historial"])

    paid_in=sum(float(r.get("amount") or 0) for r in moves if r.get("direction")=="Ingreso" and r.get("status")=="Pagado")
    paid_out=sum(float(r.get("amount") or 0) for r in moves if r.get("direction")=="Egreso" and r.get("status")=="Pagado")
    receivable=sum(float(r.get("amount") or 0) for r in moves if r.get("direction")=="Ingreso" and r.get("status")=="Pendiente")
    payable=sum(float(r.get("amount") or 0) for r in moves if r.get("direction")=="Egreso" and r.get("status")=="Pendiente")

    with tabs[0]:
        a,b,c,d=st.columns(4)
        a.metric("Posición neta cargada",money(paid_in-paid_out))
        b.metric("Por cobrar",money(receivable))
        c.metric("Por pagar",money(payable))
        d.metric("Exposición neta",money(receivable-payable))
        if moves:
            df=pd.DataFrame(moves)
            df["movement_date"]=pd.to_datetime(df["movement_date"],errors="coerce")
            df["signed"]=pd.to_numeric(df["amount"],errors="coerce").fillna(0)*df["direction"].map({"Ingreso":1,"Egreso":-1}).fillna(0)
            monthly=df.dropna(subset=["movement_date"]).groupby(df["movement_date"].dt.to_period("M"))["signed"].sum().reset_index()
            monthly["movement_date"]=monthly["movement_date"].astype(str)
            st.bar_chart(monthly.set_index("movement_date")["signed"])

    with tabs[1]:
        with st.form("fin_move",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            direction=c1.selectbox("Dirección",["Ingreso","Egreso"])
            typ=c2.selectbox("Tipo",["Cobro cliente","Anticipo cliente","Compra","Gasto fijo","Aporte socio","Retiro socio","Pago proveedor","Impuesto","Otro"])
            account=c3.selectbox("Cuenta",["Caja","Banco","Mercado Pago","Otro"])
            c1,c2,c3=st.columns(3)
            category=c1.selectbox("Categoría",["Cobros","Pinturería","Materiales","Repuestos","Estructura","Servicios","Aportes","Retiros","Impuestos","Otros"])
            amount=c2.number_input("Monto",min_value=0.0,step=10000.0)
            status=c3.selectbox("Estado",["Pagado","Pendiente"])
            c1,c2=st.columns(2)
            due=c1.date_input("Vencimiento",value=date.today())
            counterparty=c2.text_input("Cliente / proveedor / socio")
            active_ots=[o for o in ots if not o.get("archived")]
            ot_labels=["— Sin OT —"]+[f'#{int(o.get("number",0)):05d} · {o.get("plate")} · {o.get("customer_name")}' for o in active_ots]
            ot_sel=st.selectbox("Relacionar con OT",ot_labels)
            notes=st.text_area("Concepto / observación")
            ok=st.form_submit_button("Registrar movimiento",type="primary",use_container_width=True)
        if ok:
            if amount<=0:
                st.error("El monto debe ser mayor a cero.")
            else:
                ot_id=None if ot_sel=="— Sin OT —" else active_ots[ot_labels.index(ot_sel)-1]["id"]
                repo.insert("financial_movements",{"movement_date":date.today().isoformat(),"direction":direction,"type":typ,"account":account,"category":category,"amount":amount,
                    "status":status,"due_date":due.isoformat() if status=="Pendiente" else None,"paid_date":date.today().isoformat() if status=="Pagado" else None,
                    "counterparty":counterparty.strip(),"work_order_id":ot_id,"notes":notes.strip()},user,f"Cargó {direction.lower()} {money(amount)} · {typ} · {counterparty.strip() or 'sin contraparte'}")
                if ot_id and direction=="Ingreso" and status=="Pagado":
                    ot=next((o for o in active_ots if str(o.get("id"))==str(ot_id)),None)
                    if ot:
                        repo.update("work_orders",ot_id,{"paid_amount":float(ot.get("paid_amount") or 0)+amount},user,f"Imputó cobro {money(amount)} a OT #{int(ot.get('number',0)):05d}")
                st.success("Movimiento registrado.")
                st.rerun()

    with tabs[2]:
        pend=[r for r in moves if r.get("status")=="Pendiente"]
        if pend:
            df=pd.DataFrame(pend)
            st.dataframe(df[[c for c in ["movement_date","direction","type","category","counterparty","amount","due_date","notes"] if c in df.columns]],use_container_width=True,hide_index=True,
                         column_config={"amount":st.column_config.NumberColumn("Monto",format="$ %.0f")})
            labels={f'{r.get("direction")} · {r.get("counterparty") or r.get("type")} · {money(r.get("amount"))}':r for r in pend}
            chosen=st.selectbox("Marcar como pagado/cobrado",list(labels.keys()))
            if st.button("Confirmar pago / cobro",type="primary"):
                r=labels[chosen]
                repo.update("financial_movements",r["id"],{"status":"Pagado","paid_date":date.today().isoformat()},user,f"Marcó como pagado/cobrado {money(r.get('amount'))} · {r.get('counterparty') or r.get('type')}")
                if r.get("work_order_id") and r.get("direction")=="Ingreso":
                    ot=next((o for o in ots if str(o.get("id"))==str(r.get("work_order_id"))),None)
                    if ot:
                        repo.update("work_orders",ot["id"],{"paid_amount":float(ot.get("paid_amount") or 0)+float(r.get("amount") or 0)},user,f"Imputó cobro a OT #{int(ot.get('number',0)):05d}")
                st.success("Actualizado.")
                st.rerun()
        else:
            st.success("No hay cuentas pendientes cargadas.")

    with tabs[3]:
        if moves:
            df=pd.DataFrame(moves)
            keep=[c for c in ["movement_date","direction","type","account","category","amount","status","counterparty","work_order_id","notes","created_at"] if c in df.columns]
            st.dataframe(df[keep],use_container_width=True,hide_index=True,column_config={"amount":st.column_config.NumberColumn("Monto",format="$ %.0f")})
        st.caption("No hay botón Eliminar. Una corrección debe quedar como modificación o movimiento compensatorio y dejar auditoría.")

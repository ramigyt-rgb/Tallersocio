from __future__ import annotations

from datetime import date, timedelta
import pandas as pd
import streamlit as st

from core import ACCOUNTS, FIN_CATEGORIES_IN, FIN_CATEGORIES_OUT, MOVE_DIRECTIONS, as_float, money, parse_date
from domain import finance_summary
from theme import page_title
from ui import empty_state


def _move_label(x):
    return f"{x.get('direction')} · {x.get('counterparty') or x.get('category')} · {money(x.get('amount'))} · {x.get('status')}"


def render(store, actor, settings):
    page_title("Caja & finanzas", "Libro único de caja y banco, cuentas a cobrar/pagar, aportes, retiros, vencimientos y trazabilidad sin borrados silenciosos.")
    moves=store.list("financial_moves")
    ots=store.list("work_orders")
    suppliers=store.list("suppliers")
    fin=finance_summary(moves)
    tabs=st.tabs(["Posición","Nuevo movimiento","Cuentas pendientes","Caja / Banco","Flujo 30 días","Correcciones"])

    with tabs[0]:
        a,b,c,d,e=st.columns(5)
        a.metric("Caja + bancos",money(fin["cash_total"]))
        b.metric("Por cobrar",money(fin["receivable"]))
        c.metric("Por pagar",money(fin["payable"]))
        d.metric("Flujo mes",money(fin["month_net"]),delta=f"Ingresos {money(fin['month_in'])} / Egresos {money(fin['month_out'])}")
        e.metric("Posición ampliada",money(fin["cash_total"]+fin["receivable"]-fin["payable"]))
        if fin["overdue_receivable"] or fin["overdue_payable"]:
            st.warning(f"Vencidos: por cobrar {money(fin['overdue_receivable'])} · por pagar {money(fin['overdue_payable'])}")
        paid=[x for x in moves if x.get("status")=="Pagado" and not x.get("voided")]
        if paid:
            df=pd.DataFrame(paid)
            df["movement_date"]=pd.to_datetime(df["movement_date"],errors="coerce")
            df["signed"]=pd.to_numeric(df["amount"],errors="coerce").fillna(0)*df["direction"].map({"Ingreso":1,"Egreso":-1})
            month=df.dropna(subset=["movement_date"]).groupby(df["movement_date"].dt.to_period("M"))["signed"].sum()
            month.index=month.index.astype(str)
            st.bar_chart(month)
        else: empty_state("Sin movimientos financieros","La caja queda en cero hasta que registres un cobro, gasto, aporte o retiro real.")

    with tabs[1]:
        direction=st.radio("Dirección del movimiento",MOVE_DIRECTIONS,horizontal=True,key="fin_direction")
        with st.form("new_fin_move",clear_on_submit=True):
            c1,c2,c3=st.columns(3)
            category=c1.selectbox("Categoría",FIN_CATEGORIES_IN if direction=="Ingreso" else FIN_CATEGORIES_OUT)
            account=c2.selectbox("Cuenta",ACCOUNTS)
            amount=c3.number_input("Monto *",min_value=0.0,step=5000.0)
            c1,c2,c3=st.columns(3)
            status=c1.selectbox("Estado",["Pagado","Pendiente"])
            movement_date=c2.date_input("Fecha",value=date.today())
            due=c3.date_input("Vencimiento",value=date.today()+timedelta(days=int(settings.get("default_payment_terms_days",0))))
            c1,c2=st.columns(2)
            counterparty=c1.text_input("Cliente / proveedor / socio")
            active_ots=[o for o in ots if not o.get("cancelled")]
            ot=c2.selectbox("Imputar a OT",[None]+active_ots,format_func=lambda x:"— Sin OT —" if x is None else f"#{int(x.get('number',0)):05d} · {x.get('plate')} · saldo {money(as_float(x.get('agreed_amount'))-as_float(x.get('paid_amount')))}")
            notes=st.text_area("Concepto / comprobante / observación")
            ok=st.form_submit_button("Registrar movimiento",type="primary",width="stretch")
        if ok:
            if amount<=0: st.error("El monto debe ser mayor a cero.")
            elif ot and direction=="Ingreso" and category in ("Cobro cliente","Anticipo cliente") and status=="Pagado" and amount>as_float(ot.get("agreed_amount"))-as_float(ot.get("paid_amount")):
                st.error("El cobro supera el saldo pendiente de la OT.")
            else:
                row=store.insert("financial_moves",{"movement_date":movement_date.isoformat(),"direction":direction,"category":category,"account":account,"amount":amount,"status":status,"due_date":due.isoformat() if status=="Pendiente" else None,"paid_date":movement_date.isoformat() if status=="Pagado" else None,"counterparty":counterparty.strip(),"work_order_id":ot.get("id") if ot else None,"notes":notes.strip(),"voided":False},actor,f"Registró {direction.lower()} {money(amount)} · {category}")
                if ot and direction=="Ingreso" and category in ("Cobro cliente","Anticipo cliente") and status=="Pagado":
                    store.update("work_orders",ot["id"],{"paid_amount":as_float(ot.get("paid_amount"))+amount},actor,f"Imputó {money(amount)} a OT #{int(ot.get('number',0)):05d}")
                st.success("Movimiento registrado."); st.rerun()

    with tabs[2]:
        pending=[x for x in moves if x.get("status")=="Pendiente" and not x.get("voided")]
        if pending:
            rows=[]
            for x in pending:
                due=parse_date(x.get("due_date")); days=(due-date.today()).days if due else None
                rows.append({"Tipo":x.get("direction"),"Categoría":x.get("category"),"Contraparte":x.get("counterparty"),"Monto":x.get("amount"),"Vencimiento":due,"Días":days,"Estado":"VENCIDO" if days is not None and days<0 else "Pendiente"})
            st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True,column_config={"Monto":st.column_config.NumberColumn(format="$ %.0f")})
            sel=st.selectbox("Confirmar cobro / pago",pending,format_func=_move_label)
            paid_account=st.selectbox("Cuenta utilizada",ACCOUNTS,index=ACCOUNTS.index(sel.get("account")) if sel.get("account") in ACCOUNTS else 0,key="pending_account")
            if st.button("Marcar como pagado",type="primary"):
                store.update("financial_moves",sel["id"],{"status":"Pagado","paid_date":date.today().isoformat(),"account":paid_account},actor,f"Confirmó {sel.get('direction').lower()} {money(sel.get('amount'))}")
                if sel.get("work_order_id") and sel.get("direction")=="Ingreso" and sel.get("category") in ("Cobro cliente","Anticipo cliente"):
                    ot=next((o for o in ots if o.get("id")==sel.get("work_order_id")),None)
                    if ot: store.update("work_orders",ot["id"],{"paid_amount":as_float(ot.get("paid_amount"))+as_float(sel.get("amount"))},actor,f"Imputó cobro pendiente a OT #{int(ot.get('number',0)):05d}")
                st.rerun()
        else: empty_state("Sin cuentas pendientes","No hay cobros ni pagos pendientes cargados.")

    with tabs[3]:
        if fin["cash_by_account"]:
            cols=st.columns(max(1,min(4,len(fin["cash_by_account"]))))
            for i,(account,balance) in enumerate(fin["cash_by_account"].items()): cols[i%len(cols)].metric(account,money(balance))
            if moves:
                paid=[x for x in moves if x.get("status")=="Pagado" and not x.get("voided")]
                if paid:
                    df=pd.DataFrame(paid)
                    st.dataframe(df[[c for c in ["movement_date","direction","category","account","amount","counterparty","notes"] if c in df.columns]],hide_index=True,width="stretch",column_config={"amount":st.column_config.NumberColumn(format="$ %.0f")})
        else: empty_state("Sin saldos","Los saldos por cuenta se construyen únicamente con movimientos pagados/cobrados.")

    with tabs[4]:
        pending=[x for x in moves if x.get("status")=="Pendiente" and not x.get("voided") and parse_date(x.get("due_date"))]
        horizon=date.today()+timedelta(days=30)
        relevant=[x for x in pending if date.today()<=parse_date(x.get("due_date"))<=horizon]
        days=[]; running=fin["cash_total"]
        for i in range(31):
            d=date.today()+timedelta(days=i)
            ins=sum(as_float(x.get("amount")) for x in relevant if parse_date(x.get("due_date"))==d and x.get("direction")=="Ingreso")
            outs=sum(as_float(x.get("amount")) for x in relevant if parse_date(x.get("due_date"))==d and x.get("direction")=="Egreso")
            running+=ins-outs
            days.append({"Fecha":d,"Cobros previstos":ins,"Pagos previstos":outs,"Caja proyectada":running})
        df=pd.DataFrame(days)
        st.line_chart(df.set_index("Fecha")["Caja proyectada"])
        st.dataframe(df[df["Cobros previstos"].ne(0)|df["Pagos previstos"].ne(0)],hide_index=True,width="stretch",column_config={"Cobros previstos":st.column_config.NumberColumn(format="$ %.0f"),"Pagos previstos":st.column_config.NumberColumn(format="$ %.0f"),"Caja proyectada":st.column_config.NumberColumn(format="$ %.0f")})

    with tabs[5]:
        st.caption("No existe botón Eliminar. Una equivocación se anula con motivo y queda en auditoría.")
        valid=[x for x in moves if not x.get("voided")]
        if valid:
            sel=st.selectbox("Movimiento a anular",valid,format_func=_move_label,key="void_move")
            reason=st.text_input("Motivo de anulación")
            if st.button("Anular movimiento"):
                if not reason.strip(): st.error("El motivo es obligatorio.")
                else:
                    if sel.get("work_order_id") and sel.get("direction")=="Ingreso" and sel.get("status")=="Pagado" and sel.get("category") in ("Cobro cliente","Anticipo cliente"):
                        ot=next((o for o in ots if o.get("id")==sel.get("work_order_id")),None)
                        if ot: store.update("work_orders",ot["id"],{"paid_amount":max(0,as_float(ot.get("paid_amount"))-as_float(sel.get("amount")))},actor,f"Revirtió imputación por anulación financiera")
                    store.update("financial_moves",sel["id"],{"voided":True,"void_reason":reason.strip(),"void_date":date.today().isoformat()},actor,f"ANULÓ movimiento {money(sel.get('amount'))}: {reason.strip()}")
                    st.success("Movimiento anulado con trazabilidad."); st.rerun()
        else: empty_state("Sin movimientos anulables","No hay movimientos activos.")

from __future__ import annotations

import html
import streamlit as st

from core import money


def card(title: str, value: str, subtitle: str = "", kicker: str = ""):
    st.markdown(
        f'<div class="tos-card"><div class="tos-kicker">{html.escape(kicker)}</div><div class="tos-big">{html.escape(value)}</div><h4>{html.escape(title)}</h4><div class="tos-muted">{html.escape(subtitle)}</div></div>',
        unsafe_allow_html=True,
    )


def alert_box(title: str, detail: str, severity: str = "info"):
    st.markdown(
        f'<div class="tos-alert {severity}"><div class="tos-alert-title">{html.escape(title)}</div><div class="tos-alert-detail">{html.escape(detail)}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, detail: str):
    st.markdown(f'<div class="tos-empty"><b>{html.escape(title)}</b>{html.escape(detail)}</div>', unsafe_allow_html=True)


def progress(value: float, good_at: float = 1.0):
    value = max(0.0, value)
    display = min(value, 1.0)
    cls = "good" if value >= good_at else ("warn" if value >= good_at * .7 else "bad")
    st.markdown(f'<div class="tos-progress {cls}"><div style="width:{display*100:.1f}%"></div></div>', unsafe_allow_html=True)


def stage_card(ot: dict, balance: float, late: bool = False):
    number = int(ot.get("number", 0))
    cls = "bad" if late else ""
    st.markdown(
        f'''<div class="tos-stage"><div class="plate">{html.escape(ot.get("plate") or "SIN PATENTE")}</div>
        <div class="meta">OT #{number:05d} · {html.escape(ot.get("car") or "—")}</div>
        <div><span class="tos-pill {cls}">{html.escape(ot.get("priority") or "Normal")}</span><span class="tos-pill">{html.escape(ot.get("stage") or "")}</span></div>
        <div class="money">Saldo {html.escape(money(balance))}</div></div>''', unsafe_allow_html=True)

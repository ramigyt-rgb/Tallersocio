from __future__ import annotations

import streamlit as st
from utils import money


def metric_row(items: list[tuple[str, object, str | None]], columns: int | None = None):
    cols = st.columns(columns or len(items))
    for col, item in zip(cols, items):
        label, value, delta = item
        col.metric(label, value, delta=delta)


def card(title: str, value: str, subtitle: str = "", cls: str = ""):
    st.markdown(
        f'<div class="tos-card {cls}"><div class="tos-kicker">{title}</div><div class="tos-big">{value}</div><div class="tos-muted">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    return f'<span class="tos-pill">{status}</span>'


def money_value(value) -> str:
    return money(value)

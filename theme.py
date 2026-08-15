import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f4f5f6;
            --panel: #ffffff;
            --panel-2: #eceeef;
            --line: #d8dbde;
            --text: #171717;
            --muted: #6f7479;
            --dark: #232323;
            --good: #376b51;
            --warn: #8a6825;
            --bad: #8a3d3d;
        }
        .stApp { background: var(--bg); color: var(--text); }
        [data-testid="stSidebar"] { background: #e7e9eb; border-right: 1px solid #d5d8da; }
        [data-testid="stHeader"] { background: rgba(244,245,246,.92); }
        .block-container { padding-top: 1.35rem; padding-bottom: 3rem; max-width: 1550px; }
        h1,h2,h3,h4 { letter-spacing: -.025em; color: #171717; }
        h1 { font-size: 2.1rem !important; }
        h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.05rem !important; }
        div[data-testid="stMetric"] {
            background: #fff; border: 1px solid var(--line); border-radius: 18px;
            padding: 14px 16px; box-shadow: 0 4px 18px rgba(0,0,0,.035);
        }
        div[data-testid="stMetricLabel"] { color: var(--muted); }
        div[data-testid="stMetricValue"] { font-weight: 730; letter-spacing: -.03em; }
        div[data-testid="stForm"], div[data-testid="stExpander"] {
            background: #fff; border: 1px solid var(--line); border-radius: 18px;
        }
        .tos-card {
            background: #fff; border: 1px solid var(--line); border-radius: 20px;
            padding: 18px 18px; box-shadow: 0 5px 22px rgba(0,0,0,.035); height: 100%;
        }
        .tos-card h4 { margin: 0 0 .35rem 0; }
        .tos-kicker { color: #72777c; font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
        .tos-big { font-size: 1.75rem; line-height: 1.05; font-weight: 780; letter-spacing: -.04em; margin-top:.35rem; }
        .tos-muted { color: #74797e; font-size:.88rem; }
        .tos-pill { display:inline-block; padding: 5px 9px; border-radius:999px; background:#eceeef; color:#303337; font-size:.76rem; font-weight:700; }
        .tos-good { color: var(--good); }
        .tos-warn { color: var(--warn); }
        .tos-bad { color: var(--bad); }
        .tos-flow { display:flex; flex-wrap:wrap; gap:7px; margin:.35rem 0 1rem; }
        .tos-flow span { background:#e8eaec; border:1px solid #d6d9dc; border-radius:999px; padding:6px 10px; font-size:.74rem; font-weight:700; }
        .tos-stage-card { background:#fff; border:1px solid #dadddf; border-radius:16px; padding:12px; margin-bottom:10px; }
        .tos-stage-card .plate { font-weight:800; letter-spacing:.05em; }
        .tos-stage-card .car { color:#6e7378; font-size:.82rem; }
        .tos-alert { border-left:4px solid #7d4a4a; background:#fff; border-radius:12px; padding:12px 14px; border-top:1px solid #ddd; border-right:1px solid #ddd; border-bottom:1px solid #ddd; }
        .tos-section { margin-top: 1.05rem; margin-bottom: .35rem; }
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 12px; min-height: 42px; border: 1px solid #cfd3d6; font-weight: 700;
        }
        div.stButton > button[kind="primary"] { background:#232323; color:#fff; border-color:#232323; }
        [data-testid="stDataFrame"] { border:1px solid #d7dade; border-radius:14px; overflow:hidden; }
        .mode-demo { background:#f0ead8; color:#6c5729; padding:5px 9px; border-radius:999px; font-size:.72rem; font-weight:800; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def flow_strip() -> None:
    steps = ["LEAD", "COTIZACIÓN", "APROBADO", "TURNO", "INGRESO", "PRODUCCIÓN", "CONTROL", "ENTREGA", "COBRO", "RENTABILIDAD"]
    st.markdown('<div class="tos-flow">' + ''.join(f'<span>{s}</span>' for s in steps) + '</div>', unsafe_allow_html=True)

import streamlit as st


def apply_theme():
    st.markdown(r"""
    <style>
    :root{
      --bg:#f2f3f4;--panel:#ffffff;--panel2:#e8eaec;--panel3:#dfe2e4;--line:#d2d5d8;
      --text:#17191b;--muted:#6f7479;--dark:#202326;--good:#3f6b56;--warn:#8a6a2f;--bad:#8d4545;
      --shadow:0 10px 34px rgba(21,24,27,.055);
    }
    .stApp{background:linear-gradient(180deg,#f5f6f7 0,#eef0f1 100%);color:var(--text)}
    [data-testid="stSidebar"]{background:#e4e6e8;border-right:1px solid #cfd3d6}
    [data-testid="stSidebar"] .stRadio label{padding:.24rem .15rem}
    [data-testid="stHeader"]{background:rgba(245,246,247,.88);backdrop-filter:blur(10px)}
    .block-container{padding-top:1.05rem;padding-bottom:4rem;max-width:1640px}
    h1,h2,h3,h4{letter-spacing:-.035em;color:#17191b}
    h1{font-size:2.2rem!important;margin-bottom:.15rem!important} h2{font-size:1.45rem!important} h3{font-size:1.08rem!important}
    div[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:15px 16px;box-shadow:var(--shadow)}
    div[data-testid="stMetricLabel"]{color:var(--muted);font-weight:650} div[data-testid="stMetricValue"]{font-weight:790;letter-spacing:-.04em}
    div[data-testid="stForm"],div[data-testid="stExpander"]{background:#fff;border:1px solid var(--line);border-radius:18px;box-shadow:0 5px 22px rgba(0,0,0,.025)}
    [data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden;background:#fff}
    div.stButton>button,div.stDownloadButton>button{border-radius:12px;min-height:42px;border:1px solid #c7cbcf;font-weight:740;background:#fff}
    div.stButton>button[kind="primary"]{background:#202326;color:#fff;border-color:#202326}
    div.stButton>button:hover,div.stDownloadButton>button:hover{border-color:#8e949a;color:#111}
    .tos-brand{font-weight:850;font-size:1.34rem;letter-spacing:-.04em}.tos-brand small{font-size:.65rem;color:#767b80;letter-spacing:.08em;margin-left:.35rem}
    .tos-badge{display:inline-flex;align-items:center;padding:5px 9px;border-radius:999px;background:#d8dbde;border:1px solid #c8ccd0;font-size:.70rem;font-weight:800;color:#34383b}
    .tos-flow{display:flex;flex-wrap:wrap;gap:6px;margin:.6rem 0 1.05rem}.tos-flow span{background:#e7e9eb;border:1px solid #d2d5d8;border-radius:999px;padding:6px 10px;font-size:.69rem;font-weight:780;color:#3c4145}.tos-flow span.active{background:#202326;color:#fff;border-color:#202326}
    .tos-card{background:#fff;border:1px solid var(--line);border-radius:20px;padding:18px;box-shadow:var(--shadow);height:100%}.tos-kicker{font-size:.69rem;font-weight:820;letter-spacing:.09em;text-transform:uppercase;color:#777d82}.tos-big{font-size:1.7rem;font-weight:820;letter-spacing:-.045em;margin:.35rem 0}.tos-muted{color:#72777c;font-size:.84rem}.tos-sep{height:1px;background:#e1e3e5;margin:14px 0}
    .tos-alert{background:#fff;border:1px solid #d7dadd;border-left:4px solid #6f7479;border-radius:14px;padding:12px 14px;margin:.45rem 0}.tos-alert.critical{border-left-color:#8d4545}.tos-alert.warning{border-left-color:#92723a}.tos-alert.info{border-left-color:#66737f}.tos-alert-title{font-weight:800}.tos-alert-detail{font-size:.82rem;color:#71767b;margin-top:2px}
    .tos-stage{background:#fff;border:1px solid #d6d9dc;border-radius:16px;padding:13px;margin:.45rem 0;box-shadow:0 4px 16px rgba(0,0,0,.025)}.tos-stage .plate{font-size:1rem;font-weight:850;letter-spacing:.05em}.tos-stage .meta{color:#70757a;font-size:.78rem;margin-top:3px}.tos-stage .money{font-weight:760;margin-top:8px}
    .tos-pill{display:inline-block;background:#e9ebed;border:1px solid #d8dbde;color:#35393c;border-radius:999px;padding:4px 8px;font-size:.68rem;font-weight:760;margin:2px 2px 2px 0}.tos-pill.bad{background:#f2e6e6;color:#7b3d3d;border-color:#e4caca}.tos-pill.good{background:#e4eee8;color:#396149;border-color:#cfe0d5}.tos-pill.warn{background:#f2ecdF;color:#7c612e;border-color:#e4d8bd}
    .tos-progress{height:10px;border-radius:999px;background:#e1e3e5;overflow:hidden}.tos-progress>div{height:100%;background:#262a2d;border-radius:999px}.tos-progress.good>div{background:#4c6f5b}.tos-progress.warn>div{background:#8b6b31}.tos-progress.bad>div{background:#8d4545}
    .tos-empty{border:1px dashed #c7cbcf;border-radius:18px;padding:30px;text-align:center;background:rgba(255,255,255,.55);color:#6d7277}.tos-empty b{display:block;color:#34383c;margin-bottom:4px}
    .tos-hero{background:#202326;color:white;border-radius:22px;padding:20px 22px;box-shadow:0 16px 40px rgba(20,22,24,.13)}.tos-hero .label{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:#b9bec3;font-weight:800}.tos-hero .value{font-size:2rem;font-weight:850;letter-spacing:-.05em;margin:.2rem 0}.tos-hero .sub{color:#c9cdd1;font-size:.86rem}
    .tos-table-note{font-size:.77rem;color:#757a7f}.tos-ok{color:#3f6b56}.tos-warn{color:#8a6a2f}.tos-bad{color:#8d4545}
    section[data-testid="stSidebar"] .block-container{padding-top:1rem}
    </style>
    """, unsafe_allow_html=True)


def page_title(title: str, subtitle: str = ""):
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def flow_strip(active: str | None = None):
    steps = ["LEAD","COTIZACIÓN","APROBADO","TURNO","INGRESO","PRODUCCIÓN","CONTROL","ENTREGA","COBRO","RENTABILIDAD"]
    html = '<div class="tos-flow">' + ''.join(f'<span class="{"active" if s==active else ""}">{s}</span>' for s in steps) + '</div>'
    st.markdown(html, unsafe_allow_html=True)

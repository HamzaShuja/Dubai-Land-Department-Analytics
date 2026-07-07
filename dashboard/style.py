"""Shared visual styling for the dashboard.

Provides one CSS injection plus small helpers (branded sidebar, page header,
metric cards, section headers, a Plotly theme, and an English-display transform)
so all pages share a clean, professional look - white cards, an emerald accent,
soft shadows and rounded corners.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from realestate.translation import developer_display, project_type_display  # noqa: E402

# ---- Palette ---------------------------------------------------------------
PRIMARY = "#1B7A52"
PRIMARY_DARK = "#14603F"
PRIMARY_SOFT = "#E7F2EC"
ACCENT = "#16A34A"
INK = "#16242B"
MUTED = "#6B7785"
BG = "#F4F6F8"
CARD = "#FFFFFF"
BORDER = "#E9EDF0"
GREEN_SEQ = ["#1B7A52", "#2E9E6B", "#57B98A", "#86D0AC", "#BFE6D3"]

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: {INK};
}}
.stApp {{ background: {BG}; }}

/* Hide default Streamlit chrome (menu, footer, deploy toolbar) - but KEEP the
   header strip and the sidebar open/close controls, so the nav can always be
   reopened after collapsing it. */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent; height: 2.4rem; box-shadow: none; }}

/* The "reopen sidebar" control (shown top-left when the sidebar is collapsed) */
[data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] {{
    display: flex !important; visibility: visible !important; opacity: 1 !important;
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
    box-shadow: 0 1px 4px rgba(16,36,43,.12); color: {PRIMARY_DARK};
}}
[data-testid="stSidebarCollapsedControl"]:hover, [data-testid="stExpandSidebarButton"]:hover {{
    background: {PRIMARY_SOFT};
}}
/* The sidebar's own collapse chevron stays visible too */
[data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"] {{
    display: flex !important; visibility: visible !important;
}}

/* Main content width + padding */
.block-container {{ padding: 1.6rem 2.4rem 3rem 2.4rem; max-width: 1500px; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: {CARD}; border-right: 1px solid {BORDER}; }}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}
[data-testid="stSidebarNav"] a {{ border-radius: 10px; }}
[data-testid="stSidebarNav"] a:hover {{ background: {PRIMARY_SOFT}; }}

/* Brand block */
.re-brand {{ display:flex; align-items:center; gap:.6rem; padding:.2rem .2rem 1rem .2rem; }}
.re-brand .logo {{
    width:38px; height:38px; border-radius:11px;
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:20px; font-weight:800;
}}
.re-brand .name {{ font-weight:800; font-size:1.02rem; line-height:1.05; color:{INK}; }}
.re-brand .sub {{ font-size:.70rem; color:{MUTED}; font-weight:600; letter-spacing:.04em; text-transform:uppercase; }}

/* Page header */
.re-head h1 {{ font-size:1.7rem; font-weight:800; margin:0 0 .15rem 0; color:{INK}; }}
.re-head p {{ color:{MUTED}; margin:0 0 .2rem 0; font-size:.95rem; }}

/* Section header */
.re-section {{ font-size:1.05rem; font-weight:700; color:{INK}; margin:.4rem 0 .2rem 0;
    display:flex; align-items:center; gap:.5rem; }}
.re-section .bar {{ width:4px; height:18px; border-radius:3px; background:{PRIMARY}; display:inline-block; }}

/* Metric cards */
.re-kpi {{
    background:{CARD}; border:1px solid {BORDER}; border-radius:16px; padding:1.1rem 1.2rem;
    box-shadow:0 1px 3px rgba(16,36,43,.04); height:100%;
}}
.re-kpi .lbl {{ font-size:.78rem; color:{MUTED}; font-weight:600; text-transform:uppercase; letter-spacing:.03em; }}
.re-kpi .val {{ font-size:2rem; font-weight:800; color:{INK}; line-height:1.1; margin-top:.25rem; }}
.re-kpi .dlt {{ font-size:.8rem; font-weight:600; margin-top:.35rem; }}
.re-kpi .dlt.up {{ color:{PRIMARY}; }}
.re-kpi .dlt.muted {{ color:{MUTED}; }}
.re-kpi.primary {{ background:linear-gradient(150deg,{PRIMARY},{PRIMARY_DARK}); border:none; }}
.re-kpi.primary .lbl, .re-kpi.primary .val {{ color:#fff; }}
.re-kpi.primary .dlt {{ color:#CFEBDD; }}
.re-kpi .ico {{ float:right; font-size:1.1rem; opacity:.85; }}

/* Buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
    border-radius:10px; font-weight:600; border:1px solid {BORDER};
}}
.stFormSubmitButton > button {{
    background:{PRIMARY}; color:#fff; border:none; padding:.5rem 1.4rem;
}}
.stFormSubmitButton > button:hover {{ background:{PRIMARY_DARK}; color:#fff; }}

/* Inputs */
[data-testid="stForm"] {{ background:{CARD}; border:1px solid {BORDER}; border-radius:16px; padding:1.2rem 1.3rem; }}
[data-baseweb="select"] > div, .stTextInput input {{ border-radius:10px; }}

/* Dataframes & tabs */
[data-testid="stDataFrame"] {{ border:1px solid {BORDER}; border-radius:12px; }}
.stTabs [data-baseweb="tab-list"] {{ gap:.3rem; }}
.stTabs [data-baseweb="tab"] {{ border-radius:9px 9px 0 0; font-weight:600; }}

/* Result cards on predictor */
.re-result {{ background:{CARD}; border:1px solid {BORDER}; border-radius:16px; padding:1.3rem;
    box-shadow:0 1px 3px rgba(16,36,43,.04); }}
.re-result .big {{ font-size:2.6rem; font-weight:800; color:{PRIMARY}; line-height:1; }}
.re-badge {{ display:inline-block; padding:.3rem .8rem; border-radius:999px; font-weight:600; font-size:.85rem;
    background:{PRIMARY_SOFT}; color:{PRIMARY_DARK}; margin-top:.5rem; }}

/* Explore cards: st.page_link rendered as clickable cards */
[data-testid="stPageLink"] a, a[data-testid="stPageLink-NavLink"] {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px;
    padding: .65rem .9rem; font-weight: 700; color: {INK} !important;
    width: 100%; box-shadow: 0 1px 3px rgba(16,36,43,.04);
    transition: background .12s ease, border-color .12s ease;
}}
[data-testid="stPageLink"] a:hover, a[data-testid="stPageLink-NavLink"]:hover {{
    background: {PRIMARY_SOFT}; border-color: {PRIMARY};
}}

/* Active page in the sidebar nav */
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: {PRIMARY_SOFT}; font-weight: 700;
}}
[data-testid="stSidebarNav"] a[aria-current="page"] span {{ color: {PRIMARY_DARK}; }}

/* Subtle lift on cards */
.re-kpi, .re-result {{ transition: box-shadow .15s ease, transform .15s ease; }}
.re-kpi:hover {{ box-shadow: 0 4px 14px rgba(16,36,43,.08); }}

/* Hide Plotly's floating modebar for a cleaner read */
.modebar {{ display: none !important; }}

/* Nicer focus states */
.stButton > button:focus, .stDownloadButton > button:focus,
.stFormSubmitButton > button:focus {{
    outline: 2px solid {PRIMARY}; outline-offset: 2px; box-shadow: none;
}}

/* Loading spinner accent */
[data-testid="stSpinner"] i {{ border-top-color: {PRIMARY} !important; }}

/* Responsive: tighten padding and type on narrow screens */
@media (max-width: 1100px) {{
    .block-container {{ padding: 1.1rem 1.2rem 2.2rem 1.2rem; }}
}}
@media (max-width: 700px) {{
    .block-container {{ padding: .8rem .8rem 2rem .8rem; }}
    .re-head h1 {{ font-size: 1.35rem; }}
    .re-kpi .val {{ font-size: 1.45rem; }}
    .re-result .big {{ font-size: 2rem; }}
}}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def sidebar_reopen_shim() -> None:
    """Mount a floating arrow on the page that reopens the sidebar.

    Streamlit's built-in reopen control is unreliable once the default header
    chrome is customised, so this adds our own button to the parent document.
    It appears only while the sidebar is collapsed and programmatically clicks
    whatever native expand control the running Streamlit version provides."""
    import streamlit.components.v1 as components

    components.html("""
    <script>
    const doc = window.parent.document;
    if (!doc.getElementById('re-sb-open')) {
        const btn = doc.createElement('button');
        btn.id = 're-sb-open';
        btn.title = 'Open navigation';
        btn.textContent = '\u276F';
        Object.assign(btn.style, {
            position: 'fixed', top: '0.7rem', left: '0.7rem', zIndex: '9999999',
            width: '2.3rem', height: '2.3rem', display: 'none',
            alignItems: 'center', justifyContent: 'center',
            background: '#FFFFFF', color: '#14603F',
            border: '1px solid #E9EDF0', borderRadius: '10px',
            boxShadow: '0 2px 8px rgba(16,36,43,.16)', cursor: 'pointer',
            fontSize: '1rem', fontWeight: '700', padding: '0'
        });
        btn.addEventListener('mouseenter', () => { btn.style.background = '#E7F2EC'; });
        btn.addEventListener('mouseleave', () => { btn.style.background = '#FFFFFF'; });
        btn.addEventListener('click', () => {
            const sels = [
                '[data-testid="stSidebarCollapsedControl"] button',
                '[data-testid="stSidebarCollapsedControl"]',
                'button[data-testid="stExpandSidebarButton"]',
                '[data-testid="stExpandSidebarButton"]',
                '[data-testid="stHeader"] button'
            ];
            for (const s of sels) {
                const el = doc.querySelector(s);
                if (el) { el.click(); return; }
            }
        });
        doc.body.appendChild(btn);
        const update = () => {
            const sb = doc.querySelector('[data-testid="stSidebar"]');
            const open = sb && sb.offsetWidth > 100 &&
                         getComputedStyle(sb).visibility !== 'hidden';
            btn.style.display = open ? 'none' : 'flex';
        };
        setInterval(update, 400);
        update();
    }
    </script>""", height=0, width=0)


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="re-brand">
          <div class="logo">🏙️</div>
          <div>
            <div class="name">Dubai RE Analytics</div>
            <div class="sub">Market Intelligence</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="re-head"><h1>{title}</h1>'
        + (f"<p>{subtitle}</p>" if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="re-section"><span class="bar"></span>{title}</div>',
                unsafe_allow_html=True)


def metric_card(col, label: str, value, delta: str = "", primary: bool = False,
                delta_kind: str = "up", icon: str = "") -> None:
    cls = "re-kpi primary" if primary else "re-kpi"
    ico = f'<span class="ico">{icon}</span>' if icon else ""
    dlt = f'<div class="dlt {delta_kind}">{delta}</div>' if delta else ""
    col.markdown(
        f'<div class="{cls}">{ico}<div class="lbl">{label}</div>'
        f'<div class="val">{value}</div>{dlt}</div>',
        unsafe_allow_html=True,
    )


def style_plotly(fig, height: int | None = None):
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        colorway=GREEN_SEQ,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=BORDER)
    if height:
        fig.update_layout(height=height)
    return fig


def to_english(df):
    """Return a copy with Arabic developer / project-type / project-name columns
    rendered in English for display."""
    out = df.copy()
    if "developer_name" in out.columns:
        out["developer_name"] = out["developer_name"].map(developer_display)
    if "project_type" in out.columns:
        out["project_type"] = out["project_type"].map(project_type_display)
    if "project_name" in out.columns:
        # Arabic free-text project names have no faithful English rendering;
        # drop them rather than show vowel-less transliteration noise.
        out = out.drop(columns=["project_name"])
    if "master_project_en" in out.columns:
        out = out.rename(columns={"master_project_en": "master_project"})
    return out


def bootstrap_page(title: str, subtitle: str = "", icon: str = "🏙️") -> None:
    """Per-page header. CSS + sidebar brand are applied once by the entrypoint."""
    page_header(title, subtitle)


def callout(title: str, body: str, kind: str = "insight") -> None:
    """Insight / risk highlight box with a left accent bar."""
    palette = {
        "insight": (PRIMARY, PRIMARY_SOFT, "💡"),
        "risk": ("#C4562A", "#FBEEE6", "⚠️"),
        "info": (MUTED, "#EEF1F4", "ℹ️"),
    }
    accent, bg, icon = palette.get(kind, palette["insight"])
    st.markdown(
        f'<div style="background:{bg};border-left:4px solid {accent};'
        f'border-radius:10px;padding:.85rem 1.05rem;margin:.2rem 0 .8rem 0">'
        f'<div style="font-weight:700;color:{INK};font-size:.95rem">{icon}&nbsp; {title}</div>'
        f'<div style="color:{INK};font-size:.88rem;margin-top:.15rem;opacity:.85">{body}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def coverage_note(text: str) -> None:
    st.markdown(
        f'<div style="color:{MUTED};font-size:.78rem;margin-top:.4rem">🛈 {text}</div>',
        unsafe_allow_html=True,
    )

"""Shared visual styling for the dashboard.

Provides one CSS injection plus small helpers (branded sidebar, page header,
metric cards, section headers, a Plotly theme, and an English-display transform)
so all pages share a clean, professional look — white cards, an emerald accent,
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

/* Hide default Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}

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
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


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

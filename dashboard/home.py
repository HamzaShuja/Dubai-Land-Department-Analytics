"""Home dashboard - market intelligence at a glance."""
import streamlit as st
from bootstrap import load_data
import style
import plotly.express as px
from realestate.analysis import market
from realestate.analysis import market_intel as mi
from realestate.analysis.projects_analysis import offplan_vs_ready

style.bootstrap_page(
    "Market Intelligence Dashboard",
    "Momentum, forward supply and delivery-risk across Dubai's real-estate market.",
)

tx, pr, source = load_data()

mom = mi.market_momentum(tx)
risk = mi.delivery_risk_exposure(pr)
pipe = mi.supply_pipeline(pr)
cov = mi.coverage(tx)
offplan_units = int(pr.loc[pr["is_offplan"], "no_of_units"].sum())
total_units = int(pr["no_of_units"].sum())
delivery_rate = pr["is_delivered"].mean() * 100

# ---- KPI row (decision-grade) ----------------------------------------------
c1, c2, c3, c4 = st.columns(4)
style.metric_card(c1, f"Sales value · {mom.period_label}", f"AED {mom.value_aed/1e9:.0f}B",
                  primary=True, icon="💰",
                  delta=("Record high · " if mom.all_time_high else "")
                        + f"{mom.cagr_pct:.0f}%/yr since {mom.first_label}")
style.metric_card(c2, "Supply pipeline", f"{offplan_units/1000:.0f}k units", icon="🏗️",
                  delta=f"{offplan_units/total_units*100:.0f}% of all tracked units")
style.metric_card(c3, "Delivery-risk exposure", f"{risk['at_risk_units']/1000:.0f}k units",
                  icon="⚠️", delta=f"{risk['at_risk_share']:.0f}% of pipeline <30% built",
                  delta_kind="muted")
wl = mi.overdue_watchlist(pr)
style.metric_card(c4, "Stalled projects", f"{wl['n_zombie']}", icon="🚨",
                  delta=f"{wl['zombie_units']/1000:.0f}k units overdue & <30% built",
                  delta_kind="muted")

# ---- Headline insight -------------------------------------------------------
peak = pipe.loc[pipe["units"].idxmax()] if len(pipe) else None
peak_txt = (f" Supply peaks in {int(peak['end_year'])} with ~{peak['units']/1000:.0f}k units due."
            if peak is not None else "")
style.callout(
    "Record market, heavy forward supply, early-stage risk",
    f"Quarterly sales hit an all-time high of AED {mom.value_aed/1e9:.0f}B "
    f"({mom.cagr_pct:.0f}%/yr since {mom.first_label}). "
    f"{offplan_units/1000:.0f}k units are in the pipeline, but {risk['at_risk_share']:.0f}% "
    f"of them sit in projects less than 30% built - a delivery-timing risk to watch.{peak_txt}",
)

# ---- Supply pipeline + inventory mix ---------------------------------------
left, right = st.columns([2, 1])
with left:
    style.section("Forward supply - units by expected completion year")
    fig = px.bar(pipe, x="end_year", y="units",
                 labels={"units": "Off-plan units", "end_year": ""})
    fig.update_traces(marker_color=style.PRIMARY)
    st.plotly_chart(style.style_plotly(fig, height=300), width="stretch")
with right:
    style.section("Inventory mix")
    ovr = offplan_vs_ready(pr)
    fig2 = px.pie(ovr, names="segment", values="n_projects", hole=0.62,
                  color_discrete_sequence=[style.PRIMARY, style.GREEN_SEQ[2]])
    fig2.update_traces(textinfo="percent+label")
    st.plotly_chart(style.style_plotly(fig2, height=300), width="stretch")

# ---- Price index ------------------------------------------------------------
style.section("Dubai Price Index by property type (base = 100)")
idx = market.price_index(tx, "Sales")
fig3 = px.line(idx, x="period_label", y="index_value", color="property_type",
               labels={"index_value": "Index", "period_label": "", "property_type": ""})
st.plotly_chart(style.style_plotly(fig3, height=300), width="stretch")

# ---- Explore + governance ---------------------------------------------------
style.section("Explore")
pages = [
    ("📈", "Market Overview", "Volume, value & the Dubai Price Index.", "pages/1_Market_Overview.py"),
    ("🗺️", "Geospatial Map", "Activity & risk across communities.", "pages/2_Geospatial_Map.py"),
    ("🤖", "Delivery Predictor", "Delivery-risk prediction with SHAP.", "pages/3_Delivery_Predictor.py"),
    ("🚨", "Delivery Watchlist", "Overdue projects & developer reliability.", "pages/6_Delivery_Watchlist.py"),
    ("🔮", "Market Forecast", "Prophet 12-month outlook.", "pages/4_Market_Forecast.py"),
    ("🧭", "District Intelligence", "Tiers, concentration & anomalies.", "pages/5_District_Intelligence.py"),
]
for col, (ico, name, desc, path) in zip(st.columns(len(pages)), pages):
    with col:
        st.page_link(path, label=name, icon=ico)
        st.caption(desc)
st.write("")
style.coverage_note(
    f"Source: Dubai Pulse · Dubai Land Department (DLD). Market data {cov['label']}"
    + (f" ({cov['note']})." if cov["note"] else ".")
    + f" Served via {'PostgreSQL (Neon)' if source == 'database' else 'local workbook'}."
)

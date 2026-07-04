import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

from bootstrap import load_data, df_download_button
import style
from realestate.analysis import market_intel as mi
from realestate.translation import developer_display

style.bootstrap_page(
    "Delivery Watchlist",
    "Projects already past their planned completion date, the developers behind them, "
    "and how much of the stated supply pipeline is actually credible.",
)

_, pr, _ = load_data()
wl = mi.overdue_watchlist(pr)
watch = style.to_english(wl["watchlist"])

# ---- Headline exposure ------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
style.metric_card(k1, "Overdue projects", f"{wl['n_overdue']}",
                  delta="past planned end date, unfinished", delta_kind="muted", icon="⏰")
style.metric_card(k2, "Units stuck overdue", f"{wl['overdue_units']/1000:.0f}k",
                  delta="buyers waiting beyond promised date", delta_kind="muted", icon="📦")
style.metric_card(k3, "Stalled (zombie) projects", f"{wl['n_zombie']}", primary=True,
                  delta=f"overdue and <{wl['threshold']:.0f}% built", delta_kind="muted", icon="🚨")
style.metric_card(k4, "Units in stalled projects", f"{wl['zombie_units']/1000:.0f}k",
                  delta="unlikely to deliver without re-planning", delta_kind="muted", icon="⚠️")

style.callout(
    "Where delivery promises are already broken",
    f"{wl['n_overdue']} off-plan projects ({wl['overdue_units']:,} units) have blown through "
    f"their planned completion dates. {wl['n_zombie']} of them are stalled — overdue and less "
    f"than {wl['threshold']:.0f}% built — trapping {wl['zombie_units']:,} units. "
    "These, not new launches, are where buyer and lender risk is concentrated today.",
    kind="risk",
)

# ---- Credibility-weighted pipeline ------------------------------------------
style.section("Stated pipeline vs build progress")
rp = mi.realistic_pipeline(pr)
fig = px.bar(rp, x="end_year", y="units", color="progress_band",
             color_discrete_map={"<30% built": "#C4562A",
                                 "30–70% built": "#E3B341",
                                 ">70% built": style.PRIMARY},
             labels={"units": "Off-plan units", "end_year": "Promised completion year",
                     "progress_band": ""})
st.plotly_chart(style.style_plotly(fig, height=340), width="stretch")
near = rp[rp["end_year"] <= 2027]
near_risky = near.loc[near["progress_band"] == "<30% built", "units"].sum()
near_total = near["units"].sum()
if near_total:
    st.caption(f"Of the {near_total:,.0f} units promised by end-2027, "
               f"{near_risky:,.0f} ({near_risky/near_total*100:.0f}%) sit in projects "
               f"less than 30% built — schedule slippage is almost certain for most of them.")

# ---- Developer reliability ---------------------------------------------------
style.section("Developer reliability (10+ tracked projects)")
rel = mi.developer_reliability(pr)
rel["developer"] = rel["developer_name"].map(developer_display)
c1, c2 = st.columns(2)
with c1:
    top = rel.head(8).sort_values("reliability_score")
    fig = px.bar(top, x="reliability_score", y="developer", orientation="h",
                 labels={"reliability_score": "Reliability score (0–100)", "developer": ""})
    fig.update_traces(marker_color=style.PRIMARY)
    st.plotly_chart(style.style_plotly(fig, height=300), width="stretch")
    st.caption("Most reliable — high delivery rate, little overdue stock.")
with c2:
    bot = rel.tail(8).sort_values("reliability_score")
    fig = px.bar(bot, x="reliability_score", y="developer", orientation="h",
                 labels={"reliability_score": "Reliability score (0–100)", "developer": ""})
    fig.update_traces(marker_color="#C4562A")
    st.plotly_chart(style.style_plotly(fig, height=300), width="stretch")
    st.caption("Least reliable — chronic overruns or stalled portfolios.")

show = rel[["developer", "n_projects", "total_units", "delivered_rate",
            "avg_completion", "overdue_projects", "overdue_units", "reliability_score"]]
st.dataframe(show, width="stretch", height=280)
df_download_button(show, "⬇️  Export reliability scores (CSV)", "developer_reliability.csv")

# ---- The watchlist itself ----------------------------------------------------
style.section("Overdue project watchlist")
f1, f2, f3 = st.columns([1.2, 1.2, 1])
dev_opts = ["All developers"] + sorted(watch["developer_name"].dropna().unique())
area_opts = ["All areas"] + sorted(watch["area_name_en"].dropna().unique())
dev_pick = f1.selectbox("Developer", dev_opts)
area_pick = f2.selectbox("Area", area_opts)
only_zombie = f3.toggle("Stalled only", value=False)

view = watch.copy()
if dev_pick != "All developers":
    view = view[view["developer_name"] == dev_pick]
if area_pick != "All areas":
    view = view[view["area_name_en"] == area_pick]
if only_zombie:
    view = view[view["is_zombie"]]
st.write(f"**{len(view)}** projects · **{int(view['no_of_units'].sum()):,}** units")
st.dataframe(view.round(1), width="stretch", height=340)
df_download_button(view, "⬇️  Export watchlist (CSV)", "delivery_watchlist.csv")

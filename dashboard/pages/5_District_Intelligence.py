import streamlit as st
from bootstrap import load_data, df_download_button
import style
import plotly.express as px

from realestate.models.segmentation import segment_areas
from realestate.analysis import anomaly, stats_tests
from realestate.analysis import market_intel as mi
from realestate.translation import developer_display

style.bootstrap_page("District Intelligence",
                     "Market structure, delivery-risk exposure, investment tiers and anomalies.")

tx, pr, _ = load_data()

# ---- Market structure -------------------------------------------------------
style.section("Market structure")
devc = mi.developer_concentration(pr, 5)
areac = mi.area_concentration(pr, 5)
risk = mi.delivery_risk_exposure(pr)
k1, k2, k3, k4 = st.columns(4)
style.metric_card(k1, "Top-5 developer share", f"{devc['top_n_share']:.0f}%",
                  delta="of all units", delta_kind="muted", icon="🏢")
style.metric_card(k2, "Top-5 area share", f"{areac['top_n_share']:.0f}%",
                  delta="of all units", delta_kind="muted", icon="📍")
style.metric_card(k3, "Pipeline at risk", f"{risk['at_risk_units']/1000:.0f}k units",
                  delta=f"{risk['at_risk_share']:.0f}% of pipeline <30% built", delta_kind="muted", icon="⚠️")
hhi = devc["hhi"]
style.metric_card(k4, "Developer HHI", f"{hhi:.0f}",
                  delta="competitive" if hhi < 1500 else "concentrated", delta_kind="muted", icon="⚖️")

style.callout(
    "Fragmented market, risk concentrated in early-stage supply",
    f"The top 5 developers hold {devc['top_n_share']:.0f}% of units (HHI {hhi:.0f}, a competitive market), "
    f"but {risk['at_risk_share']:.0f}% of the off-plan pipeline is under 30% built - "
    "so delivery risk is concentrated in newer launches rather than any single developer.",
    kind="risk",
)

cA, cB = st.columns(2)
with cA:
    style.section("Delivery-risk exposure by area")
    ar = mi.at_risk_by_area(pr, n=10)
    fig = px.bar(ar.sort_values("at_risk_units"), x="at_risk_units", y="area_name_en",
                 orientation="h", labels={"at_risk_units": "Off-plan units <30% built", "area_name_en": ""})
    fig.update_traces(marker_color="#C4562A")
    st.plotly_chart(style.style_plotly(fig, height=320), width="stretch")
with cB:
    style.section("Top developers by units")
    tops = [(developer_display(n), u) for n, u, _ in devc["top"]]
    import pandas as pd
    td = pd.DataFrame(tops, columns=["Developer", "Units"]).sort_values("Units")
    fig = px.bar(td, x="Units", y="Developer", orientation="h")
    fig.update_traces(marker_color=style.PRIMARY)
    st.plotly_chart(style.style_plotly(fig, height=320), width="stretch")

# ---- Investment tiers -------------------------------------------------------
style.section("Investment tiers (KMeans)")
seg = segment_areas(pr)
order = sorted(seg["investment_tier"].unique())
fig = px.scatter(seg, x="avg_completion", y="delivery_rate", size="total_units",
                 color="investment_tier", hover_name="area_name_en",
                 color_discrete_sequence=style.GREEN_SEQ,
                 category_orders={"investment_tier": order},
                 labels={"avg_completion": "Avg completion %", "delivery_rate": "Delivery rate %", "investment_tier": ""})
st.plotly_chart(style.style_plotly(fig, height=360), width="stretch")
st.dataframe(seg[["area_name_en", "investment_tier", "n_projects", "total_units",
                  "avg_completion", "delivery_rate", "n_developers"]].round(1),
             width="stretch", height=260)
df_download_button(seg, "⬇️  Export tiers (CSV)", "investment_tiers.csv")

# ---- Anomalies --------------------------------------------------------------
style.section("Anomaly detection (Isolation Forest)")
t1, t2 = st.tabs(["Market anomalies", "Project anomalies"])
with t1:
    ta = anomaly.detect_transaction_anomalies(tx)
    st.write(f"**{int(ta['is_anomaly'].sum())}** unusual quarter / property-type observations flagged.")
    st.dataframe(ta[ta["is_anomaly"]][["period_label", "property_type", "transaction_group",
                                       "value_aed", "count", "avg_value_per_txn", "anomaly_score"]].round(2),
                 width="stretch")
with t2:
    pa = anomaly.detect_project_anomalies(pr)
    st.write(f"**{int(pa['is_anomaly'].sum())}** unusual projects flagged.")
    st.dataframe(style.to_english(pa[pa["is_anomaly"]]).round(2), width="stretch", height=280)

# ---- Hypothesis tests -------------------------------------------------------
style.section("Statistical hypothesis tests")
c1, c2 = st.columns(2)
types = ["Units", "Building", "Land", "Villa"]
ta_ = c1.selectbox("Property type A", types, index=3)
tb_ = c2.selectbox("Property type B", types, index=0)
res = stats_tests.compare_property_type_prices(tx, ta_, tb_)
m1, m2, m3, m4 = st.columns(4)
style.metric_card(m1, "Welch t-test p", f"{res.t_pvalue:.2g}")
style.metric_card(m2, "Mann-Whitney p", f"{res.mw_pvalue:.2g}")
style.metric_card(m3, "Cohen's d", f"{res.cohens_d:.2f}")
style.metric_card(m4, "Significant (5%)", "Yes" if res.significant_5pct else "No",
                  primary=res.significant_5pct)
res2 = stats_tests.compare_offplan_vs_ready_completion(pr)
st.caption(f"Off-plan vs ready completion - mean off-plan {res2.mean_a:.1f}% vs ready {res2.mean_b:.1f}%; "
           f"t-test p = {res2.t_pvalue:.2g}, "
           f"{'significant' if res2.significant_5pct else 'not significant'} at 5%.")

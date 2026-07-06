import streamlit as st
from bootstrap import load_data, df_download_button
import style
import plotly.express as px
from realestate.analysis import market
from realestate.analysis import market_intel as mi

style.bootstrap_page("Market Overview",
                     "Transaction momentum, value trends and the custom Dubai Price Index.")

tx, _, _ = load_data()
mom = mi.market_momentum(tx)
cov = mi.coverage(tx)

# ---- Momentum KPIs ----------------------------------------------------------
allsummary = market.transaction_summary(tx)
sales_all = allsummary[allsummary["transaction_group"] == "Sales"]
total_deals = sales_all["count"].sum()
c1, c2, c3, c4 = st.columns(4)
style.metric_card(c1, f"Sales value · {mom.period_label}", f"AED {mom.value_aed/1e9:.0f}B",
                  primary=True, delta="Record high" if mom.all_time_high else "", icon="💰")
style.metric_card(c2, f"QoQ vs {mom.last_comp_label}", f"{mom.last_comp_pct:+.0f}%",
                  delta="quarter-on-quarter value", delta_kind="up" if mom.last_comp_pct >= 0 else "muted", icon="📈")
style.metric_card(c3, "Growth since 2016", f"{mom.cagr_pct:.0f}%/yr",
                  delta=f"AED {mom.first_value/1e9:.0f}B → {mom.value_aed/1e9:.0f}B", delta_kind="up", icon="🚀")
style.metric_card(c4, f"Deals · {mom.period_label}", f"{mom.count:,.0f}",
                  delta="quarterly sales transactions", delta_kind="muted", icon="🧾")

style.callout(
    "Momentum at record levels",
    f"Sales value reached AED {mom.value_aed/1e9:.0f}B in {mom.period_label}, "
    f"{mom.last_comp_pct:+.0f}% versus {mom.last_comp_label} and compounding at "
    f"{mom.cagr_pct:.0f}% a year since {mom.first_label}.",
)

# ---- Filters ----------------------------------------------------------------
f = st.columns([1, 1, 2])
group = f[0].selectbox("Transaction group", ["Sales", "Mortgages", "Other"], index=0)
types = ["Units", "Building", "Land", "Villa"]
chosen = f[2].multiselect("Property types", types, default=types)

summary = market.transaction_summary(tx)
summary = summary[(summary["transaction_group"] == group)
                  & (summary["property_type"].isin(chosen))]

left, right = st.columns(2)
with left:
    style.section("Transaction volume over time")
    vol = (summary.groupby(["period_label", "period"], as_index=False)["count"].sum()
           .sort_values("period"))
    fig = px.bar(vol, x="period_label", y="count", labels={"count": "Transactions", "period_label": ""})
    fig.update_traces(marker_color=style.PRIMARY)
    st.plotly_chart(style.style_plotly(fig, height=300), width="stretch")
with right:
    style.section("Total value over time")
    val = (summary.groupby(["period_label", "period"], as_index=False)["value_aed"].sum()
           .sort_values("period"))
    fig = px.area(val, x="period_label", y="value_aed", labels={"value_aed": "Value (AED)", "period_label": ""})
    fig.update_traces(line_color=style.PRIMARY, fillcolor="rgba(27,122,82,.15)")
    st.plotly_chart(style.style_plotly(fig, height=300), width="stretch")

style.section("Custom Dubai Real Estate Price Index (base = 100)")
st.caption("Average sale value per transaction by property type, rebased to the first available quarter.")
idx = market.price_index(tx, group)
idx = idx[idx["property_type"].isin(chosen)]
fig = px.line(idx, x="period_label", y="index_value", color="property_type",
              labels={"index_value": "Index", "period_label": "", "property_type": ""})
st.plotly_chart(style.style_plotly(fig, height=320), width="stretch")

style.section("Filtered data")
st.dataframe(summary.round(2), width="stretch", height=280)
df_download_button(summary, "⬇️  Export filtered view (CSV)", "market_overview.csv")
style.coverage_note(f"Market data {cov['label']}" + (f" · {cov['note']}." if cov["note"] else "."))


# ---- Price signal: average ticket by property type ---------------------------
style.section("Price signal - average sale value per transaction")
tt = mi.ticket_trends(tx)
chips = st.columns(max(len(tt["summary"]), 1))
for col, (_, r) in zip(chips, tt["summary"].iterrows()):
    style.metric_card(col, r["property_type"], f"AED {r['latest']/1e6:.1f}M",
                      delta=f"{r['chg_4q_pct']:+.0f}% vs 4 quarters ago",
                      delta_kind="up" if r["chg_4q_pct"] >= 0 else "muted")
fig_t = px.line(tt["series"], x="period_label", y="avg_value_per_txn",
                color="property_type",
                labels={"avg_value_per_txn": "Avg value / transaction (AED)",
                        "period_label": "", "property_type": ""})
st.plotly_chart(style.style_plotly(fig_t, height=320), width="stretch")
st.caption("Buildings are a thin, lumpy segment (few very large deals per quarter) - "
           "read its swings with caution. Villas show the strongest sustained repricing.")

# ---- Credit profile: cash vs mortgage ----------------------------------------
style.section("Credit profile - how leveraged is the market?")
cp = mi.credit_profile(tx)
lc, rc = st.columns([2, 1])
with lc:
    fig_c = px.area(cp["series"], x="period_label", y="mortgage_to_sales",
                    labels={"mortgage_to_sales": "Mortgage value ÷ sales value",
                            "period_label": ""})
    fig_c.update_traces(line_color=style.PRIMARY,
                        fillcolor="rgba(27,122,82,.15)")
    fig_c.add_hline(y=1.0, line_dash="dot", line_color="#8A94A6",
                    annotation_text="mortgages = sales")
    st.plotly_chart(style.style_plotly(fig_c, height=300), width="stretch")
with rc:
    style.metric_card(st.container(), "Mortgage / sales value", f"{cp['latest']:.2f}",
                      primary=True, delta=f"latest · {cp['latest_label']}", delta_kind="muted")
    style.callout(
        "A cash-driven market",
        f"Mortgage registrations were {cp['early_avg']:.1f}× sales value in 2016 but only "
        f"{cp['recent_avg']:.2f}× over the last four reported quarters. Today's rally is "
        "financed largely with equity, not debt - a structurally healthier footing than "
        "the leveraged run-ups of the past.",
    )

# ---- Mix shift ----------------------------------------------------------------
style.section("Sales mix - where the money goes")
mix = mi.sales_mix(tx)
mix_l = mix.melt(id_vars=["period", "period_label"], var_name="property_type",
                 value_name="share")
fig_m = px.area(mix_l, x="period_label", y="share", color="property_type",
                groupnorm="percent",
                labels={"share": "Share of sales value (%)", "period_label": "",
                        "property_type": ""})
st.plotly_chart(style.style_plotly(fig_m, height=300), width="stretch")
first4 = mix.head(4).mean(numeric_only=True)
last4 = mix.tail(4).mean(numeric_only=True)
st.caption(f"Land deals made up {first4.get('Land', 0):.0f}% of sales value in 2016 but "
           f"{last4.get('Land', 0):.0f}% recently; apartments ({last4.get('Units', 0):.0f}%) "
           f"and villas ({last4.get('Villa', 0):.0f}%) now drive the market - "
           "end-user product has displaced land speculation.")

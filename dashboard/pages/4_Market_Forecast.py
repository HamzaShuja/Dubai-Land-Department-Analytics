import streamlit as st
from bootstrap import load_data
import style
import plotly.graph_objects as go

style.bootstrap_page("Market Forecast",
                     "Prophet forecast of average sale value per transaction, four quarters ahead.")

tx, _, _ = load_data()
ptype = st.selectbox("Property type", ["Units", "Building", "Land", "Villa"])


@st.cache_data(ttl=86400, show_spinner="Fitting Prophet model…")
def _forecast(ptype):
    from realestate.models.forecast import forecast_property_type
    return forecast_property_type(tx, ptype, periods=4)


try:
    fc = _forecast(ptype)
except Exception as exc:
    st.error(f"Could not forecast {ptype}: {exc}")
    st.stop()

hist = fc[~fc["is_forecast"]]
fut = fc[fc["is_forecast"]]

fig = go.Figure()
fig.add_trace(go.Scatter(x=fc["ds"], y=fc["yhat_upper"], mode="lines",
                         line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=fc["ds"], y=fc["yhat_lower"], mode="lines", fill="tonexty",
                         fillcolor="rgba(27,122,82,.18)", line=dict(width=0),
                         name="80% interval"))
fig.add_trace(go.Scatter(x=hist["ds"], y=hist["actual"], mode="markers+lines",
                         name="Actual", line=dict(color=style.INK, width=2)))
fig.add_trace(go.Scatter(x=fc["ds"], y=fc["yhat"], mode="lines", name="Forecast",
                         line=dict(color=style.PRIMARY, dash="dash", width=2)))
fig.update_layout(yaxis_title="Avg sale value per transaction (AED)", xaxis_title="")
st.plotly_chart(style.style_plotly(fig, height=420), width="stretch")

style.section("Forecast - next 4 quarters")
st.dataframe(fut[["ds", "yhat", "yhat_lower", "yhat_upper"]]
             .rename(columns={"ds": "Quarter", "yhat": "Forecast",
                              "yhat_lower": "Lower (80%)", "yhat_upper": "Upper (80%)"})
             .round(0), width="stretch")

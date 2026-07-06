"""Dubai Real Estate Analytics - entry point and navigation controller.

Run with:  streamlit run dashboard/app.py
"""
import streamlit as st

st.set_page_config(page_title="Dubai RE Analytics", page_icon="🏙️", layout="wide")

import style

style.inject()
style.sidebar_brand()

pages = [
    st.Page("home.py", title="Dashboard", icon="🏠", default=True),
    st.Page("pages/1_Market_Overview.py", title="Market Overview", icon="📈"),
    st.Page("pages/2_Geospatial_Map.py", title="Geospatial Map", icon="🗺️"),
    st.Page("pages/3_Delivery_Predictor.py", title="Delivery Predictor", icon="🤖"),
    st.Page("pages/4_Market_Forecast.py", title="Market Forecast", icon="🔮"),
    st.Page("pages/5_District_Intelligence.py", title="District Intelligence", icon="🧭"),
    st.Page("pages/6_Delivery_Watchlist.py", title="Delivery Watchlist", icon="🚨"),
]
st.navigation(pages).run()

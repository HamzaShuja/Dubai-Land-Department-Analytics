import streamlit as st
from bootstrap import load_data, df_download_button
import style
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from realestate.analysis.projects_analysis import area_summary
from realestate.analysis import market_intel as mi
from realestate.geo import AREA_COORDS

style.bootstrap_page("Geospatial Map",
                     "Development activity across Dubai communities.")

_, pr, _ = load_data()
areas = area_summary(pr)

# Overdue exposure per community (from the delivery watchlist)
_wl = mi.overdue_watchlist(pr)["watchlist"]
_ov = _wl.groupby("area_name_en")["no_of_units"].sum().rename("overdue_units")
areas = areas.merge(_ov, on="area_name_en", how="left")
areas["overdue_units"] = areas["overdue_units"].fillna(0).astype(int)

labels = {"total_units": "Total units", "n_projects": "Number of projects",
          "avg_completion": "Average completion %", "delivery_rate": "Delivery rate %",
          "overdue_units": "Overdue units (delivery watchlist)"}
metric = st.selectbox("Colour / weight by", list(labels.keys()),
                      format_func=lambda k: labels[k])

areas["lat"] = areas["area_name_en"].map(lambda a: (AREA_COORDS.get(a) or (None, None))[0])
areas["lon"] = areas["area_name_en"].map(lambda a: (AREA_COORDS.get(a) or (None, None))[1])
mapped = areas.dropna(subset=["lat", "lon"]).copy()

m = folium.Map(location=[25.12, 55.25], zoom_start=10, tiles="cartodbpositron")
vmax = mapped[metric].max() or 1
HeatMap(mapped[["lat", "lon", metric]].values.tolist(), radius=28, blur=20).add_to(m)
for _, r in mapped.iterrows():
    folium.CircleMarker(
        location=[r["lat"], r["lon"]],
        radius=6 + 18 * (r[metric] / vmax),
        color="#14603F", fill=True, fill_color="#1B7A52", fill_opacity=0.75, weight=1,
        tooltip=(f"<b>{r['area_name_en']}</b><br>Projects: {int(r['n_projects'])}<br>"
                 f"Units: {int(r['total_units']):,}<br>"
                 f"Avg completion: {r['avg_completion']:.0f}%<br>"
                 f"Delivery rate: {r['delivery_rate']:.0f}%"),
    ).add_to(m)

st_folium(m, use_container_width=True, height=500)
st.caption(f"Map shows {len(mapped)} communities with known centroids · "
           f"full ranking for all {len(areas)} communities below.")

style.section("All communities")
st.dataframe(areas.drop(columns=["lat", "lon"]).round(1),
             width="stretch", height=320)
df_download_button(areas.drop(columns=["lat", "lon"]),
                   "⬇️  Export all communities (CSV)", "communities.csv")

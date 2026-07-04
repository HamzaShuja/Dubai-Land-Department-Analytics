import streamlit as st

from bootstrap import load_data
import style
import numpy as np
import pandas as pd
import plotly.express as px

from realestate.models import lgbm_model
from realestate.models.inference import (load_reference, featurize_request,
                                          risk_band, cohort_context)
from realestate.translation import developer_display, project_type_display, is_known_developer

style.bootstrap_page(
    "Project Delivery Predictor",
    "Estimates what share of a project's construction is finished as of today, "
    "based on the developer's delivery track record and the project's size, type "
    "and timeline. The estimate is compared with projects launched the same year "
    "to judge whether this one is on pace or falling behind — and SHAP shows "
    "exactly what drove the number.",
)

FEATURE_LABELS = {
    "no_of_units": "Number of units", "no_of_buildings": "Buildings",
    "no_of_villas": "Villas", "no_of_lands": "Land plots",
    "total_assets": "Total assets", "planned_duration_days": "Planned duration",
    "start_year": "Start year", "dev_n_projects": "Developer · projects",
    "dev_total_units": "Developer · total units",
    "dev_delivered_rate_loo": "Developer · delivery rate",
    "dev_avg_completion_loo": "Developer · avg completion",
    "project_type_code": "Project type",
}

tx, pr, _ = load_data()
model = lgbm_model.load_model()
reference = load_reference()

if model is None or reference is None:
    st.warning("Model artifacts not found or outdated. Run `python -m realestate.build_artifacts` first.")
    st.stop()

# English-labelled developer dropdown mapped back to the source keys the model
# reference table uses. Only developers with a verified English identity are
# listed; ordered by portfolio size so major developers come first.
dev_counts = pr.groupby("developer_name")["project_id"].count().sort_values(ascending=False)
dev_labels: dict[str, str] = {}
for d in dev_counts.index:
    if not is_known_developer(d):
        continue
    lab = developer_display(d)
    n = 2
    base = lab
    while lab in dev_labels:  # guard against rare label collisions
        lab = f"{base} ({n})"
        n += 1
    dev_labels[lab] = d

ptypes = reference.get("type_categories", []) or sorted(pr["project_type"].dropna().unique())
ptype_labels = {project_type_display(t): t for t in ptypes}

st.caption("Pick a developer and describe a project. You get: **how much of it "
           "should be built by today**, and whether that is ahead of or behind other "
           "projects launched the same year.")

with st.form("predict"):
    c1, c2 = st.columns(2)
    dev_label = c1.selectbox("Developer", list(dev_labels.keys()))
    ptype_label = c2.selectbox("Project type", list(ptype_labels.keys()))
    c3, c4 = st.columns(2)
    start_year = c3.slider("Start year", 2000, 2030, 2025)
    duration = c4.slider("Planned duration (days)", 90, 5000, 900, step=30)
    c5, c6 = st.columns(2)
    units = c5.slider("Number of units", 0, 8000, 200, step=10)
    buildings = c6.slider("Number of buildings", 0, 200, 1)
    c7, _ = st.columns(2)
    villas = c7.slider("Number of villas", 0, 2000, 0, step=10)
    submitted = st.form_submit_button("Predict delivery")

if submitted:
    dev_key = dev_labels[dev_label]
    req = dict(developer_name=dev_key,
               no_of_units=units, no_of_buildings=buildings, no_of_villas=villas,
               no_of_lands=0, project_type=ptype_labels[ptype_label],
               planned_duration_days=duration, start_year=start_year)
    X = featurize_request(req, reference)
    pred = float(np.clip(model.predict(X)[0], 0, 100))
    band, peer = cohort_context(pred, start_year, reference)
    expected_txt = ("" if peer != peer else
                    f'<div style="color:#8A94A6;font-size:.8rem;margin-top:.35rem">'
                    f'Projects started in {start_year} are at ≈{peer:.0f}% on average</div>')

    import shap
    explainer = shap.TreeExplainer(model.booster)
    shap_vals = explainer.shap_values(X[model.features])[0]

    # Plain-English takeaway
    if peer == peer:  # cohort median available
        if "Early stage" in band:
            takeaway = (f"Too new to judge — projects launched in {start_year} have "
                        f"barely broken ground (≈{peer:.0f}% built on average).")
        elif pred >= peer * 0.9:
            takeaway = (f"On pace — a typical {start_year} launch is ≈{peer:.0f}% built "
                        f"by now, and this project is estimated at {pred:.0f}%.")
        else:
            takeaway = (f"Falling behind — a typical {start_year} launch is ≈{peer:.0f}% "
                        f"built by now, but this project is estimated at only {pred:.0f}%.")
    else:
        takeaway = "No same-year projects to compare against; risk band uses absolute thresholds."

    res, expl = st.columns([1, 2])
    with res:
        st.markdown(
            f'<div class="re-result"><div class="lbl" '
            f'style="color:{style.MUTED};font-weight:600;text-transform:uppercase;'
            f'font-size:.78rem">Estimated share of construction<br>finished as of today</div>'
            f'<div class="big">{pred:.0f}%</div>'
            f'<div class="re-badge">{band}</div>{expected_txt}'
            f'<div style="font-size:.85rem;margin-top:.8rem">{takeaway}</div>'
            f'<div style="color:{style.MUTED};font-size:.8rem;margin-top:.8rem">'
            f'Model validation · MAE ≈ {model.metrics.get("val_mae", float("nan")):.1f} pts · '
            f'R² ≈ {model.metrics.get("val_r2", float("nan")):.2f}</div></div>',
            unsafe_allow_html=True,
        )
        dev_ref = reference["dev"].get(dev_key)
        if dev_ref:
            st.markdown(
                f'<div style="color:{style.MUTED};font-size:.85rem;margin-top:.6rem">'
                f'<b>{dev_label}</b> track record — '
                f'{int(dev_ref["dev_n_projects"])} projects · '
                f'{dev_ref["dev_delivered_rate_loo"]:.0f}% delivered · '
                f'{dev_ref["dev_avg_completion_loo"]:.0f}% avg completion</div>',
                unsafe_allow_html=True,
            )
    with expl:
        style.section("Why this prediction (SHAP)")
        contrib = (pd.DataFrame({
                    "feature": [FEATURE_LABELS.get(f, f) for f in model.features],
                    "shap": shap_vals})
                   .assign(abs=lambda d: d["shap"].abs())
                   .sort_values("abs", ascending=False).head(10)
                   .sort_values("shap"))
        contrib["dir"] = np.where(contrib["shap"] >= 0, "Raises completion", "Lowers completion")
        fig = px.bar(contrib, x="shap", y="feature", orientation="h", color="dir",
                     color_discrete_map={"Raises completion": style.PRIMARY,
                                         "Lowers completion": "#D7574B"},
                     labels={"shap": "SHAP contribution (pts)", "feature": "", "dir": ""})
        st.plotly_chart(style.style_plotly(fig, height=380), width="stretch")

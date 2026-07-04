# Dubai Real Estate Analytics Platform

An end-to-end analytics platform on Dubai's open real-estate data: a validated
ETL pipeline into cloud PostgreSQL, a market-intelligence and statistics layer,
five machine-learning models with experiment tracking, a prediction API, a
professional seven-page interactive dashboard, automated PDF reporting, and a
fully containerised one-command stack with CI.

---

## Key insights this platform surfaces

Grounded in the current data (Dubai Pulse / DLD):

- **Record momentum** — quarterly sales value reached an all-time high of
  ~AED 184B in 2025 Q2, compounding ~26%/yr since 2016.
- **Forward supply wave** — ~383k units are in the off-plan pipeline (54% of all
  tracked units), front-loaded into 2026–2027.
- **Delivery-risk exposure** — ~74% of pipeline units sit in projects less than
  30% built, concentrating risk in newer launches.
- **Competitive market** — the top 5 developers hold ~35% of units (HHI ≈ 400).
- **A cash-driven rally** — mortgage registrations fell from ~1.3× sales value
  (2016) to ~0.23× (2025 Q2): today's record market is financed with equity,
  not leverage.
- **Where prices move** — villa average tickets repriced ~+34% in four
  quarters while apartments stayed flat (~AED 2M); land fell from 54% to 36%
  of sales value as end-user product displaced land speculation.
- **Broken delivery promises** — 347 off-plan projects (~83k units) are past
  their planned completion dates; 95 of them are stalled (<30% built),
  trapping ~30k units. A composite reliability score ranks all developers
  with 10+ projects.

---

## Highlights

- **Validated ETL** — Arabic→English translation, a Pydantic validation layer
  (every record checked before the database), deduplication and type casting,
  loaded into PostgreSQL on Neon. 100% of source rows pass validation.
- **Market intelligence** — market momentum (with correct, coverage-aware YoY),
  a custom Dubai Price Index, forward supply pipeline, delivery-risk exposure,
  market concentration (HHI), seasonal detection, developer-reputation scoring,
  and hypothesis testing (Welch t-test + Mann-Whitney with effect sizes).
- **Machine learning** — LightGBM delivery-risk model (SHAP-explained), Prophet
  12-month forecasting, KMeans investment-tier segmentation, and Isolation
  Forest anomaly detection. Runs tracked and the best model registered in MLflow.
- **Serving** — a FastAPI `/predict` endpoint returning a prediction with its
  SHAP breakdown, and a Streamlit dashboard with an insight-first layout, an
  emerald/white design system, a delivery watchlist with developer reliability
  scores, and English display throughout.
- **Automation & DevOps** — APScheduler daily refresh, weekly PDF report,
  Docker + docker-compose full stack, and GitHub Actions running the pytest
  suite (against a Postgres service) on every push.

---

## The data

Two official **Dubai Pulse / Dubai Land Department** open datasets:

| Dataset | Grain | Drives |
|---|---|---|
| Real-estate transactions | Quarterly market aggregates by property type × Sales/Mortgages/Other × Value/Number | Momentum, Price Index, seasonal analysis, hypothesis tests, market anomalies, Prophet forecasting |
| Real-estate projects | 3,039 project-level rows: area (71 communities), developer (112), status, units, completion %, dates | Supply pipeline, delivery-risk, developer reputation, concentration, off-plan vs ready, geospatial map, KMeans tiers, the delivery model |

**Data coverage:** transactions span 2016–2025; **2024 is not published in this
Dubai Pulse dataset**, so year-over-year figures that would need 2024 are shown
as unavailable (CAGR and quarter-on-quarter are used instead) and coverage is
disclosed in the UI. Because the transactions feed is aggregated (no per-property
price-per-sqft), community-level price/segmentation/prediction come from the
project feed — nothing is fabricated.

### What the ML model predicts

LightGBM predicts a project's **completion percentage to date** from the
developer's track record and the project's own attributes (no community input
needed). Features exclude the project's own status (no target leakage);
developer reputation signals use **leave-one-out** means. The dashboard rates
delivery risk by comparing the prediction with the median completion of the
project's start-year cohort. Validation: **MAE ≈ 6 pts, R² ≈ 0.91**.

---

## Quick start (Docker — recommended)

```bash
cp .env.example .env          # then set DATABASE_URL to your Neon connection string
docker compose up --build     # pipeline ▶ API (:8000) + dashboard (:8501) + scheduler
```

- Dashboard: <http://localhost:8501>
- API docs: <http://localhost:8000/docs>

The `pipeline` service runs the ETL and trains model artifacts first (a one-shot);
the API, dashboard, and scheduler start once it completes. For day-to-day use you
only need the dashboard: `docker compose up --no-deps dashboard`.

## Quick start (local)

Python 3.10–3.11 recommended (the pinned requirements are verified there).

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .              # makes the realestate package importable everywhere
cp .env.example .env          # optional: set DATABASE_URL (the dashboard runs without it)

python -m realestate.build_artifacts   # train + persist model artifacts
python -m streamlit run dashboard/app.py   # dashboard on :8501

# Optional services:
python -m realestate.pipeline          # ETL into PostgreSQL (needs DATABASE_URL)
uvicorn api.main:app --reload          # prediction API on :8000
python -m realestate.scheduler         # daily refresh
python -m realestate.reporting.weekly_report   # weekly PDF
```

No database? No problem — the dashboard automatically falls back to the bundled
Dubai Pulse workbooks in `input/`, so it is fully functional standalone.

---

## Dashboard (Streamlit, 7 pages)

Uses `st.navigation` for an explicit, labelled sidebar and a shared style module.

1. **Dashboard (home)** — decision-grade KPIs (sales value, supply pipeline,
   delivery-risk exposure, stalled projects), an insight callout, the forward
   supply-by-year chart, inventory mix, and the Price Index.
2. **Market Overview** — momentum KPIs, volume/value trends, the Dubai Price
   Index, the price signal by property type (average ticket), the market credit
   profile (cash vs mortgage), and the sales-mix shift.
3. **Geospatial Map** — Folium map of development activity across communities,
   including an overdue-units risk layer.
4. **Delivery Predictor** — pick a developer and project attributes, get a
   completion prediction rated against its start-year cohort, with a SHAP
   explanation and the developer's track record.
5. **Market Forecast** — Prophet forecast of average sale value per transaction,
   four quarters ahead with uncertainty intervals.
6. **District Intelligence** — market concentration (HHI), delivery-risk by
   area, KMeans investment tiers, anomalies, and hypothesis tests.
7. **Delivery Watchlist** — overdue and stalled ("zombie") projects with
   filters and CSV export, developer reliability rankings, and the stated
   pipeline split by build-progress credibility.

Every developer in the dataset (all 112) is shown under its verified English
name via a curated Arabic→English dictionary. Every table exports to CSV; each
page discloses data coverage.

---

## Phase 2 — DDA iPaaS live API auto-switch

The projects dataset can be pulled live from the **Dubai Digital Authority
iPaaS** gateway (OAuth2 client-credentials + `x-DDA-SecurityApplicationIdentifier`).
Fill the two endpoint URLs and set `DATA_SOURCE=api` in `.env`:

```
DATA_SOURCE=api
DDA_TOKEN_URL=<oauth2 token endpoint>
DDA_PROJECTS_URL=<projects dataset endpoint>
DDA_CLIENT_ID=...            # from DDA onboarding
DDA_CLIENT_SECRET=...
DDA_SECURITY_APP_ID=...      # x-DDA-SecurityApplicationIdentifier
DDA_APPLICATION_ID=...
DDA_ENV=STG
```

Ingestion then fetches projects live via `src/realestate/dda_client.py`
(token caching, pagination, response-envelope tolerance), with automatic
fallback to the local workbook if the API is unreachable — no code changes.
Credentials live only in `.env` (gitignored). The client is unit-tested with
mocked responses; `api_ready` guards activation so a partial config safely
stays on XLSX.

---

## Project structure

```
.
├── src/realestate/
│   ├── config.py            # pydantic-settings; DATA_SOURCE + DSN normalisation
│   ├── logging_config.py    # structured rotating logs
│   ├── translation.py       # Arabic→English columns/values + English display layer
│   ├── schemas.py           # Pydantic validation models
│   ├── ingestion.py         # XLSX/API readers + validation
│   ├── cleaning.py          # dedup, casting, derived columns
│   ├── db.py                # SQLAlchemy schema + idempotent loader
│   ├── data_access.py       # read tables back to DataFrames
│   ├── pipeline.py          # ETL orchestration
│   ├── scheduler.py         # APScheduler daily refresh
│   ├── build_artifacts.py   # train + persist models
│   ├── geo.py               # community centroids for the map
│   ├── analysis/            # market, market_intel, stats_tests, developers, anomaly, projects
│   ├── models/              # features, lgbm_model, forecast, segmentation, inference
│   └── reporting/           # weekly PDF report
├── api/main.py              # FastAPI /predict (+ SHAP) and /health
├── dashboard/               # app.py (navigation), home.py, style.py, bootstrap.py, pages/
├── tests/                   # pytest suite (48 tests) ingestion→API→metrics
├── input/                   # source Dubai Pulse / DLD workbooks
├── .streamlit/config.toml   # theme
├── Dockerfile, docker-compose.yml
└── .github/workflows/test.yml
```

---

## Testing

```bash
pytest                       # 48 tests across ingestion, validation, cleaning,
                             # DB load, analysis, market-intelligence, models,
                             # pipeline, reporting, and the API
```

Database tests use the configured PostgreSQL (the GitHub Actions Postgres
service) and fall back to an ephemeral local Postgres otherwise. CI runs the full
suite with coverage on every push.

---

## Deployment (free public URL)

The dashboard deploys to **Streamlit Community Cloud** in a few clicks — no
server needed, and no database either (it reads the bundled workbooks and the
committed model artifacts):

1. Push this repository to GitHub (the trained artifacts in `artifacts/models/`
   and the workbooks in `input/` are committed on purpose).
2. Go to <https://share.streamlit.io>, sign in with GitHub, **New app**.
3. Pick the repo, branch `main`, main file **`dashboard/app.py`**.
4. In *Advanced settings*, choose **Python 3.11**.
5. Deploy — you get a public `https://<your-app>.streamlit.app` URL to share.

Optionally add `DATABASE_URL` in the app's *Secrets* to serve from PostgreSQL
(Neon serverless works well); without it the app uses the local files.

---

## Data attribution

Source data: **Dubai Pulse** and the **Dubai Land Department (DLD)** open-data
portals. This platform, its pipeline, models, and applications were designed and
built by **Hamza Shuja**.

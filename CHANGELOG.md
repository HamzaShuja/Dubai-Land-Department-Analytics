# Changelog

All notable changes to the Dubai Real Estate Analytics Platform.

## 1.5 - Insight overhaul (2026-07)

- New **Delivery Watchlist** page: 347 overdue off-plan projects (~83k units)
  surfaced with filters and CSV export; 95 stalled "zombie" projects flagged
  (overdue and <30% built).
- New **developer reliability score** (0-100) blending delivered rate, average
  completion and overdue share, for every developer with 10+ tracked projects.
- **Credibility-weighted supply pipeline**: stated completion years split by
  build-progress bands, showing how much of the promised supply is realistic.
- **Market Overview** gained three sections: price signal (average ticket by
  property type), market credit profile (mortgage-to-sales ratio, documenting
  the shift from a leveraged to a cash-driven market), and the sales-mix shift.
- **Geospatial Map** gained an overdue-units risk layer.
- Test suite extended to 48 tests.

## 1.4 - Naming, model and predictor rework (2026-07)

- Curated English names for **all 112 developers** (previously only major ones);
  no transliteration artefacts remain anywhere in the UI.
- Arabic free-text project names removed from displays in favour of the
  workbook's English master-project names, carried through the full pipeline
  and database schema.
- **Delivery Predictor** reworked to be developer-centric: the model was
  retrained without area features (MAE 6.3, R² 0.91 - unchanged), and
  predictions are now rated against the median completion of the project's
  start-year cohort instead of an absolute band, with the developer's track
  record shown alongside.
- Fixed a fallback bug in single-request featurisation (missing planned
  duration now falls back to the global median duration).
- Migrated off the deprecated `use_container_width` Streamlit API.

## 1.3 - DDA iPaaS live API integration (2026-07)

- OAuth2 client-credentials client for the Dubai Digital Authority iPaaS
  gateway with token caching, pagination and envelope-tolerant parsing;
  automatic fallback to the local workbook keeps the pipeline resilient.
- `DATA_SOURCE=api` switch activates live ingestion with no code changes.

## 1.2 - Market-intelligence layer (2026-06)

- Momentum metrics with coverage-aware year-over-year handling (the source
  dataset does not publish 2024), CAGR and quarter-on-quarter comparisons.
- Forward supply pipeline, delivery-risk exposure, market concentration (HHI),
  and a decision-grade home page built around them.

## 1.1 - UI overhaul (2026-06)

- Professional emerald/white design system, `st.navigation` controller,
  English display layer across all pages, slider-based predictor form.

## 1.0 - Initial platform (2026-06)

- Validated ETL (Pydantic) from Dubai Pulse / DLD workbooks into PostgreSQL,
  analysis and statistics layer, LightGBM + SHAP delivery model, Prophet
  forecasting, KMeans segmentation, Isolation Forest anomaly detection,
  FastAPI prediction service, five-page Streamlit dashboard, APScheduler
  refresh, weekly PDF reporting, Docker Compose stack and GitHub Actions CI.

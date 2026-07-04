"""Shared bootstrap for Streamlit pages: makes the src package importable and
provides cached data loaders (database first, local files as fallback)."""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st  # noqa: E402

from realestate import data_access  # noqa: E402
from realestate.ingestion import ingest  # noqa: E402
from realestate.cleaning import clean_transactions, clean_projects  # noqa: E402


@st.cache_data(ttl=3600, show_spinner="Loading market data…")
def load_data():
    """Return (transactions_df, projects_df, source). Tries PostgreSQL, then
    falls back to the local Dubai Pulse workbooks so the dashboard always runs."""
    try:
        tx = data_access.load_transactions()
        pr = data_access.load_projects()
        if len(tx) and len(pr):
            return tx, pr, "database"
    except Exception:
        pass
    ing = ingest()
    return clean_transactions(ing.transactions), clean_projects(ing.projects), "local files"


def df_download_button(df, label: str, filename: str):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"),
                       file_name=filename, mime="text/csv")

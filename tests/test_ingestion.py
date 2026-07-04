"""Ingestion + Arabic->English translation."""
from realestate.translation import translate_value, PROPERTY_TYPE_AR_EN, normalise_status


def test_translation_lookup():
    assert translate_value("وحده", PROPERTY_TYPE_AR_EN) == "Units"
    assert translate_value("فيلا", PROPERTY_TYPE_AR_EN) == "Villa"
    # Unknown values pass through unchanged.
    assert translate_value("xyz", PROPERTY_TYPE_AR_EN) == "xyz"


def test_status_normalisation():
    assert normalise_status("FINISHED") == "Finished"
    assert normalise_status("FRIEZED") == "Frozen"


def test_ingest_shapes_and_validation(ingested):
    assert len(ingested.transactions) == 696
    assert ingested.projects.shape[0] > 3000
    # Every record validated cleanly.
    for report in ingested.reports:
        assert report.acceptance_rate == 1.0


def test_transactions_columns(ingested):
    expected = {"year", "quarter", "quarter_number", "property_type",
                "transaction_group", "measure", "amount"}
    assert expected.issubset(set(ingested.transactions.columns))
    assert set(ingested.transactions["property_type"].unique()) <= {
        "Units", "Building", "Land", "Villa"}

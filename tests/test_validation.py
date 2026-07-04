"""Pydantic validation layer."""
import pytest
from pydantic import ValidationError

from realestate.schemas import TransactionRecord, ProjectRecord


def test_transaction_accepts_valid():
    r = TransactionRecord(year=2024, quarter="First Quarter", quarter_number=1,
                          property_type="Units", transaction_group="Sales",
                          measure="Value", amount=1000.0)
    assert r.amount == 1000.0


def test_transaction_rejects_unknown_type():
    with pytest.raises(ValidationError):
        TransactionRecord(year=2024, quarter="Q", quarter_number=1,
                          property_type="Spaceship", transaction_group="Sales",
                          measure="Value", amount=1.0)


def test_transaction_rejects_negative_amount():
    with pytest.raises(ValidationError):
        TransactionRecord(year=2024, quarter="Q", quarter_number=1,
                          property_type="Units", transaction_group="Sales",
                          measure="Value", amount=-5.0)


def test_project_coerces_nan_id():
    r = ProjectRecord(project_id=1, area_name_en="X", developer_name="Y",
                      project_status="Active", developer_id=float("nan"),
                      percent_completed=50, no_of_units=1, no_of_buildings=0,
                      no_of_villas=0, no_of_lands=0)
    assert r.developer_id is None


def test_project_clamps_percent():
    r = ProjectRecord(project_id=1, area_name_en="X", developer_name="Y",
                      project_status="Active", percent_completed=150,
                      no_of_units=1, no_of_buildings=0, no_of_villas=0, no_of_lands=0)
    assert r.percent_completed == 100.0


def test_project_rejects_empty_area():
    with pytest.raises(ValidationError):
        ProjectRecord(project_id=1, area_name_en="  ", developer_name="Y",
                      project_status="Active", percent_completed=50,
                      no_of_units=0, no_of_buildings=0, no_of_villas=0, no_of_lands=0)

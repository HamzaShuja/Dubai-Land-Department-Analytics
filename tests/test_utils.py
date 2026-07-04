"""Config, geo lookup, and scheduler wiring."""
from realestate.config import Settings
from realestate.geo import coords_for, AREA_COORDS
from realestate.scheduler import build_scheduler


def test_dsn_normalisation_strips_prefix():
    s = Settings(database_url="DB:postgresql://u:p@host/db")
    assert s.database_url.startswith("postgresql://")
    assert s.sqlalchemy_url.startswith("postgresql+psycopg://")


def test_geo_lookup():
    assert coords_for("Business Bay") is not None
    assert coords_for("Nonexistent Area") is None
    for lat, lon in AREA_COORDS.values():
        assert 24.0 < lat < 26.0 and 54.0 < lon < 56.0  # within Dubai bounds


def test_scheduler_has_daily_job():
    sched = build_scheduler()
    jobs = sched.get_jobs()
    assert any(j.id == "daily_refresh" for j in jobs)

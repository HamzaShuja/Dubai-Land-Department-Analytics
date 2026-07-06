"""DDA iPaaS client - token flow, headers, pagination and parsing (mocked)."""
import requests

from realestate.config import Settings
from realestate.dda_client import DDAClient


class FakeResp:
    def __init__(self, js, status=200):
        self._js, self.status_code = js, status

    def json(self):
        return self._js

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")


def _settings(**over):
    base = dict(dda_token_url="https://stg/token", dda_projects_url="https://stg/projects",
                dda_client_id="cid", dda_client_secret="sec",
                dda_security_app_id="secid", dda_application_id="appid",
                data_source="api", dda_page_size=2)
    base.update(over)
    return Settings(**base)


def test_api_ready_requires_full_config():
    assert _settings().api_ready is True
    assert _settings(dda_projects_url="").api_ready is False


def test_token_headers_and_parsing(monkeypatch):
    seen = {}

    def fake_post(url, data=None, headers=None, timeout=None):
        seen["token_data"] = data
        return FakeResp({"access_token": "TOK", "expires_in": 3600})

    pages = [[
        {"projectId": 1, "areaNameEn": "X", "developerName": "D", "projectStatus": "ACTIVE",
         "percentCompleted": 50, "noOfUnits": 10, "noOfBuildings": 1, "noOfVillas": 0, "noOfLands": 0},
        {"projectId": 2, "areaNameEn": "Y", "developerName": "E", "projectStatus": "FINISHED",
         "percentCompleted": 100, "noOfUnits": 5, "noOfBuildings": 1, "noOfVillas": 0, "noOfLands": 0},
    ], []]
    seq = {"i": 0}

    def fake_get(url, headers=None, params=None, timeout=None):
        seen["get_headers"] = headers
        i = seq["i"]; seq["i"] += 1
        return FakeResp(pages[i] if i < len(pages) else [])

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)

    df = DDAClient(_settings()).fetch_projects()
    assert df is not None and len(df) == 2
    assert {"project_id", "area_name_en", "developer_name", "project_status"}.issubset(df.columns)
    assert df.iloc[1]["project_status"] == "Finished"           # status normalised
    assert seen["get_headers"]["Authorization"] == "Bearer TOK"
    assert seen["get_headers"]["x-DDA-SecurityApplicationIdentifier"] == "secid"
    assert seen["get_headers"]["x-DDA-ApplicationId"] == "appid"
    assert seen["token_data"]["grant_type"] == "client_credentials"


def test_fetch_failure_falls_back_to_none(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(requests, "post", boom)
    assert DDAClient(_settings()).fetch_projects() is None

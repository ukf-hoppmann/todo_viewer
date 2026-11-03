from __future__ import annotations

import dataclasses
import sqlite3

from example_plugin.plugin import EXAMPLE_PLUGIN
from fastapi import FastAPI
from starlette.testclient import TestClient
from viewer.app.composition import create_app
from viewer.core.domain.settings import Settings


def test_the_configured_value_is_shown_until_one_is_stored(app: FastAPI) -> None:
    with TestClient(app) as c:
        assert c.get("/api/core/settings/sync").json() == {
            "auto_sync_interval_seconds": 30.0,
            "locked_by_environment": False,
        }


def test_put_changes_the_value_and_it_survives_a_restart(settings: Settings) -> None:
    with TestClient(create_app(settings, plugins=[EXAMPLE_PLUGIN])) as c:
        assert c.put("/api/core/settings/sync", json={"auto_sync_interval_seconds": 7}).json() == {
            "auto_sync_interval_seconds": 7.0,
            "locked_by_environment": False,
        }
    with TestClient(create_app(settings, plugins=[EXAMPLE_PLUGIN])) as c:
        assert c.get("/api/core/settings/sync").json()["auto_sync_interval_seconds"] == 7.0
    rows = sqlite3.connect(settings.db_path).execute("SELECT key, value FROM core_settings").fetchall()
    assert rows == [("auto_sync_interval_seconds", "7.0")]


def test_an_invalid_value_is_rejected(app: FastAPI) -> None:
    with TestClient(app) as c:
        response = c.put("/api/core/settings/sync", json={"auto_sync_interval_seconds": 0.1})
    assert response.status_code == 422 and response.json()["code"] == "invalid_input"


def test_a_value_from_the_environment_wins_and_blocks_writing(settings: Settings) -> None:
    locked = dataclasses.replace(settings, auto_sync_interval_seconds=5.0, auto_sync_interval_from_env=True)
    with TestClient(create_app(locked, plugins=[EXAMPLE_PLUGIN])) as c:
        assert c.get("/api/core/settings/sync").json() == {
            "auto_sync_interval_seconds": 5.0,
            "locked_by_environment": True,
        }
        response = c.put("/api/core/settings/sync", json={"auto_sync_interval_seconds": 10})
    assert response.status_code == 409 and response.json()["code"] == "setting_locked"


def test_the_settings_are_not_offered_as_mcp_tools(app: FastAPI) -> None:
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    assert set(paths["/api/core/settings/sync"]) == {"get", "put"}

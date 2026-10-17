from __future__ import annotations

import json
import sqlite3

from example_plugin.plugin import EXAMPLE_PLUGIN
from fastapi import FastAPI
from starlette.testclient import TestClient
from viewer.app.composition import create_app
from viewer.core.application.ui_state import MAX_DOCUMENT_BYTES
from viewer.core.domain.settings import Settings


def test_empty_document_until_something_is_stored(app: FastAPI) -> None:
    with TestClient(app) as c:
        assert c.get("/api/core/ui-state/backlog").json() == {"owner": "backlog", "document": {}}


def test_put_replaces_the_document_and_get_returns_it(app: FastAPI) -> None:
    with TestClient(app) as c:
        doc = {"filter": {"status": ["Open"], "text": "Größe"}, "expanded": ["EPIC-007"]}
        assert c.put("/api/core/ui-state/backlog", json={"document": doc}).json() == {
            "owner": "backlog",
            "document": doc,
        }
        c.put("/api/core/ui-state/backlog", json={"document": {"only": 1}})
        assert c.get("/api/core/ui-state/backlog").json()["document"] == {"only": 1}
        assert c.get("/api/core/ui-state/notes").json()["document"] == {}


def test_state_lives_in_the_database_and_survives_a_restart(settings: Settings) -> None:
    with TestClient(create_app(settings, plugins=[EXAMPLE_PLUGIN])) as c:
        c.put("/api/core/ui-state/layout", json={"document": {"theme": "dark"}})
    with TestClient(create_app(settings, plugins=[EXAMPLE_PLUGIN])) as c:
        assert c.get("/api/core/ui-state/layout").json()["document"] == {"theme": "dark"}
    row = sqlite3.connect(settings.db_path).execute("SELECT owner, document FROM core_ui_state").fetchall()
    assert [(o, json.loads(d)) for o, d in row] == [("layout", {"theme": "dark"})]


def test_invalid_owner_and_oversized_document_are_rejected(app: FastAPI) -> None:
    with TestClient(app) as c:
        bad_owner = c.get("/api/core/ui-state/Böse_ID")
        too_big = c.put("/api/core/ui-state/layout", json={"document": {"x": "a" * (MAX_DOCUMENT_BYTES + 1)}})
    assert bad_owner.status_code == 422 and bad_owner.json()["code"] == "invalid_input"
    assert too_big.status_code == 422 and too_big.json()["code"] == "invalid_input"
    assert too_big.json()["details"]["max"] == MAX_DOCUMENT_BYTES


def test_ui_state_routes_are_in_openapi(app: FastAPI) -> None:
    with TestClient(app) as c:
        paths = c.get("/openapi.json").json()["paths"]
    assert set(paths["/api/core/ui-state/{owner}"]) == {"get", "put"}


def test_startup_migrates_and_records_versions(settings: Settings) -> None:
    create_app(settings, plugins=[EXAMPLE_PLUGIN])
    rows = dict(sqlite3.connect(settings.db_path).execute("SELECT owner, version FROM core_migrations").fetchall())
    assert rows == {"core": 1}

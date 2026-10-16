"""GET /api/v2/storage tells where the central database is; it is read-only information."""
from __future__ import annotations

from todo_viewer.infrastructure.database.migrations import CURRENT_VERSION


def test_the_storage_is_described_by_type_location_and_schema_version(api, workspace):
    resp = api.get("/api/v2/storage")

    assert resp.status_code == 200, resp.body
    assert resp.body == {"kind": "sqlite", "location": str(workspace.config_dir / "todo.db"),
                         "schema_version": CURRENT_VERSION}


def test_asking_changes_nothing_about_the_projects(api, workspace):
    before = api.get("/api/v2/sources").body

    api.get("/api/v2/storage")

    assert api.get("/api/v2/sources").body == before

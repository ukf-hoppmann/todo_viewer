"""/api/v2/sources manages projects of both backends; markdown projects are registered by folder as before."""
from __future__ import annotations


def _central(api, **fields) -> dict:
    return api.post("/api/v2/sources", {"backend": "database", "project": "Central", **fields})


def test_a_database_project_is_created_by_name(api, workspace):
    resp = _central(api, sync_path=" /repos/central/docs/todo/ ")
    other = _central(api, project="Second")

    assert resp.status_code == 200, resp.body
    assert (resp.body["project"], resp.body["backend"], resp.body["path"], resp.body["sync_path"]) == (
        "Central", "database", "", "/repos/central/docs/todo")
    assert len(resp.body["id"]) == 36 and other.body["id"] != resp.body["id"]
    assert [(s["project"], s["backend"]) for s in api.get("/api/v2/sources").body] == [
        ("Central", "database"), ("Second", "database")]


def test_a_database_project_needs_a_name(api, workspace):
    resp = api.post("/api/v2/sources", {"backend": "database", "project": "  "})

    assert (resp.status_code, resp.body["code"]) == (400, "value_required")


def test_markdown_projects_report_their_backend(api, workspace):
    folder = workspace.add_backlog("backlog")

    resp = api.post("/api/v2/sources", {"path": str(folder)})

    assert (resp.body["backend"], resp.body["sync_path"]) == ("markdown", None)
    assert api.get("/api/v2/backlog").body["sources"][0]["backend"] == "markdown"


def test_a_database_project_holds_items(api, workspace):
    sid = _central(api).body["id"]

    created = api.post("/api/v2/items", {"source_id": sid, "type": "Epic", "title": "First", "area": "Core",
                                         "goal": "g", "completion_criteria": "c"})

    assert created.status_code == 201, created.body
    assert [s["item_count"] for s in api.get("/api/v2/backlog").body["sources"]] == [1]


def test_a_database_project_can_be_renamed_and_only_moved_to_a_folder_that_exists(api, workspace):
    sid = _central(api).body["id"]

    renamed = api.put(f"/api/v2/sources/{sid}", {"backend": "database", "project": "Renamed",
                                                  "sync_path": "/repos/x"})
    moved = api.put(f"/api/v2/sources/{sid}", {"backend": "markdown", "path": "/repos/x"})

    assert (renamed.status_code, renamed.body["project"], renamed.body["sync_path"]) == (200, "Renamed", "/repos/x")
    assert renamed.body["id"] == sid
    assert (moved.status_code, moved.body["code"]) == (400, "not_found")
    assert api.get("/api/v2/sources").body[0]["backend"] == "database"


def test_a_database_project_with_items_cannot_be_removed(api, workspace):
    sid = _central(api).body["id"]
    empty = _central(api, project="Empty").body["id"]
    api.post("/api/v2/items", {"source_id": sid, "type": "Epic", "title": "Keep me", "area": "Core",
                               "goal": "g", "completion_criteria": "c"})

    refused = api.delete(f"/api/v2/sources/{sid}")
    removed = api.delete(f"/api/v2/sources/{empty}")

    assert (refused.status_code, refused.body["code"], refused.body["details"]) == (
        409, "project_not_empty", {"project": "Central"})
    assert removed.status_code == 200
    assert [s["id"] for s in api.get("/api/v2/sources").body] == [sid]

"""API v2: items addressed by source id + item id, sources by stable id, errors as {code, message, details}."""
from __future__ import annotations

import json


def _setup(workspace, *fixtures: str) -> list:
    folders = [workspace.add_backlog(f) for f in fixtures]
    workspace.write_config([{"project": f, "path": str(p)} for f, p in zip(fixtures, folders, strict=True)])
    return folders


def _item(api, item_id: str) -> dict:
    return next(i for i in api.get("/api/v2/backlog").body["items"] if i["id"] == item_id)


def test_backlog(api, workspace, golden):
    _setup(workspace, "backlog", "no_archive")

    resp = api.get("/api/v2/backlog")

    assert resp.status_code == 200
    ids = {s["id"]: f"<SOURCE{n}>" for n, s in enumerate(resp.body["sources"])}
    text = json.dumps(resp.body)
    for real, placeholder in ids.items():
        text = text.replace(real, placeholder)
    golden("v2/backlog.json", json.loads(text))
    keys = [i["key"] for i in resp.body["items"]]
    assert len(keys) == len(set(keys))


def test_backlog_without_config_is_empty(api):
    assert api.get("/api/v2/backlog").body == {"sources": [], "items": []}
    assert api.get("/api/v2/sources").body == []


def test_index_lists_only_placement_fields(api, workspace):
    _setup(workspace, "backlog", "no_archive")
    sources = {s["project"]: s["id"] for s in api.get("/api/v2/sources").body}

    full = api.get("/api/v2/index")
    one = api.get("/api/v2/index", source_id=sources["no_archive"])
    gone = api.get("/api/v2/index", source_id="nope")

    assert full.status_code == 200
    assert set(full.body) == {"items"}
    assert all(set(i) == {"source_id", "id", "type", "status", "title", "parent"} for i in full.body["items"])
    by_id = {i["id"]: i for i in full.body["items"] if i["source_id"] == sources["backlog"]}
    assert by_id["TASK-001"] == {"source_id": sources["backlog"], "id": "TASK-001", "type": "Task",
                                 "status": "In progress", "title": "Write the parser", "parent": "STORY-001"}
    assert "TASK-000" in by_id  # archived items are part of the index
    assert len(full.body["items"]) == len(api.get("/api/v2/backlog").body["items"])
    assert {i["source_id"] for i in one.body["items"]} == {sources["no_archive"]}
    assert (gone.status_code, gone.body["code"]) == (404, "source_gone")


def test_get_item_by_id(api, workspace):
    _setup(workspace, "backlog")
    active, archived = _item(api, "TASK-001"), _item(api, "TASK-000")
    url = f"/api/v2/items/{active['source_id']}"

    assert api.get(f"{url}/TASK-001").body == active
    assert api.get(f"{url}/TASK-000").body == archived
    assert (active["key"], active["archived"], archived["archived"]) == (f"{active['source_id']}/TASK-001",
                                                                         False, True)
    missing = api.get(f"{url}/TASK-999")
    assert (missing.status_code, missing.body["code"]) == (404, "item_not_found")
    assert missing.body["details"] == {"id": "TASK-999"}
    assert api.get("/api/v2/items/nope/TASK-001").body["code"] == "source_gone"


def test_edit_archives_and_changes_version(api, workspace):
    _setup(workspace, "backlog")
    item = _item(api, "TASK-001")

    resp = api.patch(f"/api/v2/items/{item['source_id']}/TASK-001",
                     {"version": item["version"], "field": "status", "value": "Completed", "resolution": "Done"})

    assert resp.status_code == 200
    assert (resp.body["archived"], resp.body["key"]) == (True, item["key"])
    assert resp.body["version"] != item["version"]
    assert (resp.body["status"], resp.body["resolution"]) == ("Completed", "Done.")
    assert _item(api, "TASK-001") == resp.body


def test_edit_errors(api, workspace):
    _setup(workspace, "backlog")
    item = _item(api, "TASK-001")
    url = f"/api/v2/items/{item['source_id']}/TASK-001"
    version = item["version"]

    stale = api.patch(url, {"version": "outdated", "field": "status", "value": "Open"})
    unknown_source = api.patch("/api/v2/items/nope/TASK-001", {"version": version, "field": "status",
                                                              "value": "Open"})
    no_version = api.patch(url, {"field": "status", "value": "Open"})
    no_resolution = api.patch(url, {"version": version, "field": "status", "value": "Rejected"})
    bad_field = api.patch(url, {"version": version, "field": "title", "value": "x"})

    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    assert (unknown_source.status_code, unknown_source.body["code"]) == (404, "source_gone")
    assert (no_version.status_code, no_version.body["code"]) == (400, "bad_request")
    assert (no_resolution.status_code, no_resolution.body["code"]) == (400, "resolution_required")
    assert (bad_field.status_code, bad_field.body["code"]) == (400, "bad_request")
    assert bad_field.body["details"] == {"field": "field"}
    assert set(stale.body) == {"code", "message", "details"}


def test_old_edit_endpoint_is_gone(api):
    assert api.post("/api/v2/items/edit", {}).status_code in (404, 405)


def test_sources_by_id(api, workspace):
    backlog, second = _setup(workspace, "backlog", "no_archive")
    extra = workspace.add_backlog("no_archive", name="Extra")
    sources = api.get("/api/v2/sources").body

    added = api.post("/api/v2/sources", {"path": str(extra)})
    dup = api.post("/api/v2/sources", {"path": str(backlog)})
    renamed = api.put(f"/api/v2/sources/{sources[0]['id']}", {"path": str(backlog), "project": "Renamed"})
    removed = api.delete(f"/api/v2/sources/{sources[1]['id']}")
    gone = api.delete(f"/api/v2/sources/{sources[1]['id']}")

    assert added.body["project"] == "Extra"
    assert (dup.status_code, dup.body["code"]) == (409, "duplicate")
    assert renamed.body == {"id": sources[0]["id"], "project": "Renamed", "path": str(backlog)}
    assert removed.body["path"] == str(second)
    assert (gone.status_code, gone.body["code"]) == (404, "source_gone")
    assert [s["project"] for s in api.get("/api/v2/sources").body] == ["Renamed", "Extra"]


def test_document_folders_and_ui_state(api, workspace):
    _setup(workspace, "backlog")
    source_id = api.get("/api/v2/sources").body[0]["id"]

    doc = api.get(f"/api/v2/sources/{source_id}/document", path="items/TASK-002/notes.md")
    forbidden = api.get(f"/api/v2/sources/{source_id}/document", path="../x.md")
    folders = api.get("/api/v2/folders")
    saved = api.put("/api/v2/ui-state", {"view": "tree"})

    assert doc.body["content"].startswith("# Notes for TASK-002")
    assert (forbidden.status_code, forbidden.body["code"]) == (403, "forbidden")
    assert [d["name"] for d in folders.body["dirs"]] == ["backlog"]
    assert saved.body == api.get("/api/v2/ui-state").body == {"view": "tree"}


def test_serves_frontend_and_reports_missing_build(api, settings):
    from fastapi.testclient import TestClient

    from todo_viewer.api import create_app
    from todo_viewer.bootstrap import build_container

    index = api._raw.get("/")
    missing = TestClient(create_app(build_container(settings), settings.frontend_dir / "nope")).get("/")

    assert (index.status_code, index.text) == (200, "<!doctype html><title>test</title>")
    assert missing.status_code == 503
    assert "npm --prefix web run build" in missing.text

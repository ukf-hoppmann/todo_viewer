"""API v2: items addressed by ref, sources by stable id, errors as {code, message, details}."""
from __future__ import annotations

import json


def _setup(workspace, *fixtures: str) -> list:
    folders = [workspace.add_backlog(f) for f in fixtures]
    workspace.write_config([{"project": f, "path": str(p)} for f, p in zip(fixtures, folders, strict=True)])
    return folders


def _item(api, item_id: str) -> dict:
    return next(i for i in api.get("/api/v2/backlog").body["items"] if i["ref"]["id"] == item_id)


def test_backlog(api, workspace, golden):
    _setup(workspace, "backlog", "checklist")

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


def test_edit_archives_and_returns_new_ref(api, workspace):
    _setup(workspace, "backlog")
    item = _item(api, "TASK-001")

    resp = api.post("/api/v2/items/edit",
                    {"ref": item["ref"], "field": "status", "value": "Completed", "resolution": "Done"})

    assert resp.status_code == 200
    assert resp.body["ref"]["location"] == "archive"
    assert resp.body["ref"]["line"] != item["ref"]["line"]
    assert (resp.body["status"], resp.body["resolution"]) == ("Completed", "Done.")
    assert _item(api, "TASK-001")["ref"] == resp.body["ref"]


def test_edit_errors(api, workspace):
    _setup(workspace, "backlog")
    ref = _item(api, "TASK-001")["ref"]

    stale = api.post("/api/v2/items/edit", {"ref": {**ref, "line": ref["line"] + 1}, "field": "status",
                                            "value": "Open"})
    unknown_source = api.post("/api/v2/items/edit", {"ref": {**ref, "source_id": "nope"}, "field": "status",
                                                     "value": "Open"})
    no_resolution = api.post("/api/v2/items/edit", {"ref": ref, "field": "status", "value": "Rejected"})
    bad_field = api.post("/api/v2/items/edit", {"ref": ref, "field": "title", "value": "x"})

    assert (stale.status_code, stale.body["code"]) == (409, "entry_moved")
    assert (unknown_source.status_code, unknown_source.body["code"]) == (404, "source_gone")
    assert (no_resolution.status_code, no_resolution.body["code"]) == (400, "resolution_required")
    assert (bad_field.status_code, bad_field.body["code"]) == (400, "bad_request")
    assert bad_field.body["details"] == {"field": "field"}
    assert set(stale.body) == {"code", "message", "details"}


def test_sources_by_id(api, workspace):
    backlog, checklist = _setup(workspace, "backlog", "checklist")
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
    assert removed.body["path"] == str(checklist)
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

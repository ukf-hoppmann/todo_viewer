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


def test_health(api):
    assert api.get("/api/v2/health").body == {"status": "ok", "api": "2"}


def test_backlog_without_config_is_empty(api):
    assert api.get("/api/v2/backlog").body == {"sources": [], "items": []}
    assert api.get("/api/v2/sources").body == []


def test_index_lists_only_placement_fields(api, workspace):
    folder, _ = _setup(workspace, "backlog", "no_archive")
    archive = folder / "archive.md"
    archive.write_text(archive.read_text(encoding="utf-8").replace(
        "  - Status: Completed.\n", "  - Status: Completed.\n  - Area: Setup.\n", 1), encoding="utf-8")
    sources = {s["project"]: s["id"] for s in api.get("/api/v2/sources").body}

    full = api.get("/api/v2/index")
    one = api.get("/api/v2/index", source_id=sources["no_archive"])
    gone = api.get("/api/v2/index", source_id="nope")

    assert full.status_code == 200
    assert set(full.body) == {"items"}
    assert all(set(i) == {"source_id", "id", "type", "status", "title", "parent", "area"}
               for i in full.body["items"])
    by_id = {i["id"]: i for i in full.body["items"] if i["source_id"] == sources["backlog"]}
    assert by_id["TASK-001"] == {"source_id": sources["backlog"], "id": "TASK-001", "type": "Task",
                                 "status": "In progress", "title": "Write the parser", "parent": "STORY-001",
                                 "area": None}
    assert by_id["EPIC-001"]["area"] == "Core"
    assert by_id["TASK-000"]["area"] == "Setup"  # archived items are part of the index, area included
    assert len(full.body["items"]) == len(api.get("/api/v2/backlog").body["items"])
    assert {i["source_id"] for i in one.body["items"]} == {sources["no_archive"]}
    assert (gone.status_code, gone.body["code"]) == (404, "source_gone")


def test_create_item(api, workspace):
    (folder,) = _setup(workspace, "backlog")
    source_id = api.get("/api/v2/sources").body[0]["id"]
    body = {"source_id": source_id, "type": "Task", "title": "Write tests", "area": "Core",
            "goal": "Tests exist.", "completion_criteria": "They pass.", "parent": "STORY-001",
            "required_for_parent": "Yes", "dependencies": ["TASK-001"]}

    created = api.post("/api/v2/items", body)
    second = api.post("/api/v2/items", {**body, "title": "Second"})

    assert created.status_code == 201, created.body
    assert (created.body["id"], created.body["status"], created.body["priority"]) == ("TASK-004", "Open", "Normal")
    assert second.body["id"] == "TASK-005"
    assert api.get(f"/api/v2/items/{source_id}/TASK-004").body == created.body
    todo = (folder / "TODO.md").read_text(encoding="utf-8")
    assert todo.index("`TASK-005`") < todo.index("## Other section")


def test_create_item_errors(api, workspace):
    (folder,) = _setup(workspace, "backlog")
    source_id = api.get("/api/v2/sources").body[0]["id"]
    before = (folder / "TODO.md").read_bytes()
    body = {"source_id": source_id, "type": "Task", "title": "x", "area": "a", "goal": "g",
            "completion_criteria": "c"}

    cases = [
        (400, "invalid_value", {"type": "Bug"}),
        (400, "bad_request", {"status": "Completed"}),
        (400, "bad_request", {"goal": None}),
        (400, "value_required", {"area": "  "}),
        (404, "source_gone", {"source_id": "nope"}),
        (409, "unknown_reference", {"parent": "STORY-999", "required_for_parent": "Yes"}),
        (409, "required_for_parent_missing", {"parent": "STORY-001"}),
        (409, "epic_with_parent", {"type": "Epic", "parent": "STORY-001", "required_for_parent": "Yes"}),
        (409, "parent_closed", {"parent": "STORY-000", "required_for_parent": "No"}),
    ]
    for status, code, override in cases:
        resp = api.post("/api/v2/items", {**body, **override})
        assert (resp.status_code, resp.body.get("code")) == (status, code), (code, resp.body)
    assert resp.body["details"] == {"id": "TASK-004", "items": "STORY-000"}  # the new item and what to reopen

    assert (folder / "TODO.md").read_bytes() == before


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
                     {"version": item["version"], "fields": {"status": "Completed"}, "resolution": "Done"})

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

    stale = api.patch(url, {"version": "outdated", "fields": {"status": "Open"}})
    unknown_source = api.patch("/api/v2/items/nope/TASK-001", {"version": version, "fields": {"status": "Open"}})
    no_version = api.patch(url, {"fields": {"status": "Open"}})
    no_resolution = api.patch(url, {"version": version, "fields": {"status": "Rejected"}})
    bad_field = api.patch(url, {"version": version, "fields": {}})

    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    assert (unknown_source.status_code, unknown_source.body["code"]) == (404, "source_gone")
    assert (no_version.status_code, no_version.body["code"]) == (400, "bad_request")
    assert (no_resolution.status_code, no_resolution.body["code"]) == (400, "resolution_required")
    assert (bad_field.status_code, bad_field.body["code"]) == (400, "bad_request")
    assert bad_field.body["details"] == {"field": "fields"}
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
    assert renamed.body == {"id": sources[0]["id"], "project": "Renamed", "path": str(backlog), "backend": "markdown",
                            "sync_path": None, "primary": "markdown", "markdown_path": str(backlog), "mirror": "none"}
    assert removed.body["path"] == str(second)
    assert (gone.status_code, gone.body["code"]) == (404, "source_gone")
    assert [s["project"] for s in api.get("/api/v2/sources").body] == ["Renamed", "Extra"]


def test_create_backlog(api, workspace):
    existing = workspace.add_backlog("backlog")
    before = (existing / "TODO.md").read_bytes()
    (workspace.repos / "New" / ".git").mkdir(parents=True)
    folder = workspace.repos / "New" / "docs" / "todo"

    created = api.post("/api/v2/backlogs", {"path": str(folder)})
    german = api.post("/api/v2/backlogs", {"path": str(workspace.repos / "Neu"), "project": "Neu",
                                           "language": "de"})
    dup = api.post("/api/v2/backlogs", {"path": str(folder)})
    exists = api.post("/api/v2/backlogs", {"path": str(existing)})
    bad_language = api.post("/api/v2/backlogs", {"path": str(workspace.repos / "X"), "language": "fr"})
    item = api.post("/api/v2/items", {"source_id": created.body["id"], "type": "Epic", "title": "First",
                                      "area": "Core", "goal": "g", "completion_criteria": "c"})

    assert created.status_code == 201
    assert created.body == {"id": created.body["id"], "project": "New", "path": str(folder), "backend": "markdown",
                            "sync_path": None, "primary": "markdown", "markdown_path": str(folder), "mirror": "none"}
    assert sorted(p.name for p in folder.iterdir()) == ["TODO.md", "archive.md", "items"]
    assert "Claude_Harness backlog format version 1" in (folder / "TODO.md").read_text(encoding="utf-8")
    assert (workspace.repos / "Neu" / "TODO.md").read_text(encoding="utf-8").startswith("# Projekt-Backlog\n")
    assert german.body["project"] == "Neu"
    assert (dup.status_code, dup.body["code"]) == (409, "duplicate")
    assert (exists.status_code, exists.body["code"]) == (409, "backlog_exists")
    assert (existing / "TODO.md").read_bytes() == before
    assert (bad_language.status_code, bad_language.body["code"]) == (400, "bad_request")
    assert not (workspace.repos / "X").exists()
    assert (item.status_code, item.body["id"]) == (201, "EPIC-001")
    sources = {s["project"]: s for s in api.get("/api/v2/backlog").body["sources"]}
    assert (sources["New"]["item_count"], sources["New"]["problem"]) == (1, None)
    assert "- `EPIC-001` **First**" in (folder / "TODO.md").read_text(encoding="utf-8")
    assert "No entries." not in (folder / "TODO.md").read_text(encoding="utf-8")


def test_folders_and_ui_state(api, workspace):
    _setup(workspace, "backlog")

    folders = api.get("/api/v2/folders")
    saved = api.put("/api/v2/ui-state", {"view": "tree"})

    assert [d["name"] for d in folders.body["dirs"]] == ["backlog"]
    assert saved.body == api.get("/api/v2/ui-state").body == {"view": "tree"}


def test_old_document_endpoint_is_gone(api, workspace):
    _setup(workspace, "backlog")
    source_id = api.get("/api/v2/sources").body[0]["id"]

    assert api.get(f"/api/v2/sources/{source_id}/document", path="items/TASK-002/notes.md").status_code in (404, 405)


def test_serves_frontend_and_reports_missing_build(api, settings):
    from fastapi.testclient import TestClient

    from todo_viewer.api import create_app
    from todo_viewer.bootstrap import build_container

    index = api._raw.get("/")
    missing = TestClient(create_app(build_container(settings), settings.frontend_dir / "nope")).get("/")

    assert (index.status_code, index.text) == (200, "<!doctype html><title>test</title>")
    assert missing.status_code == 503
    assert "npm --prefix web run build" in missing.text

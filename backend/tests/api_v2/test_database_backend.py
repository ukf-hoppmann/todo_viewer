"""A project stored in the central database works through the same API as a markdown project."""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from tests.conftest import TODAY, ApiClient
from todo_viewer.api import create_app
from todo_viewer.bootstrap import build_container


def _setup(workspace, **config) -> None:
    workspace.config_dir.mkdir(parents=True, exist_ok=True)
    sources = [{"project": "Central", "path": "central", "backend": "database"}]
    (workspace.config_dir / "config.json").write_text(json.dumps({"sources": sources, **config}), encoding="utf-8")


def _create(api, sid: str, type_: str, title: str, **fields) -> dict:
    resp = api.post("/api/v2/items", {"source_id": sid, "type": type_, "title": title, "area": "Core",
                                      "goal": "A goal.", "completion_criteria": "Checked.", **fields})
    assert resp.status_code == 201, resp.body
    return resp.body


def _item(api, sid: str, item_id: str) -> dict:
    return api.get(f"/api/v2/items/{sid}/{item_id}").body


def test_a_database_project_works_end_to_end(api, workspace):
    _setup(workspace)
    sid = api.get("/api/v2/sources").body[0]["id"]
    url = f"/api/v2/items/{sid}"

    assert api.get("/api/v2/backlog").body["items"] == []
    epic = _create(api, sid, "Epic", "Central storage")
    story = _create(api, sid, "Story", "Store items", parent=epic["id"], required_for_parent="Yes")
    task = _create(api, sid, "Task", "Write adapter", parent=story["id"], required_for_parent="Yes",
                   dependencies=[story["id"]])
    assert [epic["id"], story["id"], task["id"]] == ["EPIC-001", "STORY-001", "TASK-001"]

    edited = api.patch(f"{url}/TASK-001", {"version": task["version"], "fields": {"priority": "Urgent"}})
    assert (edited.status_code, edited.body["priority"]) == (200, "Urgent")

    notes = api.post(f"{url}/TASK-001/notes", {"topic": "Design", "decided": ["Keep TASK-001 small"],
                                                "summary": "Adapter for the database."})
    spec = api.put(f"{url}/TASK-001/documents/TASK-001_spec.md", {"content": "# TASK-001 spec\n", "version": None})
    assert (notes.status_code, spec.status_code) == (200, 200), (notes.body, spec.body)

    retyped = api.post(f"{url}/TASK-001/retype", {"version": _item(api, sid, "TASK-001")["version"], "type": "Story"})
    assert retyped.status_code == 200, retyped.body
    assert retyped.body["item"]["id"] == "STORY-002"
    assert [d["name"] for d in retyped.body["item"]["documents"]] == ["STORY-002_notes.md", "STORY-002_spec.md"]
    moved_notes = api.get(f"{url}/STORY-002/documents/STORY-002_notes.md").body
    assert "Keep STORY-002 small" in moved_notes["content"]
    assert api.get(f"{url}/STORY-002/documents/STORY-002_spec.md").body["content"] == "# STORY-002 spec\n"

    done = api.patch(f"{url}/STORY-002", {"version": _item(api, sid, "STORY-002")["version"],
                                          "fields": {"status": "Completed"}, "resolution": "Done"})
    assert (done.status_code, done.body["archived"]) == (200, True), done.body

    deleted = api.delete(f"{url}/STORY-002", version=done.body["version"], cascade="false")
    assert deleted.status_code == 200, deleted.body
    in_trash = api.get("/api/v2/trash", source_id=sid).body
    restored = api.post(f"/api/v2/trash/{sid}/STORY-002/restore", {"version": in_trash[0]["version"]})
    assert (restored.status_code, _item(api, sid, "STORY-002")["deleted"]) == (200, None), restored.body

    again = api.delete(f"{url}/STORY-002", version=_item(api, sid, "STORY-002")["version"], cascade="false")
    purged = api.delete(f"/api/v2/trash/{sid}/STORY-002", version=again.body[0]["version"])
    assert purged.status_code == 200, purged.body
    assert [i["id"] for i in api.get("/api/v2/backlog").body["items"]] == ["EPIC-001", "STORY-001"]

    assert (workspace.config_dir / "todo.db").is_file()
    assert not (workspace.root / "central").exists()


def test_the_database_location_comes_from_the_config_read_at_start(workspace, settings):
    _setup(workspace, storage_url=f"sqlite:///{workspace.root / 'elsewhere.db'}")
    app = create_app(build_container(settings, lambda: TODAY), settings.frontend_dir)

    with TestClient(app) as client:
        api = ApiClient(client, workspace.root)
        _create(api, api.get("/api/v2/sources").body[0]["id"], "Epic", "Somewhere else")

    assert (workspace.root / "elsewhere.db").is_file()
    assert not (workspace.config_dir / "todo.db").exists()


def test_markdown_projects_do_not_create_a_database(api, workspace):
    folder = workspace.add_backlog("backlog")
    workspace.write_config([{"project": "backlog", "path": str(folder)}])

    assert api.get("/api/v2/backlog").status_code == 200
    assert not (workspace.config_dir / "todo.db").exists()

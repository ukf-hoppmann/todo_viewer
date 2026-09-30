"""POST /api/v2/sources/{id}/sync: preview first, then confirm; both directions."""
from __future__ import annotations

from pathlib import Path


def _project(api, workspace, sync: str | None = "md") -> str:
    fields = {"sync_path": str(workspace.root / sync)} if sync else {}
    return api.post("/api/v2/sources", {"backend": "database", "project": "Central", **fields}).body["id"]


def _seed(api, sid: str) -> None:
    epic = api.post("/api/v2/items", {"source_id": sid, "type": "Epic", "title": "Storage", "area": "Core",
                                      "goal": "g", "completion_criteria": "c"}).body
    story = api.post("/api/v2/items", {"source_id": sid, "type": "Story", "title": "Sync", "area": "Core",
                                       "goal": "g", "completion_criteria": "c", "parent": epic["id"],
                                       "required_for_parent": "Yes"}).body
    api.post(f"/api/v2/items/{sid}/{story['id']}/notes", {"topic": "Start", "decided": ["Go"], "summary": "Sum"})


def _sync(api, sid: str, direction: str, **body):
    return api.post(f"/api/v2/sources/{sid}/sync", {"direction": direction, **body})


def test_a_preview_lists_what_would_happen_and_changes_nothing(api, workspace):
    sid = _project(api, workspace)
    _seed(api, sid)

    resp = _sync(api, sid, "to_md")

    assert resp.status_code == 200, resp.body
    body = resp.body
    assert body["executed"] is False and len(body["token"]) > 8
    assert [(e["label"], e["title"]) for e in body["items"]["created"]] == [("EPIC-001", "Storage"),
                                                                            ("STORY-001", "Sync")]
    assert [e["name"] for e in body["documents"]["created"]] == ["STORY-001_notes.md"]
    assert (body["items"]["changed"], body["items"]["unchanged"], body["items"]["missing"]) == ([], 0, [])
    assert not (workspace.root / "md").exists()


def test_confirming_with_the_token_writes_the_folder(api, workspace):
    sid = _project(api, workspace)
    _seed(api, sid)
    token = _sync(api, sid, "to_md").body["token"]

    resp = _sync(api, sid, "to_md", confirm=True, token=token)

    assert resp.status_code == 200, resp.body
    assert resp.body["executed"] is True
    md = Path(workspace.root / "md")
    assert "- `STORY-001` **Sync**" in (md / "TODO.md").read_text(encoding="utf-8")
    assert "Go" in (md / "items" / "STORY-001" / "STORY-001_notes.md").read_text(encoding="utf-8")
    assert _sync(api, sid, "to_md").body["items"]["unchanged"] == 2


def test_a_folder_can_be_imported_into_another_database_project(api, workspace):
    source = _project(api, workspace)
    _seed(api, source)
    _sync(api, source, "to_md", confirm=True, token=_sync(api, source, "to_md").body["token"])
    copy = api.post("/api/v2/sources", {"backend": "database", "project": "Copy",
                                        "sync_path": str(workspace.root / "md")}).body["id"]

    preview = _sync(api, copy, "from_md")
    done = _sync(api, copy, "from_md", confirm=True, token=preview.body["token"])

    assert done.status_code == 200, done.body
    assert [e["label"] for e in preview.body["items"]["created"]] == ["EPIC-001", "STORY-001"]
    ids = {i["id"]: i["version"] for i in api.get("/api/v2/backlog").body["items"] if i["source_id"] == copy}
    original = {i["id"]: i["version"] for i in api.get("/api/v2/backlog").body["items"] if i["source_id"] == source}
    assert ids == original
    assert api.get(f"/api/v2/items/{copy}/STORY-001/documents/STORY-001_notes.md").status_code == 200


def test_missing_entries_are_deleted_only_with_delete_missing(api, workspace):
    source = _project(api, workspace)
    _seed(api, source)
    _sync(api, source, "to_md", confirm=True, token=_sync(api, source, "to_md").body["token"])
    api.post("/api/v2/items", {"source_id": source, "type": "Task", "title": "Only here", "area": "Core",
                               "goal": "g", "completion_criteria": "c"})

    keep = _sync(api, source, "from_md")
    kept = _sync(api, source, "from_md", confirm=True, token=keep.body["token"])
    assert [e["label"] for e in keep.body["items"]["missing"]] == ["TASK-001"]
    assert [e["label"] for e in kept.body["kept"]] == ["TASK-001"] and kept.body["deleted"] == []
    assert api.get(f"/api/v2/items/{source}/TASK-001").status_code == 200

    drop = _sync(api, source, "from_md", confirm=True, token=keep.body["token"], delete_missing=True)
    assert [e["label"] for e in drop.body["deleted"]] == ["TASK-001"]
    assert api.get(f"/api/v2/items/{source}/TASK-001").status_code == 404


def test_a_stale_token_is_refused_and_nothing_is_written(api, workspace):
    sid = _project(api, workspace)
    _seed(api, sid)
    token = _sync(api, sid, "to_md").body["token"]
    api.post("/api/v2/items", {"source_id": sid, "type": "Task", "title": "Late", "area": "Core",
                               "goal": "g", "completion_criteria": "c"})

    resp = _sync(api, sid, "to_md", confirm=True, token=token)
    missing = _sync(api, sid, "to_md", confirm=True)

    assert (resp.status_code, resp.body["code"]) == (409, "sync_stale")
    assert (missing.status_code, missing.body["code"]) == (409, "sync_stale")
    assert not (workspace.root / "md").exists()


def test_errors_have_stable_codes(api, workspace):
    no_path = _project(api, workspace, sync=None)
    md = api.post("/api/v2/sources", {"path": str(workspace.add_backlog("backlog"))}).body["id"]
    empty = _project(api, workspace, sync="nothing-here")

    assert (_sync(api, no_path, "to_md").status_code, _sync(api, no_path, "to_md").body["code"]) == (
        400, "sync_path_missing")
    assert (_sync(api, md, "to_md").status_code, _sync(api, md, "to_md").body["code"]) == (409, "sync_same_backend")
    broken = _sync(api, empty, "from_md")
    assert (broken.status_code, broken.body["code"], broken.body["details"]["reason"]) == (
        400, "sync_source_invalid", "not_found")
    assert _sync(api, "no-such-project", "to_md").body["code"] == "source_gone"
    assert _sync(api, no_path, "sideways").status_code == 400

"""/api/v2 names, for every project with a mirror, which side changed since the last sync; it never syncs by itself."""
from __future__ import annotations

from pathlib import Path


def _central(api, workspace, folder: str | None = "md") -> str:
    fields = {"sync_path": str(workspace.root / folder)} if folder else {}
    sid = api.post("/api/v2/sources", {"backend": "database", "project": "Central", **fields}).body["id"]
    epic = api.post("/api/v2/items", {"source_id": sid, "type": "Epic", "title": "Storage", "area": "Core",
                                      "goal": "g", "completion_criteria": "c"}).body
    api.post(f"/api/v2/items/{sid}/{epic['id']}/notes", {"topic": "Start", "decided": ["Go"], "summary": "Sum"})
    return sid


def _sync(api, sid: str, direction: str) -> None:
    preview = api.post(f"/api/v2/sources/{sid}/sync", {"direction": direction}).body
    done = api.post(f"/api/v2/sources/{sid}/sync", {"direction": direction, "confirm": True, "token": preview["token"]})
    assert done.status_code == 200, done.body


def _state(api, sid: str) -> str:
    listed = next(s for s in api.get("/api/v2/sources").body if s["id"] == sid)["sync"]["state"]
    in_backlog = next(s for s in api.get("/api/v2/backlog").body["sources"] if s["id"] == sid)["sync"]["state"]
    assert listed == in_backlog  # both endpoints tell the same
    return listed


def _edit_folder(workspace) -> None:
    """What an AI does: edits a notes file in the markdown folder."""
    notes = next((workspace.root / "md" / "items").glob("*/*_notes.md"))
    notes.write_text(notes.read_text(encoding="utf-8") + "\nAdded by an AI.\n", encoding="utf-8")


def _retitle(api, sid: str, item_id: str, title: str) -> None:
    url = f"/api/v2/items/{sid}/{item_id}"
    assert api.patch(url, {"version": api.get(url).body["version"], "fields": {"title": title}}).status_code == 200


def test_a_project_without_a_mirror_has_no_sync_state(api, workspace):
    plain = api.post("/api/v2/sources", {"path": str(workspace.add_backlog("backlog"))}).body["id"]
    bare = api.post("/api/v2/sources", {"backend": "database", "project": "Bare"}).body["id"]

    assert [_state(api, plain), _state(api, bare)] == ["none", "none"]
    assert api.get("/api/v2/sources").body[0]["sync"] == {"state": "none", "last_sync_at": None}


def test_a_mirror_that_was_never_synced_is_unknown_and_a_sync_puts_it_in_sync(api, workspace):
    sid = _central(api, workspace)

    assert _state(api, sid) == "unknown"
    assert api.get("/api/v2/sources").body[0]["sync"]["last_sync_at"] is None

    _sync(api, sid, "to_md")

    assert _state(api, sid) == "in_sync"
    assert api.get("/api/v2/sources").body[0]["sync"]["last_sync_at"]


def test_the_folder_of_a_database_project_changed_by_someone_else_is_reported(api, workspace):
    sid = _central(api, workspace)
    _sync(api, sid, "to_md")

    _edit_folder(workspace)
    assert _state(api, sid) == "mirror_changed"

    _retitle(api, sid, "EPIC-001", "Storage, renamed")
    assert _state(api, sid) == "both_changed"

    _sync(api, sid, "from_md")  # the folder wins, the project takes the edit over
    assert _state(api, sid) == "in_sync"

    _retitle(api, sid, "EPIC-001", "Storage, renamed again")
    assert _state(api, sid) == "primary_changed"


def test_a_markdown_project_with_a_database_mirror_reports_the_same_way(api, workspace):
    folder = workspace.add_backlog("backlog")
    sid = api.post("/api/v2/sources", {"path": str(folder), "mirror": "database"}).body["id"]
    assert _state(api, sid) == "unknown"

    _sync(api, sid, "from_md")
    assert _state(api, sid) == "in_sync"

    _retitle(api, sid, "TASK-001", "Edited through the API")  # the primary source (the folder) moves on
    assert _state(api, sid) == "primary_changed"


def test_a_mirror_folder_that_cannot_be_read_is_reported_and_does_not_break_the_list(api, workspace):
    sid = _central(api, workspace)
    _sync(api, sid, "to_md")
    (workspace.root / "md" / "TODO.md").write_text("not a backlog at all\n", encoding="utf-8")

    assert _state(api, sid) == "unreadable"


def test_moving_the_mirror_forgets_the_last_sync(api, workspace):
    sid = _central(api, workspace)
    _sync(api, sid, "to_md")

    moved = api.put(f"/api/v2/sources/{sid}", {"backend": "database", "project": "Central",
                                               "sync_path": str(workspace.root / "elsewhere")}).body

    assert moved["sync"] == {"state": "unknown", "last_sync_at": None}


def test_asking_for_the_state_changes_and_syncs_nothing(api, workspace):
    sid = _central(api, workspace)
    _sync(api, sid, "to_md")
    _edit_folder(workspace)
    files = {p.name: p.read_bytes() for p in Path(workspace.root / "md").rglob("*") if p.is_file()}
    versions = {i["id"]: i["version"] for i in api.get("/api/v2/backlog").body["items"]}

    for _ in range(3):
        assert _state(api, sid) == "mirror_changed"

    assert files == {p.name: p.read_bytes() for p in Path(workspace.root / "md").rglob("*") if p.is_file()}
    assert versions == {i["id"]: i["version"] for i in api.get("/api/v2/backlog").body["items"]}

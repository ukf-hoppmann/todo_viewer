"""Switching the primary source saves the current one first; without a backup nothing is switched."""
from __future__ import annotations

from pathlib import Path


def _sync(api, sid: str, direction: str) -> None:
    preview = api.post(f"/api/v2/sources/{sid}/sync", {"direction": direction}).body
    done = api.post(f"/api/v2/sources/{sid}/sync", {"direction": direction, "confirm": True, "token": preview["token"]})
    assert done.status_code == 200, done.body


def _items(api, sid: str) -> dict[str, str]:
    return {i["id"]: i["version"] for i in api.get("/api/v2/backlog").body["items"] if i["source_id"] == sid}


def _backups(workspace) -> list[Path]:
    return sorted((workspace.config_dir / "backups").glob("*/*"))


def test_the_switch_saves_the_folder_byte_for_byte_and_the_backup_can_be_opened_as_a_project(api, workspace):
    folder = workspace.add_backlog("backlog")
    (folder / "TODO.md").write_bytes((folder / "TODO.md").read_bytes() + b"\n\n  hand written   \n")
    original = {p.name: p.read_bytes() for p in folder.iterdir() if p.is_file()}
    sid = api.post("/api/v2/sources", {"path": str(folder)}).body["id"]
    before = _items(api, sid)
    _sync(api, sid, "from_md")

    switched = api.put(f"/api/v2/sources/{sid}", {"backend": "database"})

    assert switched.status_code == 200, switched.body
    [backup] = _backups(workspace)
    assert {p.name: p.read_bytes() for p in backup.iterdir() if p.is_file()} == original
    opened = api.post("/api/v2/sources", {"path": str(backup), "project": "Restored"})
    assert opened.status_code == 200, opened.body
    assert _items(api, opened.body["id"]) == before


def test_the_switch_back_exports_the_database_and_the_backup_holds_the_old_state(api, workspace):
    folder = workspace.add_backlog("backlog")
    sid = api.post("/api/v2/sources", {"path": str(folder)}).body["id"]
    _sync(api, sid, "from_md")
    api.put(f"/api/v2/sources/{sid}", {"backend": "database"})
    url = f"/api/v2/items/{sid}/TASK-001"
    api.patch(url, {"version": api.get(url).body["version"], "fields": {"priority": "Urgent"}})
    before = _items(api, sid)
    _sync(api, sid, "to_md")

    back = api.put(f"/api/v2/sources/{sid}", {"backend": "markdown"})

    assert back.status_code == 200, back.body
    assert len(_backups(workspace)) == 2
    opened = api.post("/api/v2/sources", {"path": str(_backups(workspace)[-1]), "project": "Restored"})
    assert opened.status_code == 200, opened.body
    assert _items(api, opened.body["id"]) == before


def test_without_a_backup_nothing_is_switched_and_the_reason_is_named(api, workspace):
    folder = workspace.add_backlog("backlog")
    sid = api.post("/api/v2/sources", {"path": str(folder)}).body["id"]
    _sync(api, sid, "from_md")
    workspace.config_dir.joinpath("backups").write_text("a file, not a folder", encoding="utf-8")

    refused = api.put(f"/api/v2/sources/{sid}", {"backend": "database"})

    assert (refused.status_code, refused.body["code"]) == (409, "backup_failed")
    assert refused.body["details"]["reason"] and "backup" in refused.body["message"]
    assert api.get("/api/v2/sources").body[0]["primary"] == "markdown"


def test_a_switch_that_is_refused_for_other_reasons_makes_no_backup(api, workspace):
    sid = api.post("/api/v2/sources", {"path": str(workspace.add_backlog("backlog"))}).body["id"]

    early = api.put(f"/api/v2/sources/{sid}", {"backend": "database"})  # the two sides differ

    assert (early.status_code, early.body["code"]) == (409, "sync_required")
    assert _backups(workspace) == []


def test_an_ordinary_change_makes_no_backup(api, workspace):
    sid = api.post("/api/v2/sources", {"path": str(workspace.add_backlog("backlog"))}).body["id"]

    api.put(f"/api/v2/sources/{sid}", {"path": api.get("/api/v2/sources").body[0]["path"], "project": "Renamed"})

    assert _backups(workspace) == []

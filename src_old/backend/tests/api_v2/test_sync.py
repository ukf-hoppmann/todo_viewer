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
    assert (body["items"]["changed"], body["items"]["unchanged"], body["conflicts"]) == ([], 0, [])
    assert {e["origin"] for e in body["items"]["created"]} == {"database"}
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


def _synced_central(api, workspace) -> str:
    sid = _project(api, workspace)
    _seed(api, sid)
    _sync(api, sid, "to_md", confirm=True, token=_sync(api, sid, "to_md").body["token"])
    return sid


def _retitle(api, sid: str, label: str, title: str) -> None:
    url = f"/api/v2/items/{sid}/{label}"
    assert api.patch(url, {"version": api.get(url).body["version"], "fields": {"title": title}}).status_code == 200


def _retitle_in_folder(workspace, old: str, new: str) -> None:
    todo = workspace.root / "md" / "TODO.md"
    todo.write_text(todo.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def _title(api, sid: str, label: str) -> str:
    return api.get(f"/api/v2/items/{sid}/{label}").body["title"]


def test_without_a_direction_each_entry_travels_from_the_side_that_changed_it(api, workspace):
    sid = _synced_central(api, workspace)
    _retitle(api, sid, "EPIC-001", "Epic in the database")
    _retitle_in_folder(workspace, "**Sync**", "**Story in the file**")

    preview = api.post(f"/api/v2/sources/{sid}/sync", {}).body
    done = api.post(f"/api/v2/sources/{sid}/sync", {"confirm": True, "token": preview["token"]})

    assert {(e["label"], e["origin"]) for e in preview["items"]["changed"]} == {("EPIC-001", "database"),
                                                                              ("STORY-001", "markdown")}
    assert preview["conflicts"] == [] and done.status_code == 200, done.body
    assert {(e["label"], e["origin"]) for e in done.body["resolved"]} == {("EPIC-001", "database"),
                                                                        ("STORY-001", "markdown")}
    assert _title(api, sid, "STORY-001") == "Story in the file"
    assert "**Epic in the database**" in (workspace.root / "md" / "TODO.md").read_text(encoding="utf-8")


def test_a_conflict_shows_both_versions_and_is_decided_per_entry(api, workspace):
    sid = _synced_central(api, workspace)
    _retitle(api, sid, "STORY-001", "In the database")
    _retitle_in_folder(workspace, "**Sync**", "**In the file**")
    _retitle(api, sid, "EPIC-001", "Free change")
    url = f"/api/v2/sources/{sid}/sync"

    preview = api.post(url, {}).body
    [conflict] = preview["conflicts"]
    assert (conflict["kind"], conflict["label"], conflict["reason"]) == ("item", "STORY-001", "both_changed")
    assert {f["name"]: f["value"] for f in conflict["database"]["fields"]}["title"] == "In the database"
    assert {f["name"]: f["value"] for f in conflict["markdown"]["fields"]}["title"] == "In the file"

    left = api.post(url, {"confirm": True, "token": preview["token"]}).body  # no decision: deferred
    assert [e["label"] for e in left["deferred"]] == ["STORY-001"]
    assert _title(api, sid, "STORY-001") == "In the database"
    assert [e["label"] for e in api.post(url, {}).body["conflicts"]] == ["STORY-001"]

    preview = api.post(url, {}).body
    decided = api.post(url, {"confirm": True, "token": preview["token"], "resolutions": [
        {"kind": "item", "label": "STORY-001", "choice": "markdown"}]})

    assert decided.status_code == 200 and decided.body["deferred"] == []
    assert _title(api, sid, "STORY-001") == "In the file"
    assert api.post(url, {}).body["conflicts"] == []


def test_a_deletion_is_never_carried_out_without_a_decision(api, workspace):
    sid = _synced_central(api, workspace)
    (workspace.root / "md" / "items" / "STORY-001" / "STORY-001_notes.md").unlink()
    url = f"/api/v2/sources/{sid}/sync"

    preview = api.post(url, {}).body
    done = api.post(url, {"confirm": True, "token": preview["token"]}).body

    assert [(c["kind"], c["name"], c["reason"]) for c in preview["conflicts"]] == [
        ("document", "STORY-001_notes.md", "markdown_deleted")]
    assert [e["name"] for e in done["kept"]] == ["STORY-001_notes.md"] and done["deleted"] == []
    assert api.get(f"/api/v2/items/{sid}/STORY-001/documents/STORY-001_notes.md").status_code == 200


def test_delete_missing_is_gone_and_a_wrong_choice_is_refused(api, workspace):
    sid = _synced_central(api, workspace)
    url = f"/api/v2/sources/{sid}/sync"

    gone = api.post(url, {"delete_missing": True})
    wrong = api.post(url, {"resolutions": [{"kind": "item", "label": "X", "choice": "both"}]})

    assert gone.status_code == 400 and wrong.status_code == 400


def test_the_status_counts_open_conflicts(api, workspace):
    sid = _synced_central(api, workspace)
    _retitle(api, sid, "STORY-001", "In the database")
    _retitle_in_folder(workspace, "**Sync**", "**In the file**")

    assert api.get(f"/api/v2/sources/{sid}/sync-status").body["conflicts"] == 1


def test_a_sync_into_the_database_leaves_a_backup_of_the_database(api, workspace):
    source = _project(api, workspace)
    _seed(api, source)
    _sync(api, source, "to_md", confirm=True, token=_sync(api, source, "to_md").body["token"])
    copy = api.post("/api/v2/sources", {"backend": "database", "project": "Copy",
                                        "sync_path": str(workspace.root / "md")}).body["id"]

    _sync(api, copy, "from_md", confirm=True, token=_sync(api, copy, "from_md").body["token"])

    backups = [p.name for p in (workspace.config_dir / "backups").iterdir()]
    assert len(backups) == 1 and backups[0].startswith("todo-") and backups[0].endswith("-sync.db")


def test_a_failed_database_backup_stops_the_sync_with_its_code(api, workspace):
    source = _project(api, workspace)
    _seed(api, source)
    _sync(api, source, "to_md", confirm=True, token=_sync(api, source, "to_md").body["token"])
    copy = api.post("/api/v2/sources", {"backend": "database", "project": "Copy",
                                        "sync_path": str(workspace.root / "md")}).body["id"]
    token = _sync(api, copy, "from_md").body["token"]
    (workspace.config_dir / "backups").write_text("a file where the folder should be")

    resp = _sync(api, copy, "from_md", confirm=True, token=token)

    assert resp.status_code == 409 and resp.body["code"] == "database_backup_failed"
    assert api.get(f"/api/v2/items/{copy}/STORY-001").status_code == 404

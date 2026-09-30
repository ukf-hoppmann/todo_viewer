"""POST /api/v2/items/{source}/{id}/retype: the type is the id's prefix, so the id and every reference change."""
from __future__ import annotations


def _setup(workspace):
    folder = workspace.add_backlog("backlog")
    workspace.write_config([{"project": "backlog", "path": str(folder)}])
    return folder


def _item(api, item_id: str) -> dict:
    return next(i for i in api.get("/api/v2/backlog").body["items"] if i["id"] == item_id)


def _retype(api, item: dict, new_type: str, version: str | None = None):
    return api.post(f"/api/v2/items/{item['source_id']}/{item['id']}/retype",
                    {"version": version or item["version"], "type": new_type})


def _files(folder) -> dict[str, str]:
    return {str(p.relative_to(folder)): p.read_text(encoding="utf-8") for p in sorted(folder.rglob("*.md"))}


def test_retype_moves_item_documents_and_references(api, workspace):
    folder = _setup(workspace)
    task = _item(api, "TASK-002")

    resp = _retype(api, task, "Story")

    assert resp.status_code == 200, resp.body
    item = resp.body["item"]
    assert (item["id"], item["type"], resp.body["old_id"]) == ("STORY-002", "Story", "TASK-002")
    assert [(n["code"], n["details"]) for n in resp.body["notices"]] == [
        ("external_references_may_remain", {"old_id": "TASK-002", "new_id": "STORY-002"})]
    assert [d["name"] for d in resp.body["item"]["documents"]] == ["notes.md", "spec.md", "extra.md"]
    todo = (folder / "TODO.md").read_text(encoding="utf-8")
    assert "Notes: `items/STORY-002/notes.md`." in todo
    assert "Spec: `items/STORY-002/spec.md`, `items/STORY-002/extra.md`." in todo
    assert resp.body["item"] == _item(api, "STORY-002")
    assert api.get(f"/api/v2/items/{task['source_id']}/TASK-002").body["code"] == "item_not_found"
    assert not (folder / "items" / "TASK-002").exists()
    text = api.get(f"/api/v2/items/{task['source_id']}/STORY-002/documents/notes.md").body["content"]
    assert text.startswith("# Notes for STORY-002")
    assert "TASK-002" not in "".join(_files(folder).values()).replace("items/TASK-002", "")


def test_retype_renames_parent_and_dependency_references(api, workspace):
    folder = _setup(workspace)
    story = _item(api, "STORY-001")

    resp = _retype(api, story, "Task")

    assert (resp.status_code, resp.body["item"]["id"]) == (200, "TASK-004")
    assert {i["id"]: i["parent"] for i in api.get("/api/v2/backlog").body["items"] if i["id"] in
            {"TASK-001", "TASK-002", "TASK-003"}} == {"TASK-001": "TASK-004", "TASK-002": "TASK-004",
                                                      "TASK-003": "TASK-004"}
    assert "STORY-001" not in (folder / "TODO.md").read_text(encoding="utf-8")


def test_retype_archived_item_keeps_its_place_in_the_archive(api, workspace):
    folder = _setup(workspace)
    task = _item(api, "TASK-000")

    resp = _retype(api, task, "Story")

    assert (resp.status_code, resp.body["item"]["id"], resp.body["item"]["archived"]) == (200, "STORY-002", True)
    archive = (folder / "archive.md").read_text(encoding="utf-8")
    assert "`STORY-002` **Set up repository**" in archive and "`TASK-000`" not in archive
    assert "TASK-000" not in (folder / "TODO.md").read_text(encoding="utf-8")  # TASK-001 depended on it


def test_retype_errors_leave_the_files_untouched(api, workspace):
    folder = _setup(workspace)
    before = _files(folder)
    task, source_id = _item(api, "TASK-001"), _item(api, "TASK-001")["source_id"]

    cases = [
        (400, "invalid_value", _retype(api, task, "Task")),  # same type
        (400, "invalid_value", _retype(api, task, "Bug")),
        (409, "version_conflict", _retype(api, task, "Story", version="stale")),
        (409, "epic_with_parent", _retype(api, task, "Epic")),  # an epic has no parent
        (404, "item_not_found", api.post(f"/api/v2/items/{source_id}/TASK-404/retype",
                                        {"version": "x", "type": "Story"})),
        (404, "source_gone", api.post("/api/v2/items/nope/TASK-001/retype", {"version": "x", "type": "Story"})),
    ]

    assert [(r.status_code, r.body["code"]) for _, _, r in cases] == [(s, c) for s, c, _ in cases]
    assert _files(folder) == before


def test_retype_refuses_items_in_the_trash(api, workspace):
    folder = _setup(workspace)
    task = _item(api, "TASK-003")
    deleted = api.delete(f"/api/v2/items/{task['source_id']}/TASK-003", version=task["version"], cascade="false")
    trashed = api.get("/api/v2/trash", source_id=task["source_id"]).body[0]
    before = _files(folder)

    resp = _retype(api, trashed, "Story")

    assert deleted.status_code == 200
    assert (resp.status_code, resp.body["code"]) == (409, "item_deleted")
    assert _files(folder) == before


def test_a_plain_edit_still_cannot_change_the_type(api, workspace):
    _setup(workspace)
    task = _item(api, "TASK-001")

    resp = api.patch(f"/api/v2/items/{task['source_id']}/TASK-001",
                     {"version": task["version"], "fields": {"type": "Story"}})

    assert (resp.status_code, resp.body["code"]) == (400, "bad_request")

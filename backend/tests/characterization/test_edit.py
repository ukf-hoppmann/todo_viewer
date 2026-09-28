"""Characterization tests: pin how edits and archiving rewrite the markdown files.

The .md goldens were recorded with the original implementation (before the refactoring)
and must stay byte-identical.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from todo_viewer.domain.editing import EditPlanner
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown import build_markdown_repository


def _setup(workspace, fixture: str) -> Path:
    folder = workspace.add_backlog(fixture)
    workspace.write_config([{"project": "P", "path": str(folder)}])
    return folder


def _item(api, item_id: str) -> dict:
    items = api.get("/api/v2/backlog").body["items"]
    return next(i for i in items if i["id"] == item_id)


def _update(api, item: dict, field: str, value, resolution: str | None = None, source_id: str | None = None,
            item_id: str | None = None, **body_override):
    body = {"version": item["version"], "fields": {field: value}, "resolution": resolution, **body_override}
    return api.patch(f"/api/v2/items/{source_id or item['source_id']}/{item_id or item['id']}", body)


def _files(folder: Path) -> str:
    """All backlog files of a folder in one string, for a single golden comparison."""
    parts = []
    for name in ("TODO.md", "archive.md"):
        path = folder / name
        if path.exists():
            parts.append(f"===== {name} =====\n{path.read_bytes().decode('utf-8')}")
    return "".join(parts)


EDIT_CASES = [
    # (golden name, fixture, item id, field, value, resolution, archived afterwards)
    ("priority_existing", "backlog", "TASK-001", "priority", "Urgent", None, False),
    ("priority_inserted", "backlog", "TASK-003", "priority", "Prospective.", None, False),
    ("status_active", "backlog", "STORY-001", "status", "In progress", None, False),
    ("complete_to_archive", "backlog", "TASK-001", "status", "Completed", "Merged in PR 1", True),
    ("complete_last_entry", "backlog", "TASK-003", "status", "Rejected", "Obsolete", True),
    ("complete_into_empty_archive", "empty_archive", "TASK-020", "status", "Completed", "Done", True),
    ("reopen_from_archive", "backlog", "TASK-000", "status", "Open", None, False),
    ("reopen_last_archive_entry", "backlog", "STORY-000", "status", "In progress", None, False),
    ("terminal_within_archive", "backlog", "STORY-000", "status", "Completed", "Needed after all", True),
    ("required_existing", "backlog", "TASK-002", "required_for_parent", "Yes", None, False),
    ("required_inserted", "backlog", "TASK-003", "required_for_parent", "No", None, False),
    ("priority_in_archive", "backlog", "TASK-000", "priority", "Important", None, True),
    ("complete_without_archive", "no_archive", "TASK-010", "status", "Completed", None, False),
]


@pytest.mark.parametrize(("name", "fixture", "item_id", "field", "value", "resolution", "archived"), EDIT_CASES,
                         ids=[c[0] for c in EDIT_CASES])
def test_edit_rewrites_files(api, workspace, golden, name, fixture, item_id, field, value, resolution, archived):
    folder = _setup(workspace, fixture)

    resp = _update(api, _item(api, item_id), field, value, resolution)

    assert resp.status_code == 200, resp.body
    golden(f"edit/{name}.md", _files(folder))
    assert resp.body["archived"] is archived
    expected = {"priority": value.rstrip("."), "required_for_parent": value == "Yes"}.get(field, value)
    assert resp.body[field] == expected
    assert resp.body == _item(api, item_id)


def test_complete_first_entry_file_mechanics(workspace, golden):
    """Cutting the first entry; below the API because closing EPIC-001 breaks a lifecycle rule."""
    folder = _setup(workspace, "backlog")
    repo = build_markdown_repository(Path("/"))
    source = Source("P", str(folder))
    item = repo.get(source, "EPIC-001")

    repo.apply(source, item, EditPlanner().plan(item, {"status": "Completed"}, "All done.", archive_supported=True))

    golden("edit/complete_first_entry.md", _files(folder))


def test_lifecycle_violation_is_rejected_and_files_stay_untouched(api, workspace):
    folder = _setup(workspace, "backlog")
    before = _files(folder)

    epic = _update(api, _item(api, "EPIC-001"), "status", "Completed", "All done.")
    story = _update(api, _item(api, "STORY-001"), "status", "Awaiting confirmation")

    assert (epic.status_code, epic.body["code"]) == (409, "children_still_active")
    assert epic.body["details"] == {"id": "EPIC-001", "items": "STORY-001"}
    assert (story.status_code, story.body["code"]) == (409, "required_children_not_done")
    assert story.body["details"] == {"id": "STORY-001", "items": "TASK-001"}
    assert _files(folder) == before


def _patch(api, item: dict, fields: dict, resolution: str | None = None):
    return api.patch(f"/api/v2/items/{item['source_id']}/{item['id']}",
                     {"version": item["version"], "fields": fields, "resolution": resolution})


def test_free_fields_rewrite_files(api, workspace, golden):
    folder = _setup(workspace, "backlog")

    resp = _patch(api, _item(api, "TASK-003"), {
        "title": "Renamed task",
        "goal": "A goal that is long enough to need more than one line in the file, so it wraps like "
                "the backlog format expects.",
        "completion_criteria": "Checked by a test.",
        "summary": "Short summary.",
        "area": "Parser",
        "dependencies": ["TASK-001", "TASK-000"],
        "required_for_parent": "No",
    })

    assert resp.status_code == 200, resp.body
    golden("edit/free_fields.md", _files(folder))
    assert (resp.body["title"], resp.body["dependencies"], resp.body["required_for_parent"]) == \
        ("Renamed task", ["TASK-001", "TASK-000"], False)
    assert resp.body == _item(api, "TASK-003")


def test_parent_changes(api, workspace):
    _setup(workspace, "backlog")

    moved = _patch(api, _item(api, "TASK-002"), {"parent": "EPIC-001", "required_for_parent": "Yes"})
    standalone = _patch(api, _item(api, "TASK-003"), {"parent": None})

    assert (moved.status_code, moved.body["parent"], moved.body["required_for_parent"]) == (200, "EPIC-001", True)
    assert (standalone.status_code, standalone.body["parent"], standalone.body["required_for_parent"]) == \
        (200, None, None)


def test_rule_violations_of_free_fields(api, workspace):
    folder = _setup(workspace, "backlog")
    before = _files(folder)

    cases = [
        ("unknown_reference", "TASK-001", {"parent": "STORY-999"}),
        ("unknown_reference", "TASK-001", {"dependencies": ["NOPE"]}),
        ("epic_with_parent", "EPIC-001", {"parent": "STORY-001"}),
        ("dependency_cycle", "TASK-000", {"dependencies": ["TASK-002"]}),
        ("invalid_value", "TASK-001", {"parent": "not an id"}),
    ]
    for code, item_id, fields in cases:
        resp = _patch(api, _item(api, item_id), fields)
        assert resp.body.get("code") == code, (code, item_id, resp.body)

    assert _files(folder) == before


def test_summary_cannot_be_removed_while_notes_exist(api, workspace):
    _setup(workspace, "backlog")

    added = _patch(api, _item(api, "TASK-002"), {"summary": "Explains the polish."})
    removed = _patch(api, _item(api, "TASK-002"), {"summary": None})

    assert added.status_code == 200, added.body
    assert (removed.status_code, removed.body["code"]) == (409, "summary_required_with_notes")


def test_parent_cycle_is_rejected(api, workspace):
    _setup(workspace, "backlog")

    first = _patch(api, _item(api, "TASK-002"), {"parent": "TASK-003"})
    cycle = _patch(api, _item(api, "TASK-003"), {"parent": "TASK-002", "required_for_parent": "No"})

    assert first.status_code == 200, first.body
    assert (cycle.status_code, cycle.body["code"]) == (409, "parent_cycle")
    assert cycle.body["details"] == {"id": "TASK-002", "items": "TASK-002, TASK-003"}


@pytest.mark.parametrize(("name", "fixture", "body"), [
    ("create_task", "backlog", {"type": "Task", "parent": "STORY-001", "required_for_parent": "No",
                                "dependencies": ["TASK-001"], "summary": "Short.", "priority": "Important"}),
    ("create_epic_at_file_end", "empty_archive", {"type": "Epic"}),
], ids=["create_task", "create_epic_at_file_end"])
def test_create_writes_entry(api, workspace, golden, name, fixture, body):
    folder = _setup(workspace, fixture)
    source_id = api.get("/api/v2/sources").body[0]["id"]

    resp = api.post("/api/v2/items", {"source_id": source_id, "title": "Created entry", "area": "Core",
                                      "goal": "A goal that is long enough to need more than one line in the "
                                              "file, so it wraps like the backlog format expects.",
                                      "completion_criteria": "Checked.", "created": "2026-09-28", **body})

    assert resp.status_code == 201, resp.body
    golden(f"edit/{name}.md", _files(folder))


def _docs(api, item_id: str) -> str:
    return f"/api/v2/items/{api.get('/api/v2/sources').body[0]['id']}/{item_id}"


def test_first_notes_entry_creates_file_and_fields(api, workspace, golden):
    folder = _setup(workspace, "backlog")
    url = _docs(api, "TASK-001")

    without_summary = api.post(f"{url}/notes", {"topic": "Design", "decided": ["Use regex"]})
    first = api.post(f"{url}/notes", {"topic": "Design", "discussed": ["Regex or parser"],
                                       "decided": ["Use regex"], "summary": "Parses the files."})
    second = api.post(f"{url}/notes", {"topic": "Follow-up", "open": ["Error messages"]})

    assert (without_summary.status_code, without_summary.body["code"]) == (409, "summary_required_with_notes")
    assert first.status_code == 200, first.body
    assert second.body["name"] == "TASK-001_notes.md"
    notes = (folder / "items" / "TASK-001" / "TASK-001_notes.md").read_text(encoding="utf-8")
    assert notes == second.body["content"]
    assert notes.startswith("# TASK-001 — Write the parser\n\n## ") and "\n### Open\n\n- Error messages\n" in notes
    item = _item(api, "TASK-001")
    assert (item["summary"], item["documents"]) == \
        ("Parses the files.", [{"name": "TASK-001_notes.md", "kind": "notes"}])
    golden("edit/notes_fields.md", _files(folder))


def test_spec_create_replace_and_conflicts(api, workspace):
    folder = _setup(workspace, "backlog")
    url = _docs(api, "TASK-001")

    created = api.put(f"{url}/documents/TASK-001_spec.md", {"content": "# Spec\n", "version": None})
    again = api.put(f"{url}/documents/TASK-001_spec.md", {"content": "# Other\n", "version": None})
    stale = api.put(f"{url}/documents/TASK-001_spec.md", {"content": "# Other\n", "version": "outdated"})
    replaced = api.put(f"{url}/documents/TASK-001_spec.md", {"content": "# Spec v2\n",
                                                              "version": created.body["version"]})
    bad_name = api.put(f"{url}/documents/spec.md", {"content": "x", "version": None})
    notes = api.put(f"{_docs(api, 'TASK-002')}/documents/notes.md", {"content": "x", "version": None})

    assert created.status_code == 200, created.body
    assert (again.status_code, again.body["code"]) == (409, "version_conflict")
    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    assert replaced.body["content"] == "# Spec v2\n"
    assert (folder / "items" / "TASK-001" / "TASK-001_spec.md").read_text(encoding="utf-8") == "# Spec v2\n"
    assert _item(api, "TASK-001")["documents"] == [{"name": "TASK-001_spec.md", "kind": "spec"}]
    assert api.get(f"{url}/documents/TASK-001_spec.md").body == replaced.body
    assert (bad_name.status_code, bad_name.body["code"]) == (400, "invalid_value")
    assert (notes.status_code, notes.body["code"]) == (400, "not_editable")


def test_edit_twice_reopen_after_archive(api, workspace, golden):
    folder = _setup(workspace, "backlog")

    _update(api, _item(api, "TASK-002"), "status", "Completed", "Done")
    resp = _update(api, _item(api, "TASK-002"), "status", "Open")

    assert resp.status_code == 200
    golden("edit/roundtrip_archive_and_back.md", _files(folder))


def test_edit_preserves_crlf(api, workspace):
    folder = _setup(workspace, "backlog")
    for name in ("TODO.md", "archive.md"):
        path = folder / name
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))

    resp = _update(api, _item(api, "TASK-001"), "status", "Completed", "Done")

    assert resp.status_code == 200
    for name in ("TODO.md", "archive.md"):
        data = (folder / name).read_bytes()
        assert b"\r\n" in data
        assert b"\n" not in data.replace(b"\r\n", b"")


def test_edit_errors_leave_files_untouched(api, workspace):
    folder = _setup(workspace, "backlog")
    item = _item(api, "TASK-001")
    before = _files(folder)

    cases = [
        ("resolution_required", 400, dict(field="status", value="Completed")),
        ("resolution_required", 400, dict(field="status", value="Rejected", resolution="  ")),
        ("bad_request", 400, dict(field="created", value="2026-01-01")),
        ("value_required", 400, dict(field="title", value="  ")),
        ("invalid_value", 400, dict(field="required_for_parent", value="Maybe")),
        ("version_conflict", 409, dict(field="status", value="Open", version="outdated")),
        ("item_not_found", 404, dict(field="status", value="Open", item_id="TASK-999")),
        ("item_not_found", 404, dict(field="status", value="Open", item_id="NOT-AN-ENTRY")),
        ("source_gone", 404, dict(field="status", value="Open", source_id="unknown")),
        ("value_required", 400, dict(field="status", value=None)),
        ("bad_request", 400, dict(field="status", value="Open", version=None)),
    ]
    for code, status, override in cases:
        field = override.pop("field")
        value = override.pop("value")
        resolution = override.pop("resolution", None)
        resp = _update(api, item, field, value, resolution, **override)
        assert (resp.status_code, resp.body.get("code")) == (status, code), (code, override)

    assert _files(folder) == before


def test_external_change_of_the_item_is_a_version_conflict(api, workspace):
    folder = _setup(workspace, "backlog")
    item = _item(api, "TASK-001")
    todo = folder / "TODO.md"
    todo.write_text(todo.read_text(encoding="utf-8").replace("- `TASK-001` **", "- `TASK-001` **Renamed "),
                    encoding="utf-8")
    before = _files(folder)

    resp = _update(api, item, "status", "In progress")

    assert (resp.status_code, resp.body["code"]) == (409, "version_conflict")
    assert _files(folder) == before


def test_external_change_of_another_item_does_not_block_the_edit(api, workspace):
    folder = _setup(workspace, "backlog")
    item = _item(api, "TASK-001")
    todo = folder / "TODO.md"
    todo.write_text("<!-- inserted line shifts every entry -->\n" + todo.read_text(encoding="utf-8"),
                    encoding="utf-8")

    resp = _update(api, item, "status", "In progress")

    assert resp.status_code == 200, resp.body
    assert resp.body["status"] == "In progress"


def test_edit_rejects_non_object(api, workspace):
    _setup(workspace, "backlog")
    item = _item(api, "TASK-001")

    resp = api.patch(f"/api/v2/items/{item['source_id']}/TASK-001", [1, 2])

    assert (resp.status_code, resp.body["code"]) == (400, "bad_request")


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores folder permissions")
def test_write_failure_is_reported_and_files_stay_intact(api, workspace):
    folder = _setup(workspace, "backlog")
    item = _item(api, "TASK-001")
    before = _files(folder)
    folder.chmod(0o555)  # no new (temp) files in the backlog folder
    try:
        resp = _update(api, item, "status", "Completed", "Done")
    finally:
        folder.chmod(0o755)

    assert (resp.status_code, resp.body["code"]) == (500, "write_failed")
    assert _files(folder) == before

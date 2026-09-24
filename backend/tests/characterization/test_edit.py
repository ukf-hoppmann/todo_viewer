"""Characterization tests: pin how edits and archiving rewrite the markdown files.

The .md goldens were recorded with the original implementation (before the refactoring)
and must stay byte-identical.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


def _setup(workspace, fixture: str) -> Path:
    folder = workspace.add_backlog(fixture)
    workspace.write_config([{"project": "P", "path": str(folder)}])
    return folder


def _item(api, item_id: str) -> dict:
    items = api.get("/api/v2/backlog").body["items"]
    return next(i for i in items if i["ref"]["id"] == item_id)


def _update(api, item: dict, field: str, value, resolution: str | None = None, **ref_override):
    body = {"ref": {**item["ref"], **ref_override}, "field": field, "value": value, "resolution": resolution}
    return api.post("/api/v2/items/edit", body)


def _files(folder: Path) -> str:
    """All backlog files of a folder in one string, for a single golden comparison."""
    parts = []
    for name in ("TODO.md", "archive.md"):
        path = folder / name
        if path.exists():
            parts.append(f"===== {name} =====\n{path.read_bytes().decode('utf-8')}")
    return "".join(parts)


EDIT_CASES = [
    # (golden name, fixture, item id, field, value, resolution, location afterwards)
    ("priority_existing", "backlog", "TASK-001", "priority", "Urgent", None, "active"),
    ("priority_inserted", "backlog", "TASK-003", "priority", "Prospective.", None, "active"),
    ("status_active", "backlog", "STORY-001", "status", "In progress", None, "active"),
    ("complete_to_archive", "backlog", "TASK-001", "status", "Completed", "Merged in PR 1", "archive"),
    ("complete_last_entry", "backlog", "TASK-003", "status", "Rejected", "Obsolete", "archive"),
    ("complete_first_entry", "backlog", "EPIC-001", "status", "Completed", "All done.", "archive"),
    ("complete_into_empty_archive", "empty_archive", "TASK-020", "status", "Completed", "Done", "archive"),
    ("reopen_from_archive", "backlog", "TASK-000", "status", "Open", None, "active"),
    ("reopen_last_archive_entry", "backlog", "STORY-000", "status", "In progress", None, "active"),
    ("terminal_within_archive", "backlog", "STORY-000", "status", "Completed", "Needed after all", "archive"),
    ("required_existing", "backlog", "TASK-002", "required_for_parent", "Yes", None, "active"),
    ("required_inserted", "backlog", "TASK-003", "required_for_parent", "No", None, "active"),
    ("priority_in_archive", "backlog", "TASK-000", "priority", "Important", None, "archive"),
    ("complete_without_archive", "no_archive", "TASK-010", "status", "Completed", None, "active"),
    ("checkbox_check", "checklist", "TODO:5", "status", "Completed", None, "active"),
    ("checkbox_uncheck", "checklist", "TODO:4", "status", "Open", None, "active"),
]


@pytest.mark.parametrize(("name", "fixture", "item_id", "field", "value", "resolution", "location"), EDIT_CASES,
                         ids=[c[0] for c in EDIT_CASES])
def test_edit_rewrites_files(api, workspace, golden, name, fixture, item_id, field, value, resolution, location):
    folder = _setup(workspace, fixture)

    resp = _update(api, _item(api, item_id), field, value, resolution)

    assert resp.status_code == 200, resp.body
    golden(f"edit/{name}.md", _files(folder))
    assert resp.body["ref"]["location"] == location
    expected = {"priority": value.rstrip("."), "required_for_parent": value == "Yes"}.get(field, value)
    assert resp.body[field] == expected
    assert resp.body == _item(api, item_id)


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
        ("bad_request", 400, dict(field="title", value="x")),
        ("invalid_value", 400, dict(field="required_for_parent", value="Maybe")),
        ("entry_moved", 409, dict(field="status", value="Open", line=item["ref"]["line"] + 1)),
        ("entry_moved", 409, dict(field="status", value="Open", line=9999)),
        ("entry_moved", 409, dict(field="status", value="Open", id="TASK-999")),
        ("entry_moved", 409, dict(field="status", value="Open", location="archive")),
        ("source_gone", 404, dict(field="status", value="Open", source_id="unknown")),
        ("bad_request", 400, dict(field="status", value=None)),
        ("bad_request", 400, dict(field="status", value="Open", line="3x")),
    ]
    for code, status, override in cases:
        field = override.pop("field")
        value = override.pop("value")
        resolution = override.pop("resolution", None)
        resp = _update(api, item, field, value, resolution, **override)
        assert (resp.status_code, resp.body.get("code")) == (status, code), (code, override)

    assert _files(folder) == before


def test_checkbox_only_status(api, workspace):
    _setup(workspace, "checklist")

    resp = _update(api, _item(api, "TODO:3"), "priority", "Urgent")

    assert (resp.status_code, resp.body["code"]) == (400, "checkbox_status_only")


def test_edit_rejects_non_object(api):
    resp = api.post("/api/v2/items/edit", [1, 2])

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

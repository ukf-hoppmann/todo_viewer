"""Characterization tests: pin how edits and archiving rewrite the markdown files."""
from __future__ import annotations

from pathlib import Path

import pytest


def _setup(api, workspace, fixture: str) -> Path:
    folder = workspace.add_backlog(fixture)
    workspace.write_config([{"project": "P", "path": str(folder)}])
    return folder


def _item(api, item_id: str) -> dict:
    items = api.get("/api/data").body["items"]
    return next(i for i in items if i["id"] == item_id)


def _update(api, item: dict, field: str, value: str, resolution: str | None = None, **override):
    body = {
        "source_file": item["source_file"],
        "line": item["line"],
        "id": item["id"],
        "project": item["project"],
        "format": item["format"],
        "field": field,
        "value": value,
        "resolution": resolution,
        **override,
    }
    return api.post("/api/items/update", body)


def _files(folder: Path) -> str:
    """All backlog files of a folder in one string, for a single golden comparison."""
    parts = []
    for name in ("TODO.md", "archive.md"):
        path = folder / name
        if path.exists():
            parts.append(f"===== {name} =====\n{path.read_bytes().decode('utf-8')}")
    return "".join(parts)


EDIT_CASES = [
    # (golden name, fixture, item id, field, value, resolution)
    ("priority_existing", "backlog", "TASK-001", "priority", "Urgent", None),
    ("priority_inserted", "backlog", "TASK-003", "priority", "Prospective.", None),
    ("status_active", "backlog", "STORY-001", "status", "In progress", None),
    ("complete_to_archive", "backlog", "TASK-001", "status", "Completed", "Merged in PR 1"),
    ("complete_last_entry", "backlog", "TASK-003", "status", "Rejected", "Obsolete"),
    ("complete_first_entry", "backlog", "EPIC-001", "status", "Completed", "All done."),
    ("complete_into_empty_archive", "empty_archive", "TASK-020", "status", "Completed", "Done"),
    ("reopen_from_archive", "backlog", "TASK-000", "status", "Open", None),
    ("reopen_last_archive_entry", "backlog", "STORY-000", "status", "In progress", None),
    ("terminal_within_archive", "backlog", "STORY-000", "status", "Completed", "Needed after all"),
    ("priority_in_archive", "backlog", "TASK-000", "priority", "Important", None),
    ("complete_without_archive", "no_archive", "TASK-010", "status", "Completed", None),
    ("checkbox_check", "checklist", "TODO:5", "status", "Completed", None),
    ("checkbox_uncheck", "checklist", "TODO:4", "status", "Open", None),
]


@pytest.mark.parametrize(("name", "fixture", "item_id", "field", "value", "resolution"), EDIT_CASES,
                         ids=[c[0] for c in EDIT_CASES])
def test_edit_rewrites_files(api, workspace, golden, name, fixture, item_id, field, value, resolution):
    folder = _setup(api, workspace, fixture)

    resp = _update(api, _item(api, item_id), field, value, resolution)

    assert resp.status_code == 200, resp.body
    golden(f"edit/{name}.md", _files(folder))
    golden(f"edit/{name}.response.json", resp.body)


def test_edit_twice_reopen_after_archive(api, workspace, golden):
    folder = _setup(api, workspace, "backlog")

    _update(api, _item(api, "TASK-002"), "status", "Completed", "Done")
    resp = _update(api, _item(api, "TASK-002"), "status", "Open")

    assert resp.status_code == 200
    golden("edit/roundtrip_archive_and_back.md", _files(folder))


def test_edit_preserves_crlf(api, workspace):
    folder = _setup(api, workspace, "backlog")
    for name in ("TODO.md", "archive.md"):
        path = folder / name
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))

    resp = _update(api, _item(api, "TASK-001"), "status", "Completed", "Done")

    assert resp.status_code == 200
    for name in ("TODO.md", "archive.md"):
        data = (folder / name).read_bytes()
        assert b"\r\n" in data
        assert b"\n" not in data.replace(b"\r\n", b"")


def test_edit_errors(api, workspace):
    folder = _setup(api, workspace, "backlog")
    item = _item(api, "TASK-001")
    before = _files(folder)

    cases = [
        ("resolution_required", 400, dict(field="status", value="Completed")),
        ("resolution_required", 400, dict(field="status", value="Rejected", resolution="  ")),
        ("not_editable", 400, dict(field="title", value="x")),
        ("entry_moved", 400, dict(field="status", value="Open", line=item["line"] + 1)),
        ("entry_moved", 400, dict(field="status", value="Open", line=9999)),
        ("entry_moved", 400, dict(field="status", value="Open", id="TASK-999")),
        ("unknown_format", 400, dict(field="status", value="Open", format="yaml")),
        ("file_not_found", 404, dict(field="status", value="Open", source_file=str(folder / "nope.md"))),
        ("bad_request", 400, dict(field="status", value=None)),
        ("bad_request", 400, dict(field="status", value="Open", line="3")),
    ]
    for code, status, override in cases:
        field = override.pop("field")
        value = override.pop("value")
        resolution = override.pop("resolution", None)
        resp = _update(api, item, field, value, resolution, **override)
        assert (resp.status_code, resp.body.get("code")) == (status, code), (code, override)

    assert _files(folder) == before


def test_checkbox_only_status(api, workspace):
    _setup(api, workspace, "checklist")

    resp = _update(api, _item(api, "TODO:3"), "priority", "Urgent")

    assert (resp.status_code, resp.body["code"]) == (400, "checkbox_status_only")


def test_edit_rejects_non_object(api):
    resp = api.post("/api/items/update", [1, 2])

    assert (resp.status_code, resp.body["code"]) == (400, "bad_request")

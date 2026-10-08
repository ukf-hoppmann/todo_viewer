"""Notes and specs of a note through API v2: read, replace, append a dated entry; version conflicts."""
from __future__ import annotations

import re

from tests.api_v2.conftest import BASE, OTHER_BASE

DOCS = f"{BASE}/notes/NOTE-001/documents"


def _note(api, summary: str = "an idea") -> dict:
    resp = api.post(f"{BASE}/notes", {"summary": summary})
    assert resp.status_code == 201, resp.body
    return resp.body


def test_a_spec_is_created_read_listed_and_replaced_with_the_version(notes_api):
    _note(notes_api)
    assert notes_api.get(DOCS).body == []

    created = notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "# spec\n", "version": None})
    assert created.status_code == 200, created.body
    assert (created.body["name"], created.body["kind"], created.body["content"]) == (
        "NOTE-001_spec.md", "spec", "# spec\n")
    assert [(d["name"], d["kind"]) for d in notes_api.get(DOCS).body] == [("NOTE-001_spec.md", "spec")]
    assert notes_api.get(f"{DOCS}/NOTE-001_spec.md").body == created.body

    replaced = notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "# new\n", "version": created.body["version"]})
    assert (replaced.status_code, replaced.body["content"]) == (200, "# new\n")
    assert replaced.body["version"] != created.body["version"]


def test_a_stale_version_or_a_missing_version_is_a_conflict(notes_api):
    _note(notes_api)
    first = notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "one", "version": None}).body
    notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "two", "version": first["version"]})

    stale = notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "three", "version": first["version"]})
    assert (stale.status_code, stale.body["code"]) == (409, "version_conflict")
    no_version = notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "three", "version": None})
    assert no_version.body["code"] == "version_conflict"
    assert notes_api.get(f"{DOCS}/NOTE-001_spec.md").body["content"] == "two"
    not_there = notes_api.put(f"{DOCS}/NOTE-001_spec_ui.md", {"content": "x", "version": "0000"})
    assert not_there.body["code"] == "version_conflict"


def test_a_spec_with_a_topic_in_its_name_is_allowed(notes_api):
    _note(notes_api)
    created = notes_api.put(f"{DOCS}/NOTE-001_spec_ui-design.md", {"content": "x", "version": None})
    assert (created.status_code, created.body["kind"]) == (200, "spec")


def test_names_that_do_not_belong_to_the_note_are_refused(notes_api):
    _note(notes_api)
    for name in ("NOTE-002_spec.md", "NOTE-001_other.md", "notes.md", "NOTE-001_spec.txt", "NOTE-001_spec_a_b.md"):
        refused = notes_api.put(f"{DOCS}/{name}", {"content": "x", "version": None})
        assert (refused.status_code, refused.body["code"]) == (403, "forbidden"), name
        assert notes_api.get(f"{DOCS}/{name}").body["code"] == "forbidden"
    assert notes_api.get(DOCS).body == []


def test_a_document_that_does_not_exist_is_not_found(notes_api):
    _note(notes_api)
    missing = notes_api.get(f"{DOCS}/NOTE-001_notes.md")
    assert (missing.status_code, missing.body["code"]) == (404, "file_not_found")
    assert notes_api.get(f"{BASE}/notes/NOTE-009/documents").body["code"] == "note_not_found"
    assert notes_api.get(f"{BASE}/notes/NOTE-009/documents/NOTE-009_spec.md").body["code"] == "note_not_found"


def test_a_dated_entry_is_appended_to_the_notes_file(notes_api):
    _note(notes_api, "Think about caching")
    first = notes_api.post(f"{BASE}/notes/NOTE-001/notes", {
        "topic": "First look", "discussed": ["Redis or not"], "decided": ["Not now"], "open": ["Measure"]})
    assert first.status_code == 200, first.body
    assert (first.body["name"], first.body["kind"]) == ("NOTE-001_notes.md", "notes")
    assert first.body["content"].startswith("# NOTE-001 — Think about caching\n")
    assert re.search(r"^## \d{4}-\d{2}-\d{2} — First look$", first.body["content"], re.M)
    for text in ("### Discussed", "- Redis or not", "### Decided", "- Not now", "### Open", "- Measure"):
        assert text in first.body["content"]

    second = notes_api.post(f"{BASE}/notes/NOTE-001/notes", {"topic": "Second look", "decided": ["Use it"]})
    assert second.body["content"].startswith(first.body["content"].rstrip())
    assert len(re.findall(r"^## ", second.body["content"], re.M)) == 2
    assert notes_api.get(f"{DOCS}/NOTE-001_notes.md").body["content"] == second.body["content"]
    assert [d["name"] for d in notes_api.get(DOCS).body] == ["NOTE-001_notes.md"]


def test_an_entry_needs_a_topic_and_some_content(notes_api):
    _note(notes_api)
    url = f"{BASE}/notes/NOTE-001/notes"
    assert notes_api.post(url, {"topic": " ", "decided": ["x"]}).body["code"] == "value_required"
    assert notes_api.post(url, {"topic": "t"}).body["code"] == "value_required"
    assert notes_api.get(DOCS).body == []


def test_the_notes_file_can_be_replaced_as_a_whole(notes_api):
    _note(notes_api)
    entry = notes_api.post(f"{BASE}/notes/NOTE-001/notes", {"topic": "t", "decided": ["x"]}).body
    replaced = notes_api.put(f"{DOCS}/NOTE-001_notes.md", {"content": "# fresh\n", "version": entry["version"]})
    assert (replaced.status_code, replaced.body["content"], replaced.body["kind"]) == (200, "# fresh\n", "notes")


def test_documents_of_closed_notes_can_be_read_but_not_written(notes_api):
    note = _note(notes_api)
    notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "kept", "version": None})
    notes_api.post(f"{BASE}/notes/NOTE-001/finish", {"version": note["version"], "status": "done"})

    assert notes_api.get(f"{DOCS}/NOTE-001_spec.md").body["content"] == "kept"
    written = notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "x", "version": None})
    assert (written.status_code, written.body["code"]) == (409, "note_closed")
    appended = notes_api.post(f"{BASE}/notes/NOTE-001/notes", {"topic": "t", "decided": ["x"]})
    assert appended.body["code"] == "note_closed"


def test_the_documents_come_along_when_the_note_moves_to_another_project(notes_api):
    note = _note(notes_api)
    notes_api.put(f"{DOCS}/NOTE-001_spec.md", {"content": "kept", "version": None})
    notes_api.post(f"{BASE}/notes/NOTE-001/notes", {"topic": "t", "decided": ["x"]})
    notes_api.post(f"{BASE}/notes/NOTE-001/move", {"version": note["version"], "project": "other"})

    moved = notes_api.get(f"{OTHER_BASE}/notes/NOTE-001/documents").body
    assert [d["name"] for d in moved] == ["NOTE-001_notes.md", "NOTE-001_spec.md"]
    assert notes_api.get(f"{OTHER_BASE}/notes/NOTE-001/documents/NOTE-001_spec.md").body["content"] == "kept"

from __future__ import annotations

import pytest

from todo_viewer.domain.documents import (
    DocumentKind,
    DocumentRef,
    NotesEntry,
    content_version,
    item_documents,
    new_notes_file,
    notes_path,
    spec_path,
)
from todo_viewer.domain.errors import InvalidValueError, ValueRequiredError
from todo_viewer.domain.item import Item


def test_documents_of_an_item_are_named_by_file_name():
    item = Item(id="T-1", title="t", project="p", notes=["items/T-1/T-1_notes.md"],
                spec=["items/T-1/T-1_spec.md", "items/T-1/T-1_spec_api.md"])

    assert item_documents(item) == [
        DocumentRef("T-1_notes.md", DocumentKind.NOTES, "items/T-1/T-1_notes.md"),
        DocumentRef("T-1_spec.md", DocumentKind.SPEC, "items/T-1/T-1_spec.md"),
        DocumentRef("T-1_spec_api.md", DocumentKind.SPEC, "items/T-1/T-1_spec_api.md"),
    ]


def test_default_paths_and_spec_names():
    item = Item(id="T-1", title="t", project="p")

    assert notes_path(item) == "items/T-1/T-1_notes.md"
    assert spec_path(item, "T-1_spec.md") == "items/T-1/T-1_spec.md"
    assert spec_path(item, "T-1_spec_data-model.md") == "items/T-1/T-1_spec_data-model.md"
    for bad in ("spec.md", "T-2_spec.md", "T-1_spec.txt", "../T-1_spec.md", "T-1_notes.md"):
        with pytest.raises(InvalidValueError):
            spec_path(item, bad)


def test_notes_entry_renders_the_format():
    entry = NotesEntry.create("2026-09-28", " Design ", discussed=["Option A", "Option\n B"], decided=["A"], open=[])

    assert entry.render() == (
        "## 2026-09-28 — Design\n\n"
        "### Discussed\n\n- Option A\n- Option B\n\n"
        "### Decided\n\n- A\n"
    )
    assert new_notes_file(Item(id="T-1", title="Title", project="p")) == "# T-1 — Title\n"


def test_notes_entry_needs_topic_and_content():
    with pytest.raises(ValueRequiredError):
        NotesEntry.create("2026-09-28", " ", discussed=["x"], decided=[], open=[])
    with pytest.raises(ValueRequiredError):
        NotesEntry.create("2026-09-28", "Topic", discussed=[" "], decided=[], open=[])


def test_content_version():
    assert content_version("a") == content_version("a") != content_version("b")
    assert len(content_version("a")) == 16

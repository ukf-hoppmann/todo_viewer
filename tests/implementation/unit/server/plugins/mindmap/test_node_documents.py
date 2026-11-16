from __future__ import annotations

from datetime import date

import pytest
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.mindmap.domain.documents import (
    NotesEntry,
    append_entry,
    document_kind,
    new_document_kind,
    notes_header,
    notes_name,
)


@pytest.mark.parametrize(
    "name,kind",
    [
        ("NODE-1_notes.md", "notes"),
        ("NODE-1_spec.md", "spec"),
        ("NODE-1_spec_api.md", "spec"),
        ("NODE-2_notes.md", None),
        ("NODE-1_spec_a b.md", None),
    ],
)
def test_the_name_of_a_document_decides_its_kind(name: str, kind: str | None) -> None:
    assert document_kind("NODE-1", name) == kind


def test_the_notes_are_named_after_the_label_of_the_node() -> None:
    assert notes_name("NODE-7") == "NODE-7_notes.md"


def test_a_new_document_needs_a_valid_name() -> None:
    assert new_document_kind("NODE-1", "NODE-1_notes.md") == "notes"
    with pytest.raises(InvalidInput) as error:
        new_document_kind("NODE-1", "other.md")
    assert error.value.details["field"] == "name"


def test_the_first_entry_follows_the_header_with_the_title_and_later_ones_are_appended() -> None:
    first = NotesEntry.create(date(2026, 11, 16), "Idee", ["a  b"], [], ["offen"])
    text = append_entry(notes_header("NODE-1", "Thema"), first)
    assert text == "# NODE-1 — Thema\n\n## 2026-11-16 — Idee\n\n### Discussed\n\n- a b\n\n### Open\n\n- offen\n"
    second = NotesEntry.create(date(2026, 11, 17), "Mehr", [], ["fix"], [])
    assert append_entry(text, second).endswith("\n## 2026-11-17 — Mehr\n\n### Decided\n\n- fix\n")


def test_an_entry_needs_a_topic_and_a_bullet() -> None:
    with pytest.raises(InvalidInput):
        NotesEntry.create(date(2026, 11, 16), " ", ["x"], [], [])
    with pytest.raises(InvalidInput):
        NotesEntry.create(date(2026, 11, 16), "T", [" "], [], [])

from __future__ import annotations

from datetime import date

import pytest
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.memos.domain.documents import (
    NotesEntry,
    append_entry,
    document_kind,
    new_document_kind,
    notes_header,
)


@pytest.mark.parametrize(
    "name,kind",
    [
        ("MEMO-1_notes.md", "notes"),
        ("MEMO-1_spec.md", "spec"),
        ("MEMO-1_spec_api.md", "spec"),
        ("MEMO-2_notes.md", None),
    ],
)
def test_the_name_decides_the_kind(name: str, kind: str | None) -> None:
    assert document_kind("MEMO-1", name) == kind


def test_a_new_document_needs_a_valid_name() -> None:
    assert new_document_kind("MEMO-1", "MEMO-1_notes.md") == "notes"
    with pytest.raises(InvalidInput):
        new_document_kind("MEMO-1", "other.md")


def test_the_first_entry_follows_the_header_and_later_ones_are_appended() -> None:
    first = NotesEntry.create(date(2026, 10, 17), "Idee", ["a  b"], [], ["offen"])
    text = append_entry(notes_header("MEMO-1", "Titel"), first)
    assert text == "# MEMO-1 — Titel\n\n## 2026-10-17 — Idee\n\n### Discussed\n\n- a b\n\n### Open\n\n- offen\n"
    second = NotesEntry.create(date(2026, 10, 18), "Mehr", [], ["fix"], [])
    assert append_entry(text, second).endswith("\n## 2026-10-18 — Mehr\n\n### Decided\n\n- fix\n")


def test_an_entry_needs_a_topic_and_a_bullet() -> None:
    with pytest.raises(InvalidInput):
        NotesEntry.create(date(2026, 10, 17), " ", ["x"], [], [])
    with pytest.raises(InvalidInput):
        NotesEntry.create(date(2026, 10, 17), "T", [" "], [], [])

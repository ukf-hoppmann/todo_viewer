from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from backlog_fixtures import item
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.backlog.domain.documents import (
    NotesEntry,
    append_entry,
    new_document_kind,
    notes_header,
    notes_name,
    renamed_documents,
)
from viewer.plugins.backlog.domain.editing import ValueRequired
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules, LifecycleViolation

DAY = date(2026, 10, 16)


def test_the_first_notes_and_specs_have_names_that_follow_the_label() -> None:
    story = replace(item("s", label="STORY-008"))

    assert notes_name("STORY-008") == "STORY-008_notes.md"
    assert new_document_kind(story, "STORY-008_notes.md") == "notes"
    assert new_document_kind(story, "STORY-008_spec.md") == "spec"
    assert new_document_kind(story, "STORY-008_spec_Server-Teil.md") == "spec"


@pytest.mark.parametrize(
    "name", ["STORY-009_spec.md", "STORY-008_spec_ü.md", "STORY-008_other.md", "notes.md", "STORY-008_spec_a_b.md"]
)
def test_other_names_are_refused(name: str) -> None:
    with pytest.raises(InvalidInput):
        new_document_kind(item("s", label="STORY-008"), name)


def test_a_second_notes_document_is_refused() -> None:
    story = replace(item("s", label="STORY-008"), notes=("STORY-008_notes.md",))

    with pytest.raises(InvalidInput):
        new_document_kind(story, "STORY-008_notes.md")


def test_an_entry_has_the_date_the_topic_and_only_the_filled_sections() -> None:
    entry = NotesEntry.create(DAY, "  Sync \n entscheiden ", ["Eins  ", " "], [], ["Offen\nzwei"])

    assert entry.render() == "## 2026-10-16 — Sync entscheiden\n\n### Discussed\n\n- Eins\n\n### Open\n\n- Offen zwei\n"


def test_an_entry_needs_a_topic_and_a_bullet() -> None:
    with pytest.raises(ValueRequired):
        NotesEntry.create(DAY, "  ", ["x"], [], [])
    with pytest.raises(ValueRequired):
        NotesEntry.create(DAY, "Thema", [" "], [""], [])


def test_entries_are_appended_with_a_blank_line_between() -> None:
    first = NotesEntry.create(DAY, "Eins", ["a"], [], [])
    second = NotesEntry.create(DAY, "Zwei", [], ["b"], [])
    story = replace(item("s", label="STORY-008", title="Titel"))

    text = append_entry(append_entry(notes_header(story), first), second)

    assert text == (
        "# STORY-008 — Titel\n\n## 2026-10-16 — Eins\n\n### Discussed\n\n- a\n\n"
        "## 2026-10-16 — Zwei\n\n### Decided\n\n- b\n"
    )
    assert append_entry("", first) == first.render()
    assert append_entry("ohne Zeilenende", first).startswith("ohne Zeilenende\n\n## ")


def test_documents_are_renamed_with_the_label_and_others_stay() -> None:
    names = ["STORY-008_notes.md", "STORY-008_spec_a.md", "STORY-0081_spec.md", "anderes.md"]

    assert renamed_documents(names, "STORY-008", "TASK-004") == {
        "STORY-008_notes.md": "TASK-004_notes.md",
        "STORY-008_spec_a.md": "TASK-004_spec_a.md",
    }


def test_notes_need_a_summary() -> None:
    rules = LifecycleRules()
    with_notes = replace(item("a"), notes=("A_notes.md",), summary=None)
    rules_before = [item("a")]

    with pytest.raises(LifecycleViolation) as error:
        rules.check_change(rules_before, [with_notes])
    rules.check_change(rules_before, [replace(with_notes, summary="Kurz")])

    assert error.value.code == "summary_required_with_notes"
    rules.check_change([with_notes], [replace(with_notes, title="Neu")])  # ein vorhandener Mangel blockiert nichts

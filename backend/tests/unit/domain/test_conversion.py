"""Rules for turning a note into an item and an item back into a note."""
from __future__ import annotations

import pytest

from todo_viewer.domain.conversion import (
    DEMOTE_RESOLUTION,
    check_demote,
    promotion_entry,
    promotion_fields,
    promotion_marker,
    renamed_document,
    without_header,
)
from todo_viewer.domain.errors import ConversionRefusedError
from todo_viewer.domain.item import Item, Status


def item(item_id: str, status: str = Status.OPEN, **fields) -> Item:
    return Item(id=item_id, title=item_id, project="proj", status=status, **fields)


def test_an_open_item_nobody_refers_to_may_be_demoted():
    check_demote(item("TASK-001"), [item("TASK-001"), item("TASK-002")])


@pytest.mark.parametrize("status", [Status.IN_PROGRESS, Status.AWAITING_CONFIRMATION, Status.COMPLETED,
                                    Status.REJECTED])
def test_an_item_that_is_not_open_is_refused(status):
    with pytest.raises(ConversionRefusedError) as refused:
        check_demote(item("TASK-001", status), [item("TASK-001", status)])
    assert refused.value.code == "demote_not_open"


def test_an_item_with_children_is_refused_also_when_they_are_closed():
    story = item("STORY-001")
    closed = item("TASK-001", Status.COMPLETED, parent="STORY-001")
    with pytest.raises(ConversionRefusedError) as refused:
        check_demote(story, [story, closed])
    assert (refused.value.code, refused.value.details["items"]) == ("demote_has_children", "TASK-001")


def test_an_item_that_is_a_dependency_of_another_is_refused():
    task = item("TASK-001")
    with pytest.raises(ConversionRefusedError) as refused:
        check_demote(task, [task, item("TASK-002", dependencies=["TASK-001"])])
    assert (refused.value.code, refused.value.details["items"]) == ("demote_referenced", "TASK-002")


def test_items_in_the_trash_do_not_hold_an_item_back():
    task = item("TASK-001")
    gone = item("TASK-002", dependencies=["TASK-001"], deleted="2027-12-11")
    gone_child = item("TASK-003", parent="TASK-001", deleted="2027-12-11")
    check_demote(task, [task, gone, gone_child])


def test_the_item_blocked_by_several_rules_reports_the_status_first():
    story = item("STORY-001", Status.IN_PROGRESS)
    with pytest.raises(ConversionRefusedError) as refused:
        check_demote(story, [story, item("TASK-001", parent="STORY-001")])
    assert refused.value.code == "demote_not_open"


def test_the_resolution_of_a_demoted_item_names_the_reason():
    assert DEMOTE_RESOLUTION == "zur Notiz zurückgestuft"


def test_the_long_text_of_a_note_becomes_one_dated_notes_entry_line_by_line():
    entry = promotion_entry("2027-12-11", "NOTE-007", "First thought.\n\n  Second   thought.\n")
    assert entry.render() == ("## 2027-12-11 — Aus Note NOTE-007 befördert\n\n"
                              "### Discussed\n\n- First thought.\n- Second thought.\n")
    assert promotion_marker("NOTE-007") in entry.render()


def test_a_note_without_text_still_leaves_a_trace_of_its_origin():
    entry = promotion_entry("2027-12-11", "NOTE-007", None)
    assert promotion_marker("NOTE-007") in entry.render()


@pytest.mark.parametrize("name, old, new, expected", [
    ("NOTE-001_notes.md", "NOTE-001", "TASK-004", "TASK-004_notes.md"),
    ("NOTE-001_spec.md", "NOTE-001", "TASK-004", "TASK-004_spec.md"),
    ("NOTE-001_spec_api.md", "NOTE-001", "TASK-004", "TASK-004_spec_api.md"),
    ("STORY-001_spec_ui.md", "STORY-001", "NOTE-002", "NOTE-002_spec_ui.md"),
    ("docs/STORY-001_notes.md", "STORY-001", "NOTE-002", "NOTE-002_notes.md"),
])
def test_documents_are_renamed_to_the_label_of_the_other_side(name, old, new, expected):
    assert renamed_document(name, old, new) == expected


def test_the_new_item_takes_title_and_summary_from_the_note_unless_the_caller_gives_them():
    given = {"area": "Core", "title": "Better title", "summary": None, "priority": None}
    assert promotion_fields("An idea", given) == {"title": "Better title", "summary": "An idea", "area": "Core"}


def test_a_notes_file_joins_another_without_its_heading():
    assert without_header("# NOTE-001 — idea\n\n## 2027-12-11 — Topic\n\n- a\n") == "## 2027-12-11 — Topic\n\n- a"
    assert without_header("## 2027-12-11 — Topic\n") == "## 2027-12-11 — Topic"


def test_a_document_of_another_label_is_not_renamed():
    assert renamed_document("NOTE-0011_notes.md", "NOTE-001", "TASK-004") is None

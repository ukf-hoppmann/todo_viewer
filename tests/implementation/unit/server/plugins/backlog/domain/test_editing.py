from __future__ import annotations

from datetime import date

import pytest
from backlog_fixtures import item
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.backlog.domain.editing import (
    NotEditable,
    ResolutionRequired,
    ValueRequired,
    apply_update,
    build_new_item,
    normalize,
    rewrite_labels,
    rewrite_references,
)

TODAY = date(2026, 10, 16)
NEW = {"title": "  Neues\n Item ", "area": "Server", "goal": "Ziel", "completion_criteria": "Kriterien"}


def create(**extra: object):  # type: ignore[no-untyped-def]
    fields = {**NEW, **extra}
    return build_new_item("u", "TASK-001", "p", "Task", fields, TODAY, 0, 1)


def test_new_items_are_open_with_defaults_and_one_line_texts() -> None:
    created = create()

    assert (created.title, created.status, created.priority, created.created, created.parent_uid) == (
        "Neues Item",
        "Open",
        "Normal",
        TODAY,
        None,
    )
    assert created.required_for_parent is None and created.dependencies == ()


def test_title_goal_and_criteria_are_required() -> None:
    for field in ("title", "goal", "completion_criteria"):
        with pytest.raises(ValueRequired):
            build_new_item("u", "TASK-001", "p", "Task", {**NEW, field: "  "}, TODAY, 0, 1)
        fields = {k: v for k, v in NEW.items() if k != field}
        with pytest.raises(ValueRequired):
            build_new_item("u", "TASK-001", "p", "Task", fields, TODAY, 0, 1)


def test_area_is_optional_when_creating() -> None:
    without = {k: v for k, v in NEW.items() if k != "area"}
    assert build_new_item("u", "TASK-001", "p", "Task", without, TODAY, 0, 1).area is None
    assert build_new_item("u", "TASK-001", "p", "Task", {**without, "area": "  "}, TODAY, 0, 1).area is None
    assert build_new_item("u", "TASK-001", "p", "Task", NEW, TODAY, 0, 1).area == "Server"


def test_new_items_refuse_unknown_type_status_and_fields() -> None:
    with pytest.raises(InvalidInput):
        build_new_item("u", "X-1", "p", "Bug", NEW, TODAY, 0, 1)
    with pytest.raises(NotEditable):
        create(status="Completed")
    with pytest.raises(InvalidInput):
        create(created="gestern")
    assert create(created="2026-01-02").created == date(2026, 1, 2)


def test_a_new_item_can_have_a_parent_dependencies_and_a_summary() -> None:
    created = create(
        parent="p1", required_for_parent=True, dependencies=["a", "b", "a"], summary="Kurz", priority="Urgent"
    )

    assert (
        created.parent_uid,
        created.required_for_parent,
        created.dependencies,
        created.summary,
        created.priority,
    ) == (
        "p1",
        True,
        ("a", "b"),
        "Kurz",
        "Urgent",
    )


@pytest.mark.parametrize(
    ("field", "raw"),
    [
        ("priority", "Egal"),
        ("status", "Erfunden"),
        ("title", "mit ** Fett"),
        ("required_for_parent", "Yes"),
        ("dependencies", "a,b"),
    ],
)
def test_invalid_values_are_refused(field: str, raw: object) -> None:
    with pytest.raises(InvalidInput):
        normalize(field, raw)


def test_update_changes_only_the_given_fields() -> None:
    base = item("a")

    updated = apply_update(base, {"title": " Neu  ", "priority": "Urgent", "summary": "Kurz"}, None)

    assert (updated.title, updated.priority, updated.summary, updated.status) == ("Neu", "Urgent", "Kurz", "Open")
    assert apply_update(updated, {"summary": ""}, None).summary is None


def test_update_refuses_unknown_fields_and_an_empty_change() -> None:
    with pytest.raises(NotEditable):
        apply_update(item("a"), {"label": "X-1"}, None)
    with pytest.raises(NotEditable):
        apply_update(item("a"), {}, None)
    with pytest.raises(ValueRequired):
        apply_update(item("a"), {"goal": " "}, None)


def test_closing_needs_a_resolution_and_reopening_drops_it() -> None:
    base = item("a")
    with pytest.raises(ResolutionRequired):
        apply_update(base, {"status": "Completed"}, "  ")

    closed = apply_update(base, {"status": "Completed"}, "Bestätigt am 2026-10-16.")
    assert (closed.status, closed.resolution) == ("Completed", "Bestätigt am 2026-10-16.")
    reopened = apply_update(closed, {"status": "In progress"}, "ignoriert")
    assert (reopened.status, reopened.resolution) == ("In progress", None)


def test_removing_the_parent_removes_the_required_flag() -> None:
    child = apply_update(item("c"), {"parent": "p", "required_for_parent": True}, None)
    assert (child.parent_uid, child.required_for_parent) == ("p", True)

    orphan = apply_update(child, {"parent": None}, None)

    assert (orphan.parent_uid, orphan.required_for_parent) == (None, None)


def test_rewrite_labels_replaces_whole_ids_only() -> None:
    text = "Siehe STORY-008, nicht STORY-0081 oder STORY-008-b; Datei STORY-008_notes.md und STORY-008."

    assert rewrite_labels(text, "STORY-008", "TASK-004") == (
        "Siehe TASK-004, nicht STORY-0081 oder STORY-008-b; Datei TASK-004_notes.md und TASK-004."
    )


def test_rewrite_references_finds_the_text_fields_that_mention_the_old_label() -> None:
    from dataclasses import replace

    items = [
        replace(item("a"), title="Folge von STORY-008", summary=None, goal="Ziel"),
        replace(item("b"), goal="Wie STORY-008", resolution="STORY-008 erledigt"),
        item("c"),
    ]

    assert rewrite_references(items, "STORY-008", "TASK-004") == {
        "a": {"title": "Folge von TASK-004"},
        "b": {"goal": "Wie TASK-004", "resolution": "TASK-004 erledigt"},
    }


@pytest.mark.parametrize("field", ["goal", "completion_criteria", "summary"])
def test_long_texts_keep_their_line_breaks(field: str) -> None:
    assert (
        normalize(field, "\n 1.  Erstens\r\n2. Zweites \n\n\n\n3. Drittes\n") == "1. Erstens\n2. Zweites\n\n3. Drittes"
    )


def test_title_stays_one_line() -> None:
    assert normalize("title", "Ein\nTitel") == "Ein Titel"

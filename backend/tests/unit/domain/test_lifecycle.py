from __future__ import annotations

import dataclasses

import pytest

from todo_viewer.domain.errors import LifecycleViolationError
from todo_viewer.domain.item import Item
from todo_viewer.domain.lifecycle import LifecycleRules, Violation

rules = LifecycleRules()


def item(item_id: str, item_type: str = "Task", status: str = "Open", parent: str | None = None,
         required: bool | None = None, dependencies: tuple[str, ...] = ()) -> Item:
    if parent is not None and required is None:
        required = True
    return Item(id=item_id, title=item_id, project="p", item_type=item_type, status=status, parent=parent,
                required_for_parent=required, dependencies=list(dependencies))


def with_status(items: list[Item], item_id: str, status: str) -> list[Item]:
    return [dataclasses.replace(i, status=status) if i.id == item_id else i for i in items]


# ---------- single rules ----------

def test_consistent_backlog_has_no_violations():
    items = [item("E", "Epic", "In progress"), item("S", "Story", "Completed", parent="E"),
             item("T", status="Rejected", parent="S", required=False), item("U", dependencies=("T",))]

    assert rules.violations(items) == set()


@pytest.mark.parametrize("status", ["In progress", "Awaiting confirmation", "Completed"])
def test_epic_needs_required_child_to_leave_open(status):
    items = [item("E", "Epic", status), item("S", "Story", "Completed", parent="E", required=False)]

    assert rules.violations(items) == {Violation("epic_without_required_child", "E")}


def test_empty_epic_may_stay_open_or_be_rejected():
    assert rules.violations([item("E", "Epic"), item("F", "Epic", "Rejected")]) == set()


def test_awaiting_parent_needs_required_children_awaiting_or_completed():
    items = [item("S", "Story", "Awaiting confirmation"), item("A", status="Awaiting confirmation", parent="S"),
             item("B", status="In progress", parent="S"), item("C", status="Open", parent="S", required=False)]

    assert rules.violations(items) == {Violation("required_children_not_done", "S", ("B",))}


def test_completed_parent_needs_completed_required_children():
    items = [item("S", "Story", "Completed"), item("A", status="Rejected", parent="S"),
             item("B", status="Awaiting confirmation", parent="S")]

    assert Violation("required_children_not_done", "S", ("A", "B")) in rules.violations(items)


@pytest.mark.parametrize("status", ["Completed", "Rejected"])
def test_closed_parent_has_no_active_children(status):
    items = [item("S", "Story", status), item("A", status="Completed", parent="S"),
             item("B", status="Open", parent="S", required=False)]

    assert Violation("children_still_active", "S", ("B",)) in rules.violations(items)


def test_structure_rules():
    items = [item("E", "Epic"), item("F", "Epic", parent="E"), item("T", parent="E", required=None),
             item("T2", "Task")]
    items[2] = dataclasses.replace(items[2], required_for_parent=None)

    assert rules.violations(items) == {
        Violation("epic_with_parent", "F"),
        Violation("required_for_parent_missing", "T"),
    }


def test_cycles():
    items = [item("A", parent="B"), item("B", parent="A"),
             item("X", dependencies=("Y",)), item("Y", dependencies=("Z",)), item("Z", dependencies=("X",))]

    assert rules.violations(items) >= {
        Violation("parent_cycle", "A", ("A", "B")),
        Violation("dependency_cycle", "X", ("X", "Y", "Z")),
    }


# ---------- checking a change ----------

def test_change_introducing_a_violation_is_rejected():
    before = [item("S", "Story", "In progress"), item("A", status="In progress", parent="S")]

    with pytest.raises(LifecycleViolationError) as err:
        rules.check_change(before, with_status(before, "S", "Awaiting confirmation"))

    assert err.value.code == "required_children_not_done"
    assert err.value.details == {"id": "S", "items": "A"}


def test_reopening_a_child_of_a_completed_parent_is_rejected():
    before = [item("S", "Story", "Completed"), item("A", status="Completed", parent="S")]

    with pytest.raises(LifecycleViolationError) as err:
        rules.check_change(before, with_status(before, "A", "In progress"))

    assert err.value.code in {"children_still_active", "required_children_not_done"}
    assert err.value.details["id"] == "S"


def test_existing_violations_do_not_block_unrelated_or_improving_changes():
    before = [item("S", "Story", "Completed"), item("A", status="Open", parent="S"),
              item("B", status="Open", parent="S"), item("X")]

    rules.check_change(before, with_status(before, "X", "In progress"))
    rules.check_change(before, with_status(before, "A", "Completed"))


def test_extending_an_existing_violation_is_rejected():
    before = [item("S", "Story", "Completed"), item("A", status="Open", parent="S"),
              item("B", status="Completed", parent="S")]

    with pytest.raises(LifecycleViolationError) as err:
        rules.check_change(before, with_status(before, "B", "Open"))

    assert "B" in err.value.details["items"]


def test_references_must_exist():
    items = [item("S", "Story"), item("T", parent="S", dependencies=("S", "GONE")), item("U", parent="NOPE")]

    assert rules.violations(items) == {
        Violation("unknown_reference", "T", ("GONE",)),
        Violation("unknown_reference", "U", ("NOPE",)),
    }


def test_summary_is_required_with_notes():
    with_notes = dataclasses.replace(item("T"), notes=["items/T/T_notes.md"])

    assert rules.violations([with_notes]) == {Violation("summary_required_with_notes", "T")}
    assert rules.violations([dataclasses.replace(with_notes, summary="Short.")]) == set()

from __future__ import annotations

from dataclasses import replace

import pytest
from backlog_fixtures import item
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules, LifecycleViolation, closed_ancestors
from viewer.plugins.backlog.domain.model import Item

rules = LifecycleRules()


def epic(uid: str = "e", status: str = "Open") -> Item:
    return replace(item(uid, status=status), type="Epic")


def child(uid: str, parent: str, status: str = "Open", required: bool | None = True) -> Item:
    return replace(item(uid, parent=parent, status=status, required=required))


def check(before: list[Item], after: list[Item], returning: list[Item] | None = None) -> str:
    try:
        rules.check_change(before, after, returning or [])
    except LifecycleViolation as error:
        return error.code
    return "ok"


def test_an_epic_needs_a_required_child_before_it_leaves_open() -> None:
    before = [epic(), child("s", "e", required=False)]

    assert check(before, [epic(status="In progress"), child("s", "e", required=False)]) == "epic_without_required_child"
    assert check(before, [epic(status="In progress"), child("s", "e", required=True)]) == "ok"
    assert check(before, [epic(status="Rejected"), child("s", "e", status="Rejected", required=False)]) == "ok"


@pytest.mark.parametrize(
    ("parent_status", "child_status", "expected"),
    [
        ("Awaiting confirmation", "In progress", "required_children_not_done"),
        ("Awaiting confirmation", "Awaiting confirmation", "ok"),
        ("Awaiting confirmation", "Completed", "ok"),
        ("Completed", "Awaiting confirmation", "children_still_active"),
        ("Completed", "Completed", "ok"),
        ("In progress", "Open", "ok"),
    ],
)
def test_required_children_must_be_far_enough(parent_status: str, child_status: str, expected: str) -> None:
    before = [epic(status="In progress"), child("s", "e", status=child_status)]

    after = [epic(status=parent_status), child("s", "e", status=child_status)]

    assert check(before, after) == expected


def test_a_closed_item_cannot_keep_active_children() -> None:
    before = [epic(status="In progress"), child("s", "e", status="Completed")]
    after = [epic(status="Completed"), child("s", "e", status="Completed")]
    assert check(before, after) == "ok"

    before = [epic(status="In progress"), child("s", "e", status="In progress")]
    assert check(before, [epic(status="Rejected"), child("s", "e", status="In progress")]) == "children_still_active"


def test_an_active_child_below_a_closed_parent_names_the_ancestors_to_reopen() -> None:
    top = replace(epic("e", "Completed"))
    mid = child("s", "e", status="Completed")
    before = [top, mid]
    after = [top, mid, child("t", "s", status="Open")]

    with pytest.raises(LifecycleViolation) as error:
        rules.check_change(before, after)

    assert error.value.code == "parent_closed"
    assert error.value.details["ancestors"] == [{"uid": "e", "label": "E"}, {"uid": "s", "label": "S"}]


def test_closed_ancestors_stop_at_the_first_open_parent() -> None:
    items = [
        epic("e", "In progress"),
        child("s", "e", "Completed"),
        child("t", "s", "Completed"),
        child("u", "t", "Open"),
    ]

    assert closed_ancestors(items, "u") == ("s", "t")
    assert closed_ancestors(items, "s") == ()


def test_structure_rules() -> None:
    assert check([], [replace(epic(), parent_uid="x"), item("x")]) == "epic_with_parent"
    assert (
        check([item("p"), item("c")], [item("p"), replace(item("c"), parent_uid="p", required_for_parent=None)])
        == "required_for_parent_missing"
    )
    assert check([item("a")], [replace(item("a"), dependencies=("ghost",))]) == "unknown_reference"
    assert check([item("a")], [replace(item("a"), parent_uid="ghost", required_for_parent=True)]) == "unknown_reference"


def test_cycles_are_refused() -> None:
    a, b = item("a"), item("b")

    assert (
        check(
            [a, b],
            [
                replace(a, parent_uid="b", required_for_parent=True),
                replace(b, parent_uid="a", required_for_parent=True),
            ],
        )
        == "parent_cycle"
    )
    assert check([a, b], [replace(a, dependencies=("b",)), replace(b, dependencies=("a",))]) == "dependency_cycle"
    assert check([a, b], [replace(a, dependencies=("b",)), b]) == "ok"


def test_a_violation_that_was_already_there_does_not_block_other_changes() -> None:
    broken = replace(epic(status="In progress"))  # Epic ohne Pflichtkind: schon kaputt
    other = item("x")

    assert check([broken, other], [broken, replace(other, title="Neu")]) == "ok"


def test_an_old_flaw_of_a_returning_item_is_not_new_but_a_rule_between_items_is() -> None:
    flawed = replace(item("c"), parent_uid="p", required_for_parent=None)
    parent = item("p")

    assert check([parent], [parent, flawed], returning=[flawed]) == "ok"
    closed_parent = replace(item("p"), status="Completed")
    assert (
        check([closed_parent], [closed_parent, replace(flawed, required_for_parent=True)], returning=[flawed])
        == "parent_closed"
    )


def test_introduced_collects_all_new_violations_and_check_change_raises_the_first() -> None:
    """`introduced` (`TASK-074`) ist die sammelnde Fassung derselben Regeln, die `check_change` anwendet."""
    old = [item("ok")]
    bad = [
        replace(epic("e1"), parent_uid="x"),
        replace(epic("e2"), parent_uid="x"),
        item("t", parent="e1", required=None),
    ]
    found = rules.introduced(old, [*old, *bad])
    codes = sorted((v.error.code, v.uid) for v in found)

    assert ("epic_with_parent", "e1") in codes and ("epic_with_parent", "e2") in codes
    assert ("required_for_parent_missing", "t") in codes
    assert len(found) > 1
    with pytest.raises(LifecycleViolation) as first:
        rules.check_change(old, [*old, *bad])
    assert first.value.code == found[0].error.code


def test_introduced_ignores_violations_that_were_already_there() -> None:
    flawed = [replace(epic("e"), parent_uid="x")]
    assert rules.introduced(flawed, flawed) == []


def test_introduced_names_the_uids_involved() -> None:
    a = replace(item("a"), dependencies=("b",))
    b = replace(item("b"), dependencies=("a",))
    [found] = rules.introduced([], [a, b])

    assert found.error.code == "dependency_cycle"
    assert {found.uid, *found.related} == {"a", "b"}

from __future__ import annotations

import dataclasses

import pytest

from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import LifecycleViolationError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.trash import TrashPlanner

trash = TrashPlanner(LifecycleRules())
TODAY = "2026-09-28"


def item(item_id: str, item_type: str = "Task", status: str = "Open", parent: str | None = None,
         dependencies: tuple[str, ...] = (), deleted: str | None = None,
         location: Location = Location.ACTIVE) -> Item:
    return Item(id=item_id, title=item_id, project="p", item_type=item_type, status=status, parent=parent,
                required_for_parent=True if parent else None, dependencies=list(dependencies), deleted=deleted,
                location=location)


def backlog() -> list[Item]:
    return [item("E", "Epic"), item("S", "Story", parent="E"), item("T", parent="S"),
            item("U", status="Completed", parent="S", location=Location.ARCHIVE), item("X")]


def ids(plan) -> list[str]:
    return [i.id if isinstance(i, Item) else i[0].id for i in plan]


def apply(items: list[Item], plan) -> list[Item]:
    changed = {i.id: c.applied_to(i) for i, c in plan}
    return [changed.get(i.id, i) for i in items]


def test_delete_single_item_marks_and_archives():
    plan = trash.delete(backlog(), "X", cascade=False, today=TODAY)

    assert plan == [(backlog()[4], ChangeSet(set_fields=(("deleted", TODAY),), move_to=Location.ARCHIVE))]


def test_children_warn_and_cascade_on_confirmation():
    with pytest.raises(LifecycleViolationError) as warning:
        trash.delete(backlog(), "S", cascade=False, today=TODAY)
    plan = trash.delete(backlog(), "E", cascade=True, today=TODAY)

    assert (warning.value.code, warning.value.details) == ("has_children", {"id": "S", "items": "T, U"})
    assert ids(plan) == ["E", "S", "T", "U"]
    assert plan[3][1] == ChangeSet(set_fields=(("deleted", TODAY),))  # already archived


def test_dependencies_from_outside_block_deletion():
    items = [*backlog(), item("D", dependencies=("T",))]

    with pytest.raises(LifecycleViolationError) as err:
        trash.delete(items, "S", cascade=True, today=TODAY)

    assert (err.value.code, err.value.details) == ("item_referenced", {"id": "S", "items": "D"})


def test_lifecycle_rules_apply_to_the_remaining_items():
    items = [item("E", "Epic", "In progress"), item("S", "Story", parent="E")]

    with pytest.raises(LifecycleViolationError) as err:
        trash.delete(items, "S", cascade=False, today=TODAY)

    assert err.value.code == "epic_without_required_child"


def test_deleted_items_do_not_count_for_rules_or_references():
    items = apply(backlog(), trash.delete(backlog(), "X", cascade=False, today=TODAY))
    items.append(item("Y", dependencies=("X",)))

    with pytest.raises(LifecycleViolationError):
        trash.delete(items, "X", cascade=False, today=TODAY)  # already in the trash
    trash.delete(items, "T", cascade=False, today=TODAY)  # X in the trash does not matter


def test_restore_cascades_and_moves_open_items_back():
    items = apply(backlog(), trash.delete(backlog(), "S", cascade=True, today=TODAY))

    with pytest.raises(LifecycleViolationError) as child_first:
        trash.restore(items, "T")
    plan = trash.restore(items, "S")

    assert (child_first.value.code, child_first.value.details["id"]) == ("parent_deleted", "T")
    assert ids(plan) == ["S", "T", "U"]
    restored = apply(items, plan)
    assert [(i.id, i.deleted, i.location) for i in restored if i.id in {"S", "T", "U"}] == [
        ("S", None, Location.ACTIVE), ("T", None, Location.ACTIVE), ("U", None, Location.ARCHIVE)]


def test_restore_and_purge_only_items_in_the_trash():
    for action in (trash.restore, trash.purge):
        with pytest.raises(LifecycleViolationError) as err:
            action(backlog(), "X")
        assert err.value.code == "item_not_deleted"


def test_purge_cascades_and_respects_references():
    items = apply(backlog(), trash.delete(backlog(), "S", cascade=True, today=TODAY))

    assert ids(trash.purge(items, "S")) == ["S", "T", "U"]
    with pytest.raises(LifecycleViolationError) as err:
        trash.purge([*items, dataclasses.replace(item("D", dependencies=("U",)))], "S")
    assert err.value.code == "item_referenced"


def test_restore_tolerates_old_flaws_of_the_item_itself():
    legacy = dataclasses.replace(item("T", parent="S", deleted=TODAY, location=Location.ARCHIVE),
                                 required_for_parent=None)

    assert ids(trash.restore([item("S", "Story"), legacy], "T")) == ["T"]


def test_restore_is_refused_if_the_parent_was_closed_meanwhile():
    items = [item("S", "Story", "Completed", location=Location.ARCHIVE),
             item("T", parent="S", deleted=TODAY, location=Location.ARCHIVE)]

    with pytest.raises(LifecycleViolationError) as err:
        trash.restore(items, "T")

    assert err.value.details["id"] == "S"

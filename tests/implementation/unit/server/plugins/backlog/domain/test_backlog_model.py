from __future__ import annotations

from datetime import date

import pytest
from viewer.plugins.backlog.domain.model import (
    FINAL_STATUSES,
    PRIORITIES,
    STATUSES,
    TYPES,
    Item,
    ItemFilter,
    Progress,
    item_progress,
    project_progress,
)


def item(
    uid: str,
    parent: str | None = None,
    status: str = "Open",
    required: bool | None = None,
    title: str = "",
    priority: str = "Normal",
    label: str | None = None,
) -> Item:
    return Item(
        uid=uid,
        project_uid="p",
        label=label or uid.upper(),
        type="Task",
        title=title or uid,
        status=status,
        priority=priority,
        area=None,
        parent_uid=parent,
        required_for_parent=required,
        goal=None,
        completion_criteria=None,
        summary=None,
        resolution=None,
        created=date(2026, 10, 16),
        position=0,
        revision=1,
    )


def test_the_fixed_value_lists() -> None:
    assert TYPES == ("Epic", "Story", "Task")
    assert STATUSES == ("Open", "In progress", "Awaiting confirmation", "Completed", "Rejected")
    assert set(FINAL_STATUSES) == {"Completed", "Rejected"}
    assert list(PRIORITIES) == ["Urgent", "Important", "Normal", "Prospective"]


def test_progress_counts_done_over_all_descendants() -> None:
    items = [
        item("epic"),
        item("s1", "epic", "Completed"),
        item("s2", "epic"),
        item("t1", "s2", "Completed"),
        item("t2", "s2", "In progress"),
    ]

    progress = item_progress(items)

    assert progress["epic"] == Progress(2, 4)
    assert progress["s2"] == Progress(1, 2)
    assert "s1" not in progress and "t1" not in progress


def test_optional_and_rejected_children_do_not_count_with_their_subtrees() -> None:
    items = [
        item("epic"),
        item("optional", "epic", required=False),
        item("under-optional", "optional", "Completed"),
        item("rejected", "epic", "Rejected"),
        item("under-rejected", "rejected", "Completed"),
        item("real", "epic", "Completed"),
    ]

    assert item_progress(items)["epic"] == Progress(1, 1)
    assert item_progress(items)["optional"] == Progress(1, 1)  # sein eigener Unterbaum zählt für ihn selbst


def test_progress_survives_a_parent_cycle() -> None:
    items = [item("a", "b"), item("b", "a", "Completed")]

    assert item_progress(items)["a"].total >= 1


def test_project_progress_skips_optional_and_rejected_items() -> None:
    items = [
        item("a", status="Completed"),
        item("b"),
        item("c", required=False, status="Completed"),
        item("d", status="Rejected"),
    ]

    assert project_progress(items) == Progress(1, 2)
    assert project_progress([]) == Progress(0, 0)


@pytest.mark.parametrize(
    ("item_filter", "expected"),
    [
        (ItemFilter(), ["a", "b", "c"]),
        (ItemFilter(statuses=frozenset({"Open"})), ["a", "c"]),
        (ItemFilter(priorities=frozenset({"Urgent"})), ["b"]),
        (ItemFilter(query="  SYNC "), ["a"]),
        (ItemFilter(query="dritt"), ["c"]),
        (ItemFilter(statuses=frozenset({"Open"}), query="zzz"), []),
    ],
)
def test_filter(item_filter: ItemFilter, expected: list[str]) -> None:
    items = [
        item("a", title="Sync reparieren"),
        item("b", status="Completed", priority="Urgent", title="Zweites"),
        item("c", title="Drittes"),
    ]

    assert [i.uid for i in items if item_filter.matches(i)] == expected

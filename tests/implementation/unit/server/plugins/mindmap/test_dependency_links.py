from __future__ import annotations

from viewer.plugins.mindmap.domain import assignment as rules
from viewer.plugins.mindmap.domain.assignment import ItemFact, LinkFact


def item(uid: str, needs: tuple[str, ...] = (), status: str = "Open", deleted: bool = False) -> ItemFact:
    return ItemFact(uid, None, status, deleted, needs)


def test_an_item_that_needs_another_in_a_different_node_gives_a_line_from_the_needed_to_the_dependent_node() -> None:
    items = [item("a1"), item("b1", needs=("a1",))]

    links = rules.dependency_links(items, {"a1": "a", "b1": "b"})

    assert links == [LinkFact("a", "b", 1)]


def test_several_dependencies_between_the_same_two_nodes_are_summed() -> None:
    items = [item("a1"), item("a2"), item("b1", needs=("a1", "a2")), item("b2", needs=("a1",))]

    links = rules.dependency_links(items, {"a1": "a", "a2": "a", "b1": "b", "b2": "b"})

    assert links == [LinkFact("a", "b", 3)]


def test_the_opposite_direction_is_a_line_of_its_own() -> None:
    items = [item("a1", needs=("b1",)), item("b1", needs=("a1",))]

    links = rules.dependency_links(items, {"a1": "a", "b1": "b"})

    assert links == [LinkFact("a", "b", 1), LinkFact("b", "a", 1)]


def test_a_dependency_inside_one_node_gives_no_line() -> None:
    items = [item("a1"), item("a2", needs=("a1",))]

    assert rules.dependency_links(items, {"a1": "a", "a2": "a"}) == []


def test_items_without_a_node_or_in_the_trash_or_outside_the_project_give_no_line() -> None:
    items = [
        item("a1"),
        item("loose", needs=("a1",)),
        item("gone", needs=("a1",), deleted=True),
        item("b1", needs=("a1", "foreign")),
    ]

    links = rules.dependency_links(items, {"a1": "a", "b1": "b", "gone": "b"})

    assert links == [LinkFact("a", "b", 1)]


def test_the_status_filter_counts_only_items_it_lets_through_on_both_ends() -> None:
    items = [
        item("a1", status="Completed"),
        item("a2"),
        item("b1", needs=("a1", "a2")),
        item("c1", needs=("a2",), status="Completed"),
    ]
    effective = {"a1": "a", "a2": "a", "b1": "b", "c1": "c"}

    assert rules.dependency_links(items, effective, ["Open"]) == [LinkFact("a", "b", 1)]
    assert rules.dependency_links(items, effective, ["Completed"]) == []
    assert rules.dependency_links(items, effective) == [LinkFact("a", "b", 2), LinkFact("a", "c", 1)]

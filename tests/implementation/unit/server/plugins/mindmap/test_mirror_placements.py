"""Platzierungen aus der Baumliste einer Datei übernehmen: Regeln wie in der API, mit Fakes (ohne Datenbank)."""

from __future__ import annotations

import pytest

from viewer.plugins.mindmap.domain.listing import (
    changed_placements,
    changed_removed,
    check_no_children_of_removed,
    placements_from_listing,
)
from viewer.plugins.mindmap.domain.model import MindmapViolation, Placement, RemovedPlacement
from viewer.plugins.mindmap.domain.tree import apply, check_acyclic

T = "tree-1"


def _p(node: str, parent: str | None, position: int) -> Placement:
    return Placement(T, node, parent, position)


def test_a_listing_becomes_placements_with_parent_and_position_among_siblings() -> None:
    result = placements_from_listing(T, ["a", "b", "c", "d"], [0, 1, 1, 0])

    assert result == [_p("a", None, 0), _p("b", "a", 0), _p("c", "a", 1), _p("d", None, 1)]


def test_a_node_listed_twice_in_one_tree_is_a_rule_violation() -> None:
    with pytest.raises(MindmapViolation) as caught:
        placements_from_listing(T, ["a", "b", "a"], [0, 1, 1])

    assert caught.value.code == "mindmap_node_in_tree"


def test_an_indent_that_skips_a_level_is_a_rule_violation() -> None:
    with pytest.raises(MindmapViolation) as caught:
        placements_from_listing(T, ["a", "b"], [0, 2])

    assert caught.value.code == "mindmap_parent_missing"


def test_a_cycle_through_nodes_left_out_of_the_listing_is_found() -> None:
    # a steht (nicht gelistet) unter b; die Datei hängt b unter a
    kept = [_p("a", "b", 0), _p("b", "a", 0)]

    with pytest.raises(MindmapViolation) as caught:
        check_acyclic(kept)

    assert caught.value.code == "mindmap_loop"


def test_a_tree_without_a_cycle_passes() -> None:
    check_acyclic([_p("a", None, 0), _p("b", "a", 0), _p("c", "b", 0), _p("d", None, 1)])


def test_unchanged_placements_are_not_written_again_even_if_the_stored_positions_have_gaps() -> None:
    stored = [_p("a", None, 0), _p("b", None, 3), _p("c", "a", 5)]
    wanted = placements_from_listing(T, ["a", "c", "b"], [0, 1, 0])

    assert changed_placements(stored, wanted) == []


def test_a_reordered_group_is_rewritten_and_nodes_left_out_of_the_listing_stay_where_they_are() -> None:
    stored = [_p("a", None, 0), _p("b", None, 1), _p("x", None, 2)]
    wanted = placements_from_listing(T, ["b", "a"], [0, 0])

    result = changed_placements(stored, wanted)

    assert sorted((p.node_uid, p.parent_uid, p.position) for p in result) == [("a", None, 1), ("b", None, 0)]
    check_acyclic(apply(stored, result))


def _removed(node: str, parent: str | None = None, position: int = 0, root: str = "r") -> RemovedPlacement:
    return RemovedPlacement("t", node, parent, position, root)


def test_removed_rows_that_are_new_or_different_are_remembered_and_unchanged_ones_are_left_alone() -> None:
    stored = [_removed("a"), _removed("b", "a", 1)]
    wanted = [_removed("a"), _removed("b", "a", 2), _removed("c")]

    mark, forget = changed_removed(stored, wanted, listed=[])

    assert mark == [_removed("b", "a", 2), _removed("c")]
    assert forget == []


def test_a_removed_row_the_file_no_longer_names_is_forgotten_unless_the_node_is_listed_again() -> None:
    stored = [_removed("a"), _removed("b")]

    mark, forget = changed_removed(stored, [_removed("a")], listed=["b"])
    assert (mark, forget) == ([], [])

    mark, forget = changed_removed(stored, [_removed("a")], listed=[])
    assert (mark, forget) == ([], [_removed("b")])


def test_a_live_child_under_a_removed_parent_is_a_rule_violation() -> None:
    live = [Placement("t", "x", None, 0), Placement("t", "y", "a", 0)]

    check_no_children_of_removed(live, {"b"})
    with pytest.raises(MindmapViolation) as error:
        check_no_children_of_removed(live, {"a"})
    assert error.value.code == "mindmap_parent_removed"

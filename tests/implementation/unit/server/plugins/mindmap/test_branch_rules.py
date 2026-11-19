"""Äste: Ziel prüfen und Schnitte planen (`TASK-063`)."""

from __future__ import annotations

import pytest
from viewer.plugins.mindmap.domain import branches
from viewer.plugins.mindmap.domain.model import (
    MindmapViolation,
    Placement,
    RemovedPlacement,
)

A, B = "tree-a", "tree-b"


def _p(tree: str, *rows: tuple[str, str | None, int]) -> list[Placement]:
    return [Placement(tree, n, parent, pos) for n, parent, pos in rows]


def _sample() -> list[Placement]:
    """r (x (y, z (w)), q)"""
    return _p(
        A,
        ("r", None, 0),
        ("x", "r", 0),
        ("q", "r", 1),
        ("y", "x", 0),
        ("z", "x", 1),
        ("w", "z", 0),
    )


def test_a_branch_lists_the_node_and_all_descendants_parents_first() -> None:
    assert branches.branch_uids(_sample(), "x") == ["x", "y", "z", "w"]
    assert branches.branch_uids(_sample(), "w") == ["w"]


def test_a_live_branch_stops_at_nodes_in_the_trash() -> None:
    assert branches.branch_uids(_sample(), "x", live={"x", "y", "w"}) == ["x", "y"]


def test_a_target_that_already_holds_branch_nodes_is_rejected_with_the_list() -> None:
    target = _p(B, ("w", None, 0), ("y", None, 1), ("n", None, 2))
    with pytest.raises(MindmapViolation) as caught:
        branches.check_target_free(target, ["x", "y", "z", "w"], live={"w", "y", "n"})
    assert caught.value.code == "mindmap_target_conflict"
    assert caught.value.details["nodes"] == ["y", "w"]


def test_a_trashed_node_in_the_target_does_not_block() -> None:
    target = _p(B, ("w", None, 0))
    branches.check_target_free(target, ["x", "w"], live=set())


def test_the_copy_below_the_root_keeps_the_structure_and_appends_at_the_end() -> None:
    target = _p(B, ("n", None, 0), ("m", None, 1))
    made = branches.graft(_sample(), "x", ["x", "y", "z", "w"], B, target)
    assert sorted((p.node_uid, p.parent_uid, p.position) for p in made) == [
        ("w", "z", 0),
        ("x", None, 2),
        ("y", "x", 0),
        ("z", "x", 1),
    ]
    assert {p.tree_uid for p in made} == {B}


def test_a_node_with_one_placement_goes_to_the_trash_with_its_whole_branch() -> None:
    cut = branches.plan_cuts({A: _sample()}, "x", {n: {A} for n in "rxqyzw"})
    assert cut.removed == []
    assert cut.reparented == []
    assert cut.homeless == ["x", "y", "z", "w"]


def test_a_shared_root_is_only_taken_out_and_homeless_children_move_up() -> None:
    standing = {n: {A} for n in "rxqyzw"}
    standing["x"] = {A, B}
    standing["z"] = {A, B}
    cut = branches.plan_cuts({A: _sample()}, "x", standing)
    assert sorted(p.node_uid for p in cut.removed) == ["x", "z"]
    assert cut.homeless == ["y", "w"]
    # y hängt nun an r (dem alten Parent von x), w an r statt an dem gehenden z
    assert sorted((p.node_uid, p.parent_uid) for p in cut.reparented) == [
        ("w", "r"),
        ("y", "r"),
    ]
    positions = [p.position for p in cut.reparented]
    assert len(set(positions)) == 2 and min(positions) >= 2  # hinter q


def test_a_shared_descendant_stays_alive_when_only_the_root_is_homeless() -> None:
    standing = {n: {A} for n in "rxqyzw"}
    standing["z"] = {A, B}
    cut = branches.plan_cuts({A: _sample()}, "x", standing)
    assert [p.node_uid for p in cut.removed] == ["z"]
    assert cut.homeless == ["x", "y", "w"]
    assert [(p.node_uid, p.parent_uid) for p in cut.reparented] == [("w", "x")]


def test_deleting_everywhere_cuts_every_tree_before_counting_what_stays() -> None:
    other = _p(B, ("x", None, 0), ("y", "x", 0), ("k", "y", 0))
    standing = {
        "r": {A},
        "x": {A, B},
        "q": {A},
        "y": {A, B},
        "z": {A},
        "w": {A},
        "k": {B},
    }
    cut = branches.plan_cuts({A: _sample(), B: other}, "x", standing)
    assert cut.removed == []
    assert cut.homeless == ["x", "y", "z", "w", "k"]


# --- Entfernte Platzierungen wieder einsetzen (`TASK-066`) ------------------------------------------------------------


def _gone(root: str, *rows: tuple[str, str | None, int]) -> list[RemovedPlacement]:
    return [RemovedPlacement(A, n, parent, pos, root) for n, parent, pos in rows]


def test_a_removed_branch_returns_as_a_group_to_its_old_parent_and_place() -> None:
    live = _p(A, ("r", None, 0), ("q", "r", 0), ("s", "r", 1))
    gone = _gone("x", ("x", "r", 1), ("y", "x", 0), ("z", "x", 1))
    result = branches.plan_restore(
        gone, "x", live, alive={"r", "q", "s", "x", "y", "z"}
    )

    assert not result.fell_back
    assert result.restored == ["x", "y", "z"]
    placed = {p.node_uid: (p.parent_uid, p.position) for p in result.placements}
    assert placed["x"] == ("r", 1)
    assert placed["s"] == ("r", 2)  # das Geschwister rückt nach, nichts ist „belegt“
    assert placed["y"] == ("x", 0) and placed["z"] == ("x", 1)


def test_a_missing_old_parent_puts_the_branch_under_the_root_and_says_so() -> None:
    live = _p(A, ("r", None, 0))
    gone = _gone("x", ("x", "gone-parent", 0), ("y", "x", 0))
    result = branches.plan_restore(gone, "x", live, alive={"r", "x", "y"})

    assert result.fell_back
    placed = {p.node_uid: p.parent_uid for p in result.placements}
    assert placed["x"] is None and placed["y"] == "x"


def test_an_old_parent_in_the_trash_counts_as_missing() -> None:
    live = _p(A, ("r", None, 0), ("p", "r", 0))
    gone = _gone("x", ("x", "p", 0))
    result = branches.plan_restore(gone, "x", live, alive={"r", "x"})

    assert result.fell_back
    assert [p.parent_uid for p in result.placements if p.node_uid == "x"] == [None]


def test_a_root_level_placement_returns_without_fallback() -> None:
    gone = _gone("x", ("x", None, 0))
    result = branches.plan_restore(gone, "x", [], alive={"x"})
    assert not result.fell_back
    assert [(p.node_uid, p.parent_uid) for p in result.placements] == [("x", None)]


def test_restoring_a_member_brings_back_only_its_own_subtree() -> None:
    gone = _gone("x", ("x", "r", 0), ("y", "x", 0), ("z", "x", 1), ("w", "z", 0))
    result = branches.plan_restore(
        gone, "z", _p(A, ("r", None, 0)), alive={"r", "x", "y", "z", "w"}
    )

    assert result.restored == ["z", "w"]
    assert result.fell_back  # sein Parent x ist noch entfernt
    assert {p.node_uid: p.parent_uid for p in result.placements} == {
        "z": None,
        "w": "z",
    }


def test_members_in_the_trash_stay_removed_with_their_subtree() -> None:
    gone = _gone("x", ("x", None, 0), ("y", "x", 0), ("v", "y", 0), ("z", "x", 1))
    result = branches.plan_restore(gone, "x", [], alive={"x", "z", "v"})

    assert result.restored == ["x", "z"]
    assert result.skipped == ["y", "v"]


def test_a_node_without_a_removed_placement_is_rejected() -> None:
    with pytest.raises(MindmapViolation) as caught:
        branches.plan_restore(
            _gone("x", ("x", None, 0)), "other", [], alive={"x", "other"}
        )
    assert caught.value.code == "mindmap_nothing_to_restore"


def test_a_node_that_stands_in_the_tree_again_is_rejected() -> None:
    live = _p(A, ("x", None, 0))
    with pytest.raises(MindmapViolation) as caught:
        branches.plan_restore(_gone("x", ("x", None, 0)), "x", live, alive={"x"})
    assert caught.value.code == "mindmap_node_in_tree"

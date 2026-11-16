from __future__ import annotations

import pytest
from mindmap_fixtures import TREE, placed, sample
from viewer.plugins.mindmap.domain import tree
from viewer.plugins.mindmap.domain.model import MindmapViolation, Placement

ALL = {"a", "b", "c", "d", "e", "x"}


def _order(placements: list[Placement], parent: str | None) -> list[str]:
    return [p.node_uid for p in tree.children_of(placements, parent)]


def test_children_come_in_the_order_of_their_position() -> None:
    assert _order(sample(), None) == ["a", "e"]
    assert _order(sample(), "a") == ["b", "c"]
    assert _order(sample(), "e") == []


def test_descendants_are_listed_parents_first() -> None:
    assert tree.descendants(sample(), "a") == ["b", "c", "d"]
    assert tree.descendants(sample(), "d") == []


def test_a_new_node_is_appended_or_inserted_and_siblings_are_renumbered() -> None:
    appended = tree.apply(sample(), tree.arrange(sample(), TREE, "x", "a", None, ALL))
    assert _order(appended, "a") == ["b", "c", "x"]
    inserted = tree.apply(sample(), tree.arrange(sample(), TREE, "x", "a", 1, ALL))
    assert _order(inserted, "a") == ["b", "x", "c"]
    assert [p.position for p in tree.children_of(inserted, "a")] == [0, 1, 2]
    top = tree.apply(sample(), tree.arrange(sample(), TREE, "x", None, 0, ALL))
    assert _order(top, None) == ["x", "a", "e"]


def test_a_position_beyond_the_end_means_the_end_and_a_negative_one_is_refused() -> None:
    far = tree.apply(sample(), tree.arrange(sample(), TREE, "x", "a", 99, ALL))
    assert _order(far, "a") == ["b", "c", "x"]
    with pytest.raises(MindmapViolation) as error:
        tree.arrange(sample(), TREE, "x", "a", -1, ALL)
    assert error.value.code == "mindmap_position_invalid"


def test_a_node_is_placed_at_most_once_per_tree() -> None:
    with pytest.raises(MindmapViolation) as error:
        tree.check_new(sample(), "b", "e", ALL)
    assert error.value.code == "mindmap_node_in_tree"


def test_the_parent_must_be_in_the_tree_and_alive() -> None:
    with pytest.raises(MindmapViolation) as error:
        tree.check_new(sample(), "x", "unknown", ALL)
    assert error.value.code == "mindmap_parent_missing"
    with pytest.raises(MindmapViolation) as error:
        tree.check_new(sample(), "x", "c", ALL - {"c"})  # c liegt im Papierkorb
    assert error.value.code == "mindmap_parent_missing"
    tree.check_new(sample(), "x", None, ALL)


def test_a_node_cannot_move_below_itself_or_its_descendants() -> None:
    for parent in ("a", "b", "d"):
        with pytest.raises(MindmapViolation) as error:
            tree.check_move(sample(), "a", parent, ALL)
        assert error.value.code == "mindmap_loop"
    tree.check_move(sample(), "a", "e", ALL)
    tree.check_move(sample(), "d", None, ALL)


def test_only_a_placed_node_can_move() -> None:
    with pytest.raises(MindmapViolation) as error:
        tree.check_move(sample(), "x", None, ALL)
    assert error.value.code == "mindmap_node_not_in_tree"


def test_moving_renumbers_the_old_and_the_new_siblings() -> None:
    moved = tree.arrange(sample(), TREE, "b", "e", 0, ALL)
    changed = {p.node_uid: p for p in tree.apply(sample(), moved)}
    assert changed["b"].parent_uid == "e"
    assert _order(tree.apply(sample(), moved), "a") == ["c"]
    assert [p.position for p in tree.children_of(tree.apply(sample(), moved), "a")] == [0]


def test_moving_inside_the_same_parent_reorders() -> None:
    moved = tree.arrange(sample(), TREE, "b", "a", 1, ALL)
    assert _order(tree.apply(sample(), moved), "a") == ["c", "b"]
    first = tree.arrange(sample(), TREE, "c", "a", 0, ALL)
    assert _order(tree.apply(sample(), first), "a") == ["c", "b"]


def test_arrange_returns_only_what_changed() -> None:
    moved = tree.arrange(sample(), TREE, "e", None, 0, ALL)
    assert {p.node_uid for p in moved} == {"a", "e"}
    unchanged = tree.arrange(sample(), TREE, "a", None, 0, ALL)
    assert unchanged == []


def test_deleted_siblings_keep_their_place_and_do_not_count_for_the_index() -> None:
    live = ALL - {"b"}  # b liegt im Papierkorb
    result = tree.apply(sample(), tree.arrange(sample(), TREE, "x", "a", 1, live))
    live_order = [p.node_uid for p in tree.children_of(result, "a") if p.node_uid in live]
    assert live_order == ["c", "x"]
    assert any(p.node_uid == "b" for p in result)


def test_a_tree_belongs_to_exactly_one_project() -> None:
    tree.check_project("p1", "p1")
    with pytest.raises(MindmapViolation) as error:
        tree.check_project("p1", "p2")
    assert error.value.code == "mindmap_other_project"


def test_a_project_has_one_project_tree() -> None:
    tree.check_tree_free([], "p1")
    with pytest.raises(MindmapViolation) as error:
        tree.check_tree_free(["p1"], "p1")
    assert error.value.code == "mindmap_tree_exists"


def test_a_cycle_in_stored_data_is_reported_not_followed_forever() -> None:
    cyclic = placed(("a", "b", 0), ("b", "a", 0))
    with pytest.raises(MindmapViolation) as error:
        tree.descendants(cyclic, "a")
    assert error.value.code == "mindmap_loop"


def test_a_reader_sees_gapless_positions_among_the_living() -> None:
    result = tree.compacted(sample(), ALL - {"b"})
    assert {(p.node_uid, p.position) for p in result} == {("a", 0), ("e", 1), ("c", 0), ("d", 0)}
    assert tree.compacted(sample(), {"a", "e"}) == tree.children_of(sample(), None)

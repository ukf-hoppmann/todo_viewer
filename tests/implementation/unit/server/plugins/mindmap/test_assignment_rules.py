from __future__ import annotations

import pytest
from viewer.plugins.mindmap.domain import assignment as rules
from viewer.plugins.mindmap.domain.assignment import ItemFact, NodeStats
from viewer.plugins.mindmap.domain.model import MindmapViolation

#: Baum: wurzel → a → (b, c); wurzel → e
PARENT: dict[str, str | None] = {"a": None, "b": "a", "c": "a", "e": None}
LIVE = {"a", "b", "c", "e"}


def item(uid: str, status: str = "Open", parent: str | None = None, deleted: bool = False) -> ItemFact:
    return ItemFact(uid, parent, status, deleted)


def test_an_assigned_item_counts_for_its_node_and_every_node_above() -> None:
    result = rules.overview([item("t1")], {"t1": "b"}, LIVE, PARENT)

    assert result.effective == {"t1": "b"}
    assert result.stats["b"].total == 1
    assert result.stats["a"].total == 1
    assert result.stats["c"].total == 0
    assert result.stats["e"].total == 0


def test_children_inherit_the_node_of_their_parent() -> None:
    items = [item("epic"), item("story", parent="epic"), item("task", parent="story")]

    effective = rules.effective_nodes(items, {"epic": "a"}, LIVE, PARENT)

    assert effective == {"epic": "a", "story": "a", "task": "a"}


def test_an_item_attached_on_its_own_takes_its_children_along() -> None:
    items = [item("epic"), item("story", parent="epic"), item("task", parent="story")]

    effective = rules.effective_nodes(items, {"epic": "a", "story": "e"}, LIVE, PARENT)

    assert effective == {"epic": "a", "story": "e", "task": "e"}


def test_items_without_a_node_anywhere_up_the_chain_are_unassigned() -> None:
    items = [item("epic"), item("story", parent="epic"), item("loose")]

    result = rules.overview(items, {}, LIVE, PARENT)

    assert result.unassigned == ["epic", "loose", "story"]
    assert result.effective == {}
    assert all(stats.total == 0 for stats in result.stats.values())


def test_every_item_counts_exactly_once_also_across_empty_nodes() -> None:
    items = [item("epic"), item("story", parent="epic"), item("other")]

    result = rules.overview(items, {"epic": "a", "other": "b"}, LIVE, PARENT)

    assert result.stats["a"] == NodeStats(total=3, done=0, state=rules.STATE_PLANNED)
    assert result.stats["b"].total == 1
    assert result.stats["c"] == NodeStats(total=0, done=0, state=rules.STATE_IDEA)  # leerer Knoten
    assert sum(1 for node in result.effective.values() if node) == 3


def test_a_node_above_empty_nodes_sums_up_what_lies_below() -> None:
    parent: dict[str, str | None] = {"top": None, "mid": "top", "leaf": "mid", "empty": "mid"}
    result = rules.overview([item("t")], {"t": "leaf"}, set(parent), parent)

    assert [result.stats[n].total for n in ("top", "mid", "leaf", "empty")] == [1, 1, 1, 0]


def test_trashed_items_never_count_and_do_not_show_as_unassigned() -> None:
    items = [item("gone", deleted=True), item("kept")]

    result = rules.overview(items, {"gone": "a", "kept": "a"}, LIVE, PARENT)

    assert result.stats["a"].total == 1
    assert "gone" not in result.effective
    assert rules.overview([item("gone", deleted=True)], {}, LIVE, PARENT).unassigned == []


def test_the_status_filter_decides_what_counts_but_not_the_state() -> None:
    items = [item("done", "Completed"), item("open", "Open")]
    assigned = {"done": "a", "open": "a"}

    everything = rules.overview(items, assigned, LIVE, PARENT).stats["a"]
    only_open = rules.overview(items, assigned, LIVE, PARENT, statuses={"Open"}).stats["a"]

    assert everything == NodeStats(total=2, done=1, state=rules.STATE_ACTIVE)
    assert only_open == NodeStats(total=1, done=0, state=rules.STATE_ACTIVE)


def test_the_filter_also_applies_to_the_unassigned_items() -> None:
    items = [item("done", "Completed"), item("open", "Open")]

    assert rules.overview(items, {}, LIVE, PARENT, statuses={"Open"}).unassigned == ["open"]


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([], rules.STATE_IDEA),
        (["Rejected"], rules.STATE_IDEA),
        (["Open"], rules.STATE_PLANNED),
        (["Open", "Open", "Rejected"], rules.STATE_PLANNED),
        (["In progress"], rules.STATE_ACTIVE),
        (["Awaiting confirmation"], rules.STATE_ACTIVE),
        (["Open", "In progress"], rules.STATE_ACTIVE),
        (["Completed", "Open"], rules.STATE_ACTIVE),
        (["Completed"], rules.STATE_DONE),
        (["Completed", "Rejected"], rules.STATE_DONE),
    ],
)
def test_the_state_follows_the_table_of_the_story_spec(statuses: list[str], expected: str) -> None:
    assert rules.state_of(statuses) == expected


def test_rejected_items_count_in_the_number_but_not_in_the_state() -> None:
    items = [item("r", "Rejected"), item("c", "Completed")]

    stats = rules.overview(items, {"r": "a", "c": "a"}, LIVE, PARENT).stats["a"]

    assert stats == NodeStats(total=2, done=1, state=rules.STATE_DONE)


def test_the_state_comes_from_the_subtree_not_from_the_node_alone() -> None:
    items = [item("open"), item("busy", "In progress")]

    result = rules.overview(items, {"open": "a", "busy": "b"}, LIVE, PARENT)

    assert result.stats["a"].state == rules.STATE_ACTIVE
    assert result.stats["c"].state == rules.STATE_IDEA


def test_a_trashed_node_hands_its_items_to_the_nearest_living_ancestor() -> None:
    live = {"a", "c", "e"}  # b liegt im Papierkorb, behält aber seine Lage
    result = rules.overview([item("t")], {"t": "b"}, live, PARENT)

    assert result.effective == {"t": "a"}
    assert result.stats["a"].total == 1


def test_a_trashed_node_without_a_parent_node_leaves_the_item_unassigned() -> None:
    result = rules.overview([item("t")], {"t": "a"}, {"b", "c", "e"}, PARENT)

    assert result.unassigned == ["t"]
    assert result.effective == {}


def test_an_item_of_a_trashed_top_node_falls_back_to_the_node_of_its_parent_item() -> None:
    items = [item("epic"), item("story", parent="epic")]
    live = {"b", "c", "e"}  # a liegt im Papierkorb

    effective = rules.effective_nodes(items, {"epic": "b", "story": "a"}, live, PARENT)

    assert effective == {"epic": "b", "story": "b"}  # als wäre die Zuordnung zu a nie da gewesen


def test_the_result_returns_when_the_node_comes_back() -> None:
    items = [item("t")]
    trashed = rules.overview(items, {"t": "b"}, {"c", "e"}, PARENT)
    restored = rules.overview(items, {"t": "b"}, LIVE, PARENT)

    assert trashed.effective == {}
    assert restored.effective == {"t": "b"}


def test_a_loop_in_the_item_parents_does_not_hang_the_calculation() -> None:
    items = [item("x", parent="y"), item("y", parent="x")]

    assert rules.overview(items, {}, LIVE, PARENT).unassigned == ["x", "y"]


def test_a_second_node_for_an_item_is_refused_unless_replacing_is_explicit() -> None:
    with pytest.raises(MindmapViolation) as error:
        rules.check_assign(["a"], "b", replace=False)
    assert error.value.code == "mindmap_item_assigned"

    assert rules.check_assign(["a"], "b", replace=True) == ["a"]


def test_assigning_to_the_same_node_again_or_to_a_free_item_needs_no_change() -> None:
    assert rules.check_assign([], "a", replace=False) == []
    assert rules.check_assign(["a"], "a", replace=False) == []

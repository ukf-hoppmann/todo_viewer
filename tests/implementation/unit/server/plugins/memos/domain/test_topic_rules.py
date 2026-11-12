from __future__ import annotations

import pytest
from memos_fixtures import NOW, memo, topic
from viewer.plugins.memos.domain.model import MemosViolation
from viewer.plugins.memos.domain.topics import (
    ARCHIVE_TARGET,
    Choice,
    check_parent,
    content,
    depth,
    height,
    plan_archive,
    plan_delete,
    plan_reactivate,
    subtree,
)

#   a
#   ├─ b
#   │  └─ c
#   └─ d
TOPICS = [topic("a"), topic("b", "a"), topic("c", "b"), topic("d", "a"), topic("z")]


def code_of(call) -> str:  # type: ignore[no-untyped-def]
    with pytest.raises(MemosViolation) as error:
        call()
    return error.value.code


def test_depth_and_height_count_levels() -> None:
    live = {t.uid: t for t in TOPICS}
    assert [depth(live, uid) for uid in "abcdz"] == [1, 2, 3, 2, 1]
    assert [height(TOPICS, uid) for uid in "abcdz"] == [3, 2, 1, 1, 1]


def test_subtree_lists_the_topic_first_and_skips_deleted_ones() -> None:
    assert [t.uid for t in subtree(TOPICS, "a")] == ["a", "b", "d", "c"]
    gone = [*TOPICS[:2], topic("c", "b", deleted_at=NOW), *TOPICS[3:]]
    assert [t.uid for t in subtree(gone, "a")] == ["a", "b", "d"]


def test_a_new_topic_must_fit_into_the_depth() -> None:
    check_parent(TOPICS, "p", "b", None, 3)
    assert code_of(lambda: check_parent(TOPICS, "p", "c", None, 3)) == "topic_too_deep"
    check_parent(TOPICS, "p", "c", None, 4)


def test_moving_checks_the_whole_subtree() -> None:
    check_parent(TOPICS, "p", "z", "b", 3)  # z/b/c = 3 levels
    assert code_of(lambda: check_parent(TOPICS, "p", "d", "b", 3)) == "topic_too_deep"  # a/d/b/c = 4
    check_parent(TOPICS, "p", None, "c", 3)


def test_a_topic_cannot_move_below_itself() -> None:
    assert code_of(lambda: check_parent(TOPICS, "p", "c", "a", 9)) == "topic_loop"
    assert code_of(lambda: check_parent(TOPICS, "p", "a", "a", 9)) == "topic_loop"


def test_parent_must_exist_belong_to_the_project_and_be_active() -> None:
    assert code_of(lambda: check_parent(TOPICS, "p", "nope", None, 3)) == "topic_parent_missing"
    assert code_of(lambda: check_parent(TOPICS, "other", "a", None, 3)) == "topic_other_project"
    archived = [topic("a", archived_at=NOW)]
    assert code_of(lambda: check_parent(archived, "p", "a", None, 3)) == "topic_archived"


NOTES = [
    memo("n1", "b"),
    memo("n2", "c"),
    memo("n3", "c", status="done", archived=True),
    memo("n4", "z"),
    memo("n5", "b", deleted_at=NOW),
]


def test_content_counts_active_and_archived_memos_and_sub_topics() -> None:
    found = content(TOPICS, NOTES, "a")
    assert (found.topics, found.active, found.archived) == (3, 2, 1)
    assert content(TOPICS, NOTES, "d").empty


def test_deleting_an_empty_topic_needs_no_choice() -> None:
    plan = plan_delete(TOPICS, NOTES, "d", None)
    assert (plan.topics, plan.memos, plan.moves) == (("d",), (), {})


def test_deleting_a_topic_with_content_asks_for_a_choice_and_reports_the_numbers() -> None:
    with pytest.raises(MemosViolation) as error:
        plan_delete(TOPICS, NOTES, "a", None)
    assert error.value.code == "topic_has_content"
    assert error.value.details == {"active": 2, "archived": 1, "topics": 3}


def test_unchosen_groups_go_to_the_trash_with_the_topic() -> None:
    plan = plan_delete(TOPICS, NOTES, "a", Choice(active="delete"))
    assert plan.topics == ("a", "b", "d", "c")
    assert set(plan.memos) == {"n1", "n2", "n3"}
    assert plan.moves == {}


def test_archived_memos_can_be_kept_and_active_ones_moved() -> None:
    plan = plan_delete(TOPICS, NOTES, "a", Choice(keep_archived=True, active="move", move_to="z"))
    assert plan.memos == ()
    assert plan.moves == {"n1": "z", "n2": "z", "n3": ARCHIVE_TARGET}


def test_active_memos_can_move_to_no_topic() -> None:
    plan = plan_delete(TOPICS, NOTES, "a", Choice(keep_archived=True, active="move", move_to=None))
    assert plan.moves["n1"] is None


def test_the_target_must_exist_and_lie_outside_the_topic() -> None:
    assert code_of(lambda: plan_delete(TOPICS, NOTES, "a", Choice(active="move", move_to="c"))) == "topic_target_inside"
    assert (
        code_of(lambda: plan_delete(TOPICS, NOTES, "a", Choice(active="move", move_to="nope")))
        == "topic_parent_missing"
    )


def test_active_memos_need_a_decision_when_there_are_any() -> None:
    assert code_of(lambda: plan_delete(TOPICS, NOTES, "a", Choice(keep_archived=True))) == "choice_missing"
    plan_delete(TOPICS, NOTES, "z", Choice(active="delete"))


def test_system_topics_cannot_be_deleted_or_archived() -> None:
    system = [topic("s", system=True)]
    assert code_of(lambda: plan_delete(system, [], "s", None)) == "topic_system"
    assert code_of(lambda: plan_archive(system, [], "s", None)) == "topic_system"


def test_archiving_can_archive_the_active_memos_with_the_topic() -> None:
    plan = plan_archive(TOPICS, NOTES, "b", Choice(active="archive"))
    assert plan.topics == ("b", "c")
    assert set(plan.memos) == {"n1", "n2", "n3"}


def test_archiving_cannot_delete_and_deleting_cannot_archive() -> None:
    assert code_of(lambda: plan_archive(TOPICS, NOTES, "b", Choice(active="delete"))) == "choice_invalid"
    assert code_of(lambda: plan_delete(TOPICS, NOTES, "b", Choice(active="archive"))) == "choice_invalid"


def test_an_archived_topic_cannot_be_archived_again() -> None:
    assert code_of(lambda: plan_archive([topic("a", archived_at=NOW)], [], "a", None)) == "topic_archived"


def test_reactivating_restores_only_memos_that_were_archived_because_of_the_topic() -> None:
    topics = [topic("a", archived_at=NOW), topic("b", "a", archived_at=NOW), topic("x", "a")]
    memos = [
        memo("n1", "a", archived=True),  # wegen des Topics
        memo("n2", "b", archived=True, status="snoozed"),  # wegen des Topics
        memo("n3", "a", archived=True, status="done"),  # unabhängig archiviert
        memo("n4", "x", archived=True),  # Topic x ist nicht archiviert
    ]
    plan = plan_reactivate(topics, memos, "a")
    assert plan.topics == ("a", "b")
    assert set(plan.memos) == {"n1", "n2"}


def test_a_topic_below_an_archived_parent_cannot_be_reactivated_alone() -> None:
    topics = [topic("a", archived_at=NOW), topic("b", "a", archived_at=NOW)]
    assert code_of(lambda: plan_reactivate(topics, [], "b")) == "topic_archived"
    assert code_of(lambda: plan_reactivate(topics, [], "x")) == "topic_deleted"
    assert code_of(lambda: plan_reactivate([topic("a")], [], "a")) == "topic_not_archived"

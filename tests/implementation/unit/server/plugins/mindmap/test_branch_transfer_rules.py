"""Ast überführen: Plan prüfen und ordnen, reine Regeln ohne Ports (`TASK-074`)."""

from __future__ import annotations

from typing import Any

from viewer.plugins.mindmap.domain.model import Node
from viewer.plugins.mindmap.domain.transfer import TransferEntry, map_problem, plan_transfer

CRITERIA = {"completion_criteria": "1. Fertig"}


def _node(uid: str, title: str | None = None, text: str | None = None) -> Node:
    return Node(uid, "p1", uid.upper(), title or f"Thema {uid}", text, 1)


BRANCH = [_node("a", text="Text A"), _node("b"), _node("c"), _node("d")]


def _item(node: str, type_: str = "Task", **rest: Any) -> TransferEntry:
    fields = rest.pop("fields", CRITERIA)
    return TransferEntry(node=node, kind="item", type=type_, fields=fields, **rest)


def _problems(draft: Any, node: str) -> list[str]:
    return [p.code for e in draft.entries if e.node == node for p in e.problems]


def test_items_take_title_and_goal_from_the_node_and_get_the_default_required_flag() -> None:
    draft = plan_transfer(BRANCH, [_item("a", "Epic"), _item("b", "Story", parent="a")])
    a, b = draft.items
    assert (a.key, a.type, a.fields["title"], a.fields["goal"]) == ("a", "Epic", "Thema a", "Text A")
    assert (b.parent_key, b.fields["required_for_parent"]) == ("a", True)
    assert draft.problems == [] and all(e.problems == [] for e in draft.entries)


def test_a_node_without_an_entry_and_a_skip_create_nothing() -> None:
    draft = plan_transfer(BRANCH, [_item("a"), TransferEntry(node="b", kind="skip")])
    assert [i.key for i in draft.items] == ["a"] and draft.order == ["a"]
    assert [e.node for e in draft.entries] == ["a", "b"]


def test_parents_and_dependencies_come_before_their_followers() -> None:
    entries = [
        _item("c", parent="b"),
        _item("b", "Story", parent="a"),
        _item("a", "Epic", depends_on=("d",)),
        _item("d"),
    ]
    draft = plan_transfer(BRANCH, entries)
    order = draft.order
    assert order.index("a") < order.index("b") < order.index("c") and order.index("d") < order.index("a")


def test_a_memo_has_no_relations_and_cannot_be_a_target() -> None:
    entries = [
        TransferEntry(node="a", kind="memo", memo={"body": "B"}),
        _item("b", parent="a"),
        _item("c", depends_on=("a",)),
        TransferEntry(node="d", kind="memo", parent="b"),
    ]
    draft = plan_transfer(BRANCH, entries)
    assert _problems(draft, "b") == ["parent_is_memo"]
    assert _problems(draft, "c") == ["depends_on_is_memo"]
    assert _problems(draft, "d") == ["memo_with_relation"]
    memo = next(e for e in draft.entries if e.node == "a")
    assert memo.memo_fields == {"summary": "Thema a", "body": "B"}


def test_nodes_outside_the_branch_and_duplicates_are_reported() -> None:
    draft = plan_transfer(BRANCH, [_item("zzz"), _item("a"), _item("A")])
    assert _problems(draft, "zzz") == ["node_not_in_branch"]
    assert [p for e in draft.entries for p in e.problems if p.code == "node_duplicate"]
    assert [i.key for i in draft.items] == ["a"]


def test_the_kind_and_the_type_must_be_valid() -> None:
    draft = plan_transfer(
        BRANCH,
        [
            _item("a", "Thema"),
            TransferEntry(node="b", kind="item", type=None, fields=CRITERIA),
            TransferEntry(node="c", kind="idee"),
        ],
    )
    assert _problems(draft, "a") == ["invalid_type"]
    assert _problems(draft, "b") == ["invalid_type"]
    assert _problems(draft, "c") == ["invalid_kind"]
    assert draft.items == []


def test_a_parent_that_is_a_node_of_the_branch_without_an_item_is_not_found() -> None:
    draft = plan_transfer(BRANCH, [_item("b", parent="a")])
    assert _problems(draft, "b") == ["parent_not_found"]


def test_a_parent_outside_the_plan_is_an_existing_item_for_the_backlog_to_check() -> None:
    draft = plan_transfer(BRANCH, [_item("b", parent="STORY-001", depends_on=("TASK-002",))])
    [planned] = draft.items
    assert planned.parent_key is None and planned.fields["parent"] == "STORY-001"
    assert planned.fields["dependencies"] == ["TASK-002"] and planned.fields["required_for_parent"] is True


def test_backlog_codes_become_the_codes_of_the_plan() -> None:
    assert map_problem("value_required", {"field": "goal"}) == "goal_missing"
    assert map_problem("value_required", {"field": "completion_criteria"}) == "criteria_missing"
    assert map_problem("invalid_input", {"field": "type"}) == "invalid_type"
    assert map_problem("epic_with_parent", {}) == "parent_type_not_allowed"
    assert map_problem("parent_closed", {}) == "parent_closed"

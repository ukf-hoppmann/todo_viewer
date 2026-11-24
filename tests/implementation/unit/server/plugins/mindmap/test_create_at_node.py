"""Item oder Memo aus einem Knoten anlegen: Standardwerte der Felder und Ablauf mit Fakes der Ports (`TASK-073`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from viewer.core.domain.errors import DomainError, InvalidInput
from viewer.plugins.mindmap.application.creation import NodeCreationService
from viewer.plugins.mindmap.application.ports import CreatedElement
from viewer.plugins.mindmap.domain.creation import item_fields, memo_fields
from viewer.plugins.mindmap.domain.model import MindmapViolation, Node


def _node(**changes: Any) -> Node:
    base: dict[str, Any] = {
        "uid": "n1",
        "project_uid": "p1",
        "label": "NODE-1",
        "title": "Thema",
        "text": "Beschreibung",
        "revision": 1,
    }
    return Node(**{**base, **changes})


# --- Domain: Standardwerte ----------------------------------------------------------------------------------------


def test_an_item_takes_title_and_goal_from_the_node_when_they_are_missing() -> None:
    fields = item_fields(_node(), {"completion_criteria": "1. Fertig"})
    assert fields == {
        "title": "Thema",
        "goal": "Beschreibung",
        "completion_criteria": "1. Fertig",
    }


def test_given_fields_win_over_the_node() -> None:
    given = {
        "title": "Eigen",
        "goal": "Anders",
        "completion_criteria": "1. x",
        "priority": "Urgent",
    }
    assert item_fields(_node(), given) == given


def test_an_empty_title_or_goal_counts_as_missing() -> None:
    fields = item_fields(
        _node(), {"title": " ", "goal": "", "completion_criteria": "1. x"}
    )
    assert (fields["title"], fields["goal"]) == ("Thema", "Beschreibung")


def test_a_node_without_text_gives_no_goal_default() -> None:
    assert "goal" not in item_fields(_node(text=None), {"completion_criteria": "1. x"})


@pytest.mark.parametrize(
    "fields", [{}, {"completion_criteria": ""}, {"completion_criteria": "  "}]
)
def test_the_completion_criteria_are_required(fields: dict[str, Any]) -> None:
    with pytest.raises(InvalidInput) as error:
        item_fields(_node(), fields)
    assert error.value.details["field"] == "completion_criteria"


def test_a_memo_takes_summary_and_body_from_the_node() -> None:
    assert memo_fields(_node(), {}) == {"summary": "Thema", "body": "Beschreibung"}
    assert memo_fields(_node(), {"summary": "S", "body": "B", "topic": "t"}) == {
        "summary": "S",
        "body": "B",
        "topic": "t",
    }
    assert memo_fields(_node(text=None), {}) == {"summary": "Thema"}


# --- Anwendungsfall mit Fakes -------------------------------------------------------------------------------------


@dataclass
class _Fakes:
    node: Node
    calls: list[tuple[str, Any]]
    fail_assign: bool = False


class _Nodes:
    def __init__(self, fakes: _Fakes) -> None:
        self._f = fakes

    def node_for_creation(self, ref: str, project_uid: str | None) -> Node:
        if project_uid is not None and self._f.node.project_uid != project_uid:
            raise MindmapViolation("mindmap_other_project", "anderes Projekt")
        if self._f.node.deleted_at is not None:
            raise MindmapViolation("mindmap_node_deleted", "im Papierkorb")
        return self._f.node


class _Assign:
    def __init__(self, fakes: _Fakes) -> None:
        self._f = fakes

    def assign_item(
        self, item_ref: str, node_ref: str, project_uid: str | None, replace: bool
    ) -> Node:
        self._f.calls.append(("assign", (item_ref, node_ref)))
        if self._f.fail_assign:
            raise MindmapViolation("mindmap_item_assigned", "hängt schon")
        return self._f.node

    def link_memo(self, memo_ref: str, node_ref: str, project_uid: str | None) -> Node:
        self._f.calls.append(("link", (memo_ref, node_ref)))
        if self._f.fail_assign:
            raise MindmapViolation("mindmap_node_deleted", "weg")
        return self._f.node


class _Writer:
    def __init__(self, fakes: _Fakes) -> None:
        self._f = fakes

    def create_item(
        self, project_uid: str, type_: str, fields: dict[str, Any]
    ) -> CreatedElement:
        self._f.calls.append(("item", (project_uid, type_, fields)))
        return CreatedElement("i1", "TASK-1", str(fields["title"]))

    def create_memo(self, project_uid: str, fields: dict[str, Any]) -> CreatedElement:
        self._f.calls.append(("memo", (project_uid, fields)))
        return CreatedElement("m1", "MEMO-1", str(fields["summary"]))


def _service(
    node: Node | None = None, fail_assign: bool = False
) -> tuple[NodeCreationService, _Fakes]:
    fakes = _Fakes(node or _node(), [], fail_assign)
    writer = _Writer(fakes)
    return NodeCreationService(_Nodes(fakes), _Assign(fakes), writer, writer), fakes


def test_an_item_is_created_with_the_defaults_and_hung_on_the_node() -> None:
    service, fakes = _service()
    created = service.create_item("n1", "Story", {"completion_criteria": "1. x"}, None)
    assert created.element == CreatedElement("i1", "TASK-1", "Thema")
    assert created.node.uid == "n1"
    assert fakes.calls[0] == (
        "item",
        (
            "p1",
            "Story",
            {"title": "Thema", "goal": "Beschreibung", "completion_criteria": "1. x"},
        ),
    )
    assert fakes.calls[1] == ("assign", ("i1", "n1"))


def test_an_item_without_criteria_creates_nothing() -> None:
    service, fakes = _service()
    with pytest.raises(InvalidInput):
        service.create_item("n1", "Task", {}, None)
    assert fakes.calls == []


def test_a_node_in_the_trash_or_of_another_project_creates_nothing() -> None:
    service, fakes = _service()
    with pytest.raises(MindmapViolation) as other:
        service.create_item("n1", "Task", {"completion_criteria": "1. x"}, "p2")
    assert other.value.code == "mindmap_other_project"
    with pytest.raises(MindmapViolation) as other_memo:
        service.create_memo("n1", {}, "p2")
    assert other_memo.value.code == "mindmap_other_project"
    assert fakes.calls == []
    from datetime import UTC, datetime

    service, fakes = _service(_node(deleted_at=datetime(2026, 1, 1, tzinfo=UTC)))
    with pytest.raises(MindmapViolation) as gone:
        service.create_memo("n1", {}, None)
    assert gone.value.code == "mindmap_node_deleted"
    assert fakes.calls == []


def test_a_failing_assignment_names_the_created_item() -> None:
    service, fakes = _service(fail_assign=True)
    with pytest.raises(DomainError) as error:
        service.create_item("n1", "Task", {"completion_criteria": "1. x"}, None)
    assert error.value.code == "mindmap_assign_failed"
    assert error.value.details["created"] == {"uid": "i1", "label": "TASK-1"}
    assert error.value.details["cause"] == "mindmap_item_assigned"
    assert [c[0] for c in fakes.calls] == ["item", "assign"]


def test_a_memo_is_created_and_linked() -> None:
    service, fakes = _service()
    created = service.create_memo("n1", {}, None)
    assert created.element == CreatedElement("m1", "MEMO-1", "Thema")
    assert fakes.calls == [
        ("memo", ("p1", {"summary": "Thema", "body": "Beschreibung"})),
        ("link", ("m1", "n1")),
    ]


def test_a_failing_link_names_the_created_memo() -> None:
    service, _ = _service(fail_assign=True)
    with pytest.raises(DomainError) as error:
        service.create_memo("n1", {}, None)
    assert error.value.code == "mindmap_assign_failed"
    assert error.value.details["created"] == {"uid": "m1", "label": "MEMO-1"}

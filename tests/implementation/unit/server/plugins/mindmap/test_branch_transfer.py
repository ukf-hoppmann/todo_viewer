"""Ast überführen: Vorschau und Überführen mit Fakes der Ports (`TASK-074`)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from viewer.core.domain.errors import DomainError
from viewer.plugins.mindmap.application.creation import Created
from viewer.plugins.mindmap.application.ports import BacklogProblem, CreatedElement
from viewer.plugins.mindmap.application.transfer import BranchTransferService
from viewer.plugins.mindmap.domain.model import MindmapViolation, Node
from viewer.plugins.mindmap.domain.transfer import TransferEntry

CRITERIA = {"completion_criteria": "1. Fertig"}
NODES = {u: Node(u, "p1", u.upper(), f"Thema {u}", None, 1) for u in "abcd"}


class _Source:
    def branch_of(self, ref: str, project_uid: str | None, tree_uid: str | None) -> list[Node]:
        if ref not in ("a", "A"):
            raise MindmapViolation("mindmap_node_deleted", "weg")
        return list(NODES.values())


class _Checker:
    def __init__(self, problems: list[BacklogProblem] | None = None) -> None:
        self.problems = problems or []
        self.calls: list[Sequence[Any]] = []

    def check_new_items(self, project_uid: str, planned: Sequence[Any]) -> list[BacklogProblem]:
        self.calls.append(planned)
        return self.problems


class _Creation:
    """Ersetzt `NodeCreationService`: legt nichts an, merkt sich die Aufrufe, einzelne Knoten scheitern."""

    def __init__(self, failing: tuple[str, ...] = ()) -> None:
        self.calls: list[tuple[str, str, Any]] = []
        self.failing = failing

    def create_item(self, node_ref: str, type_: str, fields: dict[str, Any], project_uid: str | None) -> Created:
        self.calls.append(("item", node_ref, dict(fields)))
        if node_ref in self.failing:
            raise DomainError("kaputt", code="backlog_broken")
        uid = f"item-{node_ref}"
        return Created(CreatedElement(uid, uid.upper(), str(fields["title"]), type_), NODES[node_ref])

    def create_memo(self, node_ref: str, fields: dict[str, Any], project_uid: str | None) -> Created:
        self.calls.append(("memo", node_ref, dict(fields)))
        uid = f"memo-{node_ref}"
        return Created(CreatedElement(uid, uid.upper(), str(fields["summary"])), NODES[node_ref])


def _service(
    checker: _Checker | None = None, creation: _Creation | None = None
) -> tuple[BranchTransferService, _Checker, _Creation]:
    checker = checker or _Checker()
    creation = creation or _Creation()
    return BranchTransferService(_Source(), checker, creation), checker, creation


def _item(node: str, type_: str = "Task", **rest: Any) -> TransferEntry:
    return TransferEntry(node=node, kind="item", type=type_, fields=CRITERIA, **rest)


def test_the_preview_writes_nothing_and_reports_entries_and_order() -> None:
    service, checker, creation = _service()
    preview = service.preview("a", None, None, [_item("b", parent="a"), _item("a", "Epic")])
    assert creation.calls == []
    assert preview.ok and preview.order == ["a", "b"]
    assert [(e.node, e.ok) for e in preview.entries] == [("b", True), ("a", True)]
    assert [p.key for p in checker.calls[0]] == ["b", "a"]


def test_problems_of_the_backlog_are_mapped_to_their_entries_and_the_plan() -> None:
    found = [
        BacklogProblem("b", "epic_with_parent", "Epic hat Parent", {}),
        BacklogProblem("a", "value_required", "goal fehlt", {"field": "goal"}),
        BacklogProblem(None, "dependency_cycle", "Kreis", {}),
    ]
    service, _, _ = _service(_Checker(found))
    preview = service.preview("a", None, None, [_item("a"), _item("b")])
    assert not preview.ok
    by_node = {e.node: [p.code for p in e.problems] for e in preview.entries}
    assert by_node == {"a": ["goal_missing"], "b": ["parent_type_not_allowed"]}
    assert [p.code for p in preview.problems] == ["dependency_cycle"]


def test_a_transfer_with_problems_creates_nothing() -> None:
    service, _, creation = _service(_Checker([BacklogProblem("a", "value_required", "x", {"field": "goal"})]))
    with pytest.raises(DomainError) as error:
        service.transfer("a", None, None, [_item("a")])
    assert error.value.code == "transfer_blocked"
    assert error.value.details["entries"][0]["problems"][0]["code"] == "goal_missing"
    assert creation.calls == []


def test_a_transfer_creates_in_order_and_replaces_nodes_by_the_new_items() -> None:
    service, _, creation = _service()
    entries = [
        _item("c", parent="b", depends_on=("d",)),
        _item("b", "Story", parent="a"),
        _item("a", "Epic"),
        _item("d"),
    ]
    result = service.transfer("a", None, None, entries)
    created = [c[1] for c in creation.calls]
    assert created.index("a") < created.index("b") < created.index("c") and created.index("d") < created.index("c")
    c_fields = next(c[2] for c in creation.calls if c[1] == "c")
    assert c_fields["parent"] == "item-b" and c_fields["dependencies"] == ["item-d"]
    statuses = {e.node: e.status for e in result.entries}
    assert statuses == {"a": "created", "b": "created", "c": "created", "d": "created"}
    assert result.entries[0].element is not None


def test_nodes_without_an_entry_or_with_skip_are_reported_as_skipped() -> None:
    service, _, creation = _service()
    result = service.transfer("a", None, None, [_item("a"), TransferEntry(node="b", kind="skip")])
    assert {e.node: e.status for e in result.entries} == {
        "a": "created",
        "b": "skipped",
        "c": "skipped",
        "d": "skipped",
    }
    assert len(creation.calls) == 1


def test_a_memo_is_created_through_the_same_path() -> None:
    service, _, creation = _service()
    result = service.transfer("a", None, None, [TransferEntry(node="b", kind="memo", memo={"body": "B"})])
    assert creation.calls == [("memo", "b", {"summary": "Thema b", "body": "B"})]
    assert next(e for e in result.entries if e.node == "b").status == "created"


def test_a_failure_stops_only_what_depends_on_it_and_nothing_is_rolled_back() -> None:
    service, _, creation = _service(creation=_Creation(failing=("b",)))
    entries = [
        _item("a", "Epic"),
        _item("b", "Story", parent="a"),
        _item("c", parent="b"),
        _item("d", depends_on=("a",)),
    ]
    result = service.transfer("a", None, None, entries)
    statuses = {e.node: e.status for e in result.entries}
    assert statuses == {"a": "created", "b": "failed", "c": "not_attempted", "d": "created"}
    failed = next(e for e in result.entries if e.node == "b")
    assert failed.error is not None and failed.error["code"] == "backlog_broken"
    assert [c[1] for c in creation.calls] == ["a", "b", "d"]

"""Anwendungsfall: einen Ast der Mindmap ins Backlog überführen (`TASK-074`).

`preview` prüft einen Plan, ohne etwas zu schreiben; `transfer` prüft genauso und legt dann an. Die Regeln des
Backlogs prüft das Plugin `backlog` selbst (Port `BacklogChecker`), die der Mindmap stehen in `domain/transfer.py`.
Angelegt wird über `NodeCreationService`, also auf demselben Weg wie ein einzelner Knoten. Es gibt keinen Rückbau:
scheitert ein Eintrag, bleibt Angelegtes bestehen und alles, was von ihm abhängt, wird nicht versucht.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from viewer.core.domain.errors import DomainError
from viewer.plugins.mindmap.application.creation import Created
from viewer.plugins.mindmap.application.ports import BacklogChecker, BranchSource, CreatedElement
from viewer.plugins.mindmap.domain.model import MindmapViolation
from viewer.plugins.mindmap.domain.transfer import (
    KIND_MEMO,
    Draft,
    Problem,
    TransferEntry,
    map_problem,
    plan_transfer,
)

CREATED = "created"
FAILED = "failed"
SKIPPED = "skipped"
NOT_ATTEMPTED = "not_attempted"


class NodeCreator(Protocol):
    """Das, was der Überführer vom Anlegen am Knoten braucht (`NodeCreationService`)."""

    def create_item(self, node_ref: str, type_: str, fields: dict[str, Any], project_uid: str | None) -> Created: ...

    def create_memo(self, node_ref: str, fields: dict[str, Any], project_uid: str | None) -> Created: ...


@dataclass(frozen=True)
class EntryPreview:
    node: str
    problems: list[Problem]

    @property
    def ok(self) -> bool:
        return not self.problems


@dataclass(frozen=True)
class Preview:
    root_uid: str
    entries: list[EntryPreview]
    #: Probleme des ganzen Plans (z. B. Kreise).
    problems: list[Problem]
    #: Die Knoten in der Reihenfolge, in der angelegt würde.
    order: list[str]

    @property
    def ok(self) -> bool:
        return not self.problems and all(e.ok for e in self.entries)


@dataclass(frozen=True)
class EntryResult:
    node: str
    #: `created`, `failed`, `skipped` oder `not_attempted`.
    status: str
    element: CreatedElement | None = None
    #: Bei `failed`: `code`, `message` und `details` des Fehlers.
    error: dict[str, Any] | None = None


@dataclass(frozen=True)
class TransferResult:
    root_uid: str
    #: Alle Knoten des Astes (Wurzel zuerst).
    entries: list[EntryResult] = field(default_factory=list)


class BranchTransferService:
    def __init__(self, branches: BranchSource, checker: BacklogChecker, creation: NodeCreator) -> None:
        self._branches = branches
        self._checker = checker
        self._creation = creation

    def preview(
        self, root: str, project_uid: str | None, tree_uid: str | None, entries: Sequence[TransferEntry]
    ) -> Preview:
        return self._prepare(root, project_uid, tree_uid, entries)[0]

    def transfer(
        self, root: str, project_uid: str | None, tree_uid: str | None, entries: Sequence[TransferEntry]
    ) -> TransferResult:
        preview, draft, branch = self._prepare(root, project_uid, tree_uid, entries)
        if not preview.ok:
            raise MindmapViolation(
                "transfer_blocked",
                "Der Plan hat Probleme; es wurde nichts angelegt",
                entries=[
                    {"node": e.node, "problems": [vars(p) for p in e.problems]} for e in preview.entries if e.problems
                ],
                problems=[vars(p) for p in preview.problems],
            )
        project = branch[0].project_uid
        items = {i.key: i for i in draft.items}
        memos = {e.node: e for e in draft.entries if e.kind == KIND_MEMO}
        by_node = {e.node: e for e in draft.entries}
        outcome: dict[str, EntryResult] = {}
        for uid in preview.order:
            entry = by_node[uid]
            needs = [n for n in (entry.parent_node, *entry.depends_nodes) if n]
            if any(outcome[n].status != CREATED for n in needs):
                outcome[uid] = EntryResult(uid, NOT_ATTEMPTED)
                continue
            try:
                if uid in memos:
                    created = self._creation.create_memo(uid, dict(memos[uid].memo_fields or {}), project)
                else:
                    planned = items[uid]
                    fields = dict(planned.fields)
                    if entry.parent_node:
                        fields["parent"] = _created_uid(outcome[entry.parent_node])
                    if entry.depends_nodes:
                        fields["dependencies"] = [
                            *fields.get("dependencies", ()),
                            *(_created_uid(outcome[n]) for n in entry.depends_nodes),
                        ]
                    created = self._creation.create_item(uid, planned.type, fields, project)
                outcome[uid] = EntryResult(uid, CREATED, created.element)
            except DomainError as failure:
                outcome[uid] = EntryResult(
                    uid,
                    FAILED,
                    error={"code": failure.code, "message": failure.message, "details": dict(failure.details)},
                )
        return TransferResult(branch[0].uid, [outcome.get(n.uid) or EntryResult(n.uid, SKIPPED) for n in branch])

    def _prepare(
        self, root: str, project_uid: str | None, tree_uid: str | None, entries: Sequence[TransferEntry]
    ) -> tuple[Preview, Draft, list[Any]]:
        branch = self._branches.branch_of(root, project_uid, tree_uid)
        draft = plan_transfer(branch, entries)
        previews = {id(e): EntryPreview(e.node, e.problems) for e in draft.entries}
        by_node = {
            e.node: e
            for e in draft.entries
            if not any(p.code in ("node_duplicate", "node_not_in_branch") for p in e.problems)
        }
        plan_problems = list(draft.problems)
        if draft.items:
            for found in self._checker.check_new_items(branch[0].project_uid, draft.items):
                problem = Problem(map_problem(found.code, found.details), found.message, found.details)
                target = by_node.get(found.key) if found.key else None
                if target is not None:
                    target.problems.append(problem)
                else:
                    plan_problems.append(problem)
        return (
            Preview(branch[0].uid, [previews[id(e)] for e in draft.entries], plan_problems, draft.order),
            draft,
            branch,
        )


def _created_uid(result: EntryResult) -> str:
    assert result.element is not None
    return result.element.uid

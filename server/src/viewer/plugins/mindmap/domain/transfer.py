"""Einen Ast ins Backlog überführen: den Plan prüfen und ordnen (`TASK-074`), ohne Ports und Speicher.

Ein Plan nennt je Knoten des Astes, was daraus wird: ein Item (mit Typ), ein Memo oder nichts. Nichts wird aus der
Ebene oder Tiefe abgeleitet. Hier stehen die Regeln der Mindmap (Knoten im Ast, Doppelte, Memo ohne Beziehungen);
die Regeln des Backlogs prüft das Plugin `backlog` mit denselben Regeln wie beim Anlegen (Port `BacklogChecker`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from viewer.plugins.mindmap.domain.creation import item_defaults, memo_fields
from viewer.plugins.mindmap.domain.model import Node

KIND_ITEM = "item"
KIND_MEMO = "memo"
KIND_SKIP = "skip"
KINDS = (KIND_ITEM, KIND_MEMO, KIND_SKIP)
ITEM_TYPES = ("Epic", "Story", "Task")

#: Codes des Backlogs, die der Plan anders nennt.
_BACKLOG_CODES = {"epic_with_parent": "parent_type_not_allowed"}
_FIELD_CODES = {
    ("value_required", "goal"): "goal_missing",
    ("value_required", "completion_criteria"): "criteria_missing",
    ("value_required", "title"): "title_missing",
    ("invalid_input", "type"): "invalid_type",
}


@dataclass(frozen=True)
class TransferEntry:
    """Ein Eintrag des Plans. `node`: Knoten des Astes (uid oder Label); `fields`: Felder des Items (`title`, `goal`,
    `completion_criteria`, `summary`, `priority`, `required_for_parent`); `memo`: Felder des Memos; `parent` und
    `depends_on`: Knoten des Plans oder vorhandene Items (uid oder Label)."""

    node: str
    kind: str = KIND_SKIP
    type: str | None = None
    fields: Mapping[str, Any] = field(default_factory=dict)
    memo: Mapping[str, Any] = field(default_factory=dict)
    parent: str | None = None
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Problem:
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlannedItem:
    """Ein geplantes Item für die Prüfung des Backlogs: `key` ist die uid des Knotens; `parent_key` und `depends_keys`
    nennen andere Einträge des Plans, Verweise auf vorhandene Items stehen in `fields`."""

    key: str
    type: str
    fields: Mapping[str, Any]
    parent_key: str | None = None
    depends_keys: tuple[str, ...] = ()


@dataclass
class DraftEntry:
    #: Die uid des Knotens; bei einem Knoten außerhalb des Astes der Wert aus dem Plan.
    node: str
    kind: str
    problems: list[Problem] = field(default_factory=list)
    #: Nur bei Memos: die Felder des neuen Memos.
    memo_fields: dict[str, Any] | None = None
    #: Nur bei Items: Parent und Abhängigkeiten als uid der Knoten des Plans.
    parent_node: str | None = None
    depends_nodes: tuple[str, ...] = ()
    #: Nur bei Items: Verweise auf vorhandene Items (uid oder Label).
    item_parent: str | None = None
    item_dependencies: tuple[str, ...] = ()


@dataclass
class Draft:
    entries: list[DraftEntry]
    #: Die Items, die das Backlog prüft (nur Einträge ohne Mangel der Mindmap).
    items: list[PlannedItem]
    #: Die Knoten, die angelegt würden, Parents und Abhängigkeiten vor ihren Nachfolgern.
    order: list[str]
    problems: list[Problem] = field(default_factory=list)


def map_problem(code: str, details: Mapping[str, Any]) -> str:
    """Der Code im Plan für eine Verletzung des Backlogs."""
    return _FIELD_CODES.get((code, str(details.get("field")))) or _BACKLOG_CODES.get(code, code)


def plan_transfer(branch: Sequence[Node], entries: Sequence[TransferEntry]) -> Draft:
    """Prüft die Regeln der Mindmap und bereitet die Prüfung des Backlogs vor. `branch` ist der Ast (Wurzel zuerst)."""
    by_ref = {ref: node for node in branch for ref in (node.uid, node.label)}
    draft = Draft([], [], [])
    seen: set[str] = set()
    resolved: list[tuple[TransferEntry, DraftEntry, Node | None]] = []
    for entry in entries:
        node = by_ref.get(entry.node)
        result = DraftEntry(node.uid if node else entry.node, entry.kind)
        draft.entries.append(result)
        resolved.append((entry, result, node))
        if node is None:
            result.problems.append(
                Problem("node_not_in_branch", f"{entry.node} gehört nicht zum Ast", {"node": entry.node})
            )
        elif node.uid in seen:
            result.problems.append(
                Problem("node_duplicate", f"{node.label} steht mehrmals im Plan", {"node": node.uid})
            )
        else:
            seen.add(node.uid)
            result.node = node.uid
        if entry.kind not in KINDS:
            result.problems.append(Problem("invalid_kind", f"Unbekannte Art '{entry.kind}'", {"allowed": list(KINDS)}))
    kind_of = {r.node: r.kind for _, r, n in resolved if n is not None and r.kind in KINDS and not r.problems}
    kind_of.update({r.node: r.kind for _, r, n in resolved if n is not None and r.kind in KINDS})
    for entry, result, node in resolved:
        if node is None or any(p.code == "node_duplicate" for p in result.problems):
            continue
        if entry.kind == KIND_ITEM:
            _plan_item(draft, entry, result, node, by_ref, kind_of)
        elif entry.kind == KIND_MEMO:
            _plan_memo(entry, result, node)
    _order(draft)
    return draft


def _plan_memo(entry: TransferEntry, result: DraftEntry, node: Node) -> None:
    if entry.parent or entry.depends_on:
        result.problems.append(Problem("memo_with_relation", "Ein Memo hat weder Parent noch Abhängigkeiten"))
    result.memo_fields = memo_fields(node, entry.memo)


def _plan_item(
    draft: Draft,
    entry: TransferEntry,
    result: DraftEntry,
    node: Node,
    by_ref: Mapping[str, Node],
    kind_of: Mapping[str, str],
) -> None:
    if entry.type not in ITEM_TYPES:
        result.problems.append(
            Problem("invalid_type", f"Unbekannter Typ '{entry.type}'", {"field": "type", "allowed": list(ITEM_TYPES)})
        )
        return
    fields = item_defaults(node, entry.fields)
    parent_key, depends = _relation(result, entry.parent, "parent", by_ref, kind_of)
    keys: list[str] = []
    existing: list[str] = []
    for ref in entry.depends_on:
        key, other = _relation(result, ref, "depends_on", by_ref, kind_of)
        if key:
            keys.append(key)
        elif other:
            existing.append(other)
    if parent_key is None and depends is not None:
        fields["parent"] = depends
    if existing:
        fields["dependencies"] = existing
    if (parent_key or depends) and "required_for_parent" not in fields:
        fields["required_for_parent"] = True
    result.parent_node = parent_key
    result.depends_nodes = tuple(keys)
    result.item_parent = depends
    result.item_dependencies = tuple(existing)
    if not result.problems:
        draft.items.append(PlannedItem(node.uid, entry.type, fields, parent_key, tuple(keys)))


def _relation(
    result: DraftEntry, ref: str | None, role: str, by_ref: Mapping[str, Node], kind_of: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """(Knoten des Plans, vorhandenes Item): höchstens eines davon ist gesetzt."""
    if not ref:
        return None, None
    node = by_ref.get(ref)
    if node is None:
        return None, ref
    kind = kind_of.get(node.uid)
    if kind == KIND_MEMO:
        result.problems.append(
            Problem(
                f"{role}_is_memo", f"{node.label} wird ein Memo und kann kein Ziel von {role} sein", {"node": node.uid}
            )
        )
        return None, None
    if kind != KIND_ITEM:
        code = "parent_not_found" if role == "parent" else "depends_on_not_found"
        result.problems.append(Problem(code, f"{node.label} wird im Plan nicht angelegt", {"node": node.uid}))
        return None, None
    return node.uid, None


def _order(draft: Draft) -> None:
    """Parents und Abhängigkeiten vor ihre Nachfolger, sonst in der Reihenfolge des Plans (ein Kreis bleibt am Ende
    und wird vom Backlog gemeldet)."""
    wanted = {i.key: {k for k in (i.parent_key, *i.depends_keys) if k} for i in draft.items}
    pending = [
        e.node
        for e in draft.entries
        if (e.kind == KIND_ITEM and e.node in wanted) or (e.kind == KIND_MEMO and e.memo_fields is not None)
    ]
    done: set[str] = set()
    while pending:
        ready = next((n for n in pending if wanted.get(n, set()) <= done), pending[0])
        pending.remove(ready)
        done.add(ready)
        draft.order.append(ready)

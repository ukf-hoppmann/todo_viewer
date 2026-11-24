"""Baumliste einer Datei → Platzierungen: dieselben Regeln wie in der API, ohne Datenbank (reine Funktionen)."""

from __future__ import annotations

from collections.abc import Collection, Sequence

from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.model import MindmapViolation, Placement, RemovedPlacement


def placements_from_listing(tree_uid: str, nodes: Sequence[str], depths: Sequence[int]) -> list[Placement]:
    """Die Platzierungen aus einer Liste in Tiefensuche (Knoten und Einrückungstiefe): Parent ist der nächste Knoten
    mit kleinerer Tiefe, die Stelle zählt unter den Geschwistern. Ein Knoten steht höchstens einmal."""
    result: list[Placement] = []
    stack: list[str] = []
    count: dict[str | None, int] = {}
    seen: set[str] = set()
    for node, depth in zip(nodes, depths, strict=True):
        if node in seen:
            raise MindmapViolation("mindmap_node_in_tree", "Der Knoten steht schon in diesem Baum", node=node)
        if depth > len(stack):
            raise MindmapViolation("mindmap_parent_missing", "Der Parent-Knoten steht nicht in diesem Baum", node=node)
        del stack[depth:]
        parent = stack[-1] if stack else None
        result.append(Placement(tree_uid, node, parent, count.get(parent, 0)))
        count[parent] = count.get(parent, 0) + 1
        stack.append(node)
        seen.add(node)
    return result


def changed_placements(stored: Sequence[Placement], wanted: Sequence[Placement]) -> list[Placement]:
    """Die Platzierungen, die geschrieben werden müssen, damit der Baum der Liste folgt.

    Eine Geschwistergruppe (je Parent der Liste) wird nur angefasst, wenn sich ihre Mitglieder oder deren Reihenfolge
    ändern; Lücken in den gespeicherten Stellen allein sind kein Unterschied. Knoten, die die Liste nicht nennt,
    behalten ihren Parent und stehen hinter den genannten Geschwistern; `Removed:` regelt `changed_removed`."""
    listed = {p.node_uid for p in wanted}
    result: list[Placement] = []
    for parent in dict.fromkeys(p.parent_uid for p in wanted):
        order = [p.node_uid for p in wanted if p.parent_uid == parent]
        order += [p.node_uid for p in rules.children_of(stored, parent) if p.node_uid not in listed]
        if order == [p.node_uid for p in rules.children_of(stored, parent)]:
            continue
        for position, node in enumerate(order):
            now = Placement(wanted[0].tree_uid, node, parent, position)
            if rules.find(stored, node) != now:
                result.append(now)
    return result


def changed_removed(
    stored: Sequence[RemovedPlacement], wanted: Sequence[RemovedPlacement], listed: Collection[str]
) -> tuple[list[RemovedPlacement], list[RemovedPlacement]]:
    """Was mit den entfernten Platzierungen eines Baums geschieht, damit er `Removed:` der Datei folgt: (zu merken, zu
    vergessen). Gemerkt wird, was neu oder anders ist. Vergessen wird, was die Datei nicht mehr nennt, solange der
    Knoten nicht in der Liste des Baums steht (dann holt ihn das Schreiben der Platzierung zurück)."""
    known = {r.node_uid: r for r in stored}
    named = {r.node_uid for r in wanted}
    mark = [r for r in wanted if known.get(r.node_uid) != r]
    forget = [r for r in stored if r.node_uid not in named and r.node_uid not in listed]
    return mark, forget


def check_no_children_of_removed(live: Sequence[Placement], removed: Collection[str]) -> None:
    """Ein entfernter Knoten hat keine Kinder mehr im Baum: sie müssten unter ihm stehen, den es dort nicht gibt."""
    for placement in live:
        if placement.parent_uid in removed:
            raise MindmapViolation(
                "mindmap_parent_removed",
                "Der Parent steht unter Removed:, der Knoten aber noch im Baum (er gehört mit unter Removed:)",
                node=placement.node_uid,
                parent=placement.parent_uid,
            )

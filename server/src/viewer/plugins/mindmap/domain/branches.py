"""Äste zwischen Bäumen (`TASK-063`): Umhängen, Übertragen, Entfernen und Löschen als reine Rechnung.

Ein Ast ist ein Knoten mit seinen Unterknoten in einem Baum. Die Funktionen bekommen die Platzierungen und die `uid`s
der lebenden Knoten und geben zurück, was zu ändern ist; gelesen und gespeichert wird im Dienst.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field

from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.model import MindmapViolation, Placement


def branch_uids(placements: Sequence[Placement], node_uid: str, live: Collection[str] | None = None) -> list[str]:
    """Der Knoten und seine Nachkommen in diesem Baum, Eltern vor Kindern. Mit `live` steigt man nur durch lebende
    Knoten (ein Knoten im Papierkorb nimmt seine Unterknoten mit)."""
    found = [node_uid]
    queue = [node_uid]
    while queue:
        current = queue.pop(0)
        for child in rules.children_of(placements, current):
            if live is not None and child.node_uid not in live:
                continue
            if child.node_uid in found:
                raise MindmapViolation("mindmap_loop", "Die Knoten bilden einen Kreis", node=child.node_uid)
            found.append(child.node_uid)
            queue.append(child.node_uid)
    return found


def check_target_free(target: Sequence[Placement], branch: Sequence[str], live: Collection[str]) -> None:
    """Das Ziel darf keinen lebenden Knoten des Asts schon enthalten; die Meldung nennt alle, die dort stehen."""
    standing = [uid for uid in branch if uid in live and rules.find(target, uid) is not None]
    if standing:
        raise MindmapViolation(
            "mindmap_target_conflict",
            "Der Ast oder ein Unterknoten steht im Ziel schon",
            nodes=standing,
        )


def graft(
    source: Sequence[Placement], root_uid: str, branch: Sequence[str], target_tree: str, target: Sequence[Placement]
) -> list[Placement]:
    """Die Platzierungen des Asts im Ziel: die Wurzel des Asts steht am Ende unter der Wurzel des Ziels, darunter bleibt
    die Reihenfolge der Quelle (lückenlos nummeriert)."""
    members = set(branch)
    ends = [p.position for p in target if p.parent_uid is None]
    made = [Placement(target_tree, root_uid, None, max(ends) + 1 if ends else 0)]
    for parent in branch:
        children = [p for p in rules.children_of(source, parent) if p.node_uid in members and p.node_uid != root_uid]
        for position, child in enumerate(children):
            made.append(Placement(target_tree, child.node_uid, parent, position))
    return made


@dataclass(frozen=True)
class Cut:
    """Was der Schnitt eines Asts ändert."""

    #: Platzierungen, die gelöscht werden (der Knoten bleibt anderswo stehen).
    removed: list[Placement] = field(default_factory=list)
    #: Platzierungen heimatloser Knoten, die an einen anderen Parent wandern, weil ihr alter Parent geht.
    reparented: list[Placement] = field(default_factory=list)
    #: Knoten des Asts ohne Platzierung außerhalb des Schnitts, ohne Wiederholung. Wer lebt, kommt in den Papierkorb;
    #: seine Platzierung bleibt, damit er zurückkommen kann.
    homeless: list[str] = field(default_factory=list)


def plan_cuts(
    trees: Mapping[str, Sequence[Placement]], root_uid: str, live_trees_of: Mapping[str, Collection[str]]
) -> Cut:
    """Schneidet den Ast von `root_uid` aus jedem der `trees` (Platzierungen je Baum).

    `live_trees_of` nennt für jeden Knoten die Bäume außerhalb des Papierkorbs, in denen er steht. Ein Knoten des
    Asts, der in einem Baum steht, aus dem nicht geschnitten wird, oder außerhalb des Asts, bleibt dort (seine
    Platzierung im Schnitt wird gelöscht). Alle anderen sind heimatlos."""
    cut_branches = {tree_uid: branch_uids(placements, root_uid) for tree_uid, placements in trees.items()}
    cut_set = {(tree_uid, uid) for tree_uid, branch in cut_branches.items() for uid in branch}

    def elsewhere(uid: str) -> bool:
        return any((tree_uid, uid) not in cut_set for tree_uid in live_trees_of.get(uid, ()))

    removed: list[Placement] = []
    reparented: list[Placement] = []
    homeless: list[str] = []
    for tree_uid, placements in trees.items():
        branch = cut_branches[tree_uid]
        gone = {uid for uid in branch if elsewhere(uid)}
        by_node = {p.node_uid: p for p in placements}
        removed.extend(by_node[uid] for uid in branch if uid in gone)
        for uid in branch:
            if uid not in homeless and uid not in gone:
                homeless.append(uid)
        next_free: dict[str | None, int] = {}
        for uid in branch:
            if uid in gone:
                continue
            placement = by_node[uid]
            parent = placement.parent_uid
            while parent is not None and parent in gone:
                parent = by_node[parent].parent_uid
            if parent == placement.parent_uid:
                continue
            if parent not in next_free:
                siblings = [p.position for p in placements if p.parent_uid == parent]
                next_free[parent] = max(siblings) + 1 if siblings else 0
            reparented.append(Placement(tree_uid, uid, parent, next_free[parent]))
            next_free[parent] += 1
    return Cut(removed, reparented, homeless)

"""Äste zwischen Bäumen (`TASK-063`): Umhängen, Übertragen, Entfernen und Löschen als reine Rechnung.

Ein Ast ist ein Knoten mit seinen Unterknoten in einem Baum. Die Funktionen bekommen die Platzierungen und die `uid`s
der lebenden Knoten und geben zurück, was zu ändern ist; gelesen und gespeichert wird im Dienst.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field

from viewer.plugins.mindmap.domain import tree as rules
from viewer.plugins.mindmap.domain.model import MindmapViolation, Placement, RemovedPlacement


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


@dataclass(frozen=True)
class Restoration:
    """Was das Wiedereinsetzen eines entfernten Asts ändert (`TASK-066`)."""

    #: Neue und verschobene Platzierungen: der Ast und die Geschwister, die nachrücken.
    placements: list[Placement]
    #: Die Knoten, die wieder im Baum stehen: der Knoten und seine Nachkommen aus der entfernten Gruppe.
    restored: list[str]
    #: Mitglieder der Gruppe im Papierkorb samt ihrem Teilbaum; sie bleiben als entfernt gemerkt.
    skipped: list[str]
    #: Der Parent, unter dem der Knoten jetzt steht; `None` unter der Wurzel.
    parent_uid: str | None
    #: Der alte Parent fehlt (nicht mehr im Baum, im Papierkorb oder selbst noch entfernt): der Ast steht unter der
    #: Wurzel der Map (Ersatzregel).
    fell_back: bool


def plan_restore(
    removed: Sequence[RemovedPlacement], node_uid: str, placements: Sequence[Placement], alive: Collection[str]
) -> Restoration:
    """Setzt den entfernten Ast von `node_uid` wieder ein: an den alten Parent und die alte Stelle, mit den
    Unterknoten, die mit ihm entfernt wurden.

    `removed` sind die gemerkten Platzierungen des Baums (der Gruppe des Knotens), `placements` die heutigen, `alive`
    die Knoten außerhalb des Papierkorbs. Fehlt der alte Parent, steht der Ast unter der Wurzel (Ersatzregel). Eine alte
    Stelle ist nie „belegt“: die Geschwister rücken nach. Steht der Knoten im Baum schon wieder, wird abgelehnt."""
    if rules.find(placements, node_uid) is not None:
        raise MindmapViolation("mindmap_node_in_tree", "Der Knoten steht in diesem Baum schon wieder", node=node_uid)
    own = next((r for r in removed if r.node_uid == node_uid), None)
    if own is None:
        raise MindmapViolation(
            "mindmap_nothing_to_restore",
            "Für diesen Knoten ist in diesem Baum keine Platzierung gemerkt",
            node=node_uid,
        )
    group = [r for r in removed if r.root_uid == own.root_uid]
    by_parent: dict[str | None, list[RemovedPlacement]] = {}
    for entry in group:
        by_parent.setdefault(entry.parent_uid, []).append(entry)
    restored = [node_uid]
    skipped: list[str] = []
    queue = [node_uid]
    while queue:
        current = queue.pop(0)
        for child in sorted(by_parent.get(current, ()), key=lambda r: (r.position, r.node_uid)):
            if child.node_uid in restored or child.node_uid in skipped:
                continue
            if child.node_uid in alive:
                restored.append(child.node_uid)
                queue.append(child.node_uid)
            else:
                skipped.append(child.node_uid)
                skipped.extend(_removed_below(by_parent, child.node_uid, restored, skipped))
    live = {p.node_uid for p in placements if p.node_uid in alive}
    fell_back = own.parent_uid is not None and own.parent_uid not in live
    parent = None if fell_back else own.parent_uid
    made = rules.arrange(placements, own.tree_uid, node_uid, parent, own.position, live | {node_uid})
    members = set(restored)
    for owner in restored:
        below = [
            r for r in sorted(by_parent.get(owner, ()), key=lambda r: (r.position, r.node_uid)) if r.node_uid in members
        ]
        made.extend(Placement(own.tree_uid, r.node_uid, owner, index) for index, r in enumerate(below))
    return Restoration(made, restored, skipped, parent, fell_back)


def _removed_below(
    by_parent: Mapping[str | None, Sequence[RemovedPlacement]],
    uid: str,
    restored: Sequence[str],
    skipped: Sequence[str],
) -> list[str]:
    """Die gemerkten Nachkommen eines Knotens im Papierkorb."""
    found: list[str] = []
    queue = [uid]
    while queue:
        for child in by_parent.get(queue.pop(0), ()):
            if child.node_uid not in restored and child.node_uid not in skipped and child.node_uid not in found:
                found.append(child.node_uid)
                queue.append(child.node_uid)
    return found

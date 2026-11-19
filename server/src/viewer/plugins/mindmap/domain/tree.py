"""Die reinen Regeln eines Baums: Platzierungen prüfen und ordnen.

Die Funktionen bekommen die Platzierungen eines Baums und die `uid`s der lebenden Knoten (nicht im Papierkorb) und
geben neue Platzierungen zurück; gespeichert wird im Dienst. Vorbild für die Kreisprüfung ist `topic_loop` in
`plugins/memos/domain/topics.py`.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence

from viewer.plugins.mindmap.domain.model import (
    MAP_NAME_MAX,
    NODE_MARKS,
    TREE_PROJECT,
    MindmapViolation,
    Placement,
    Tree,
)


def children_of(placements: Sequence[Placement], parent_uid: str | None) -> list[Placement]:
    """Die Platzierungen unter `parent_uid` nach Stelle (bei gleicher Stelle nach Knoten)."""
    return sorted((p for p in placements if p.parent_uid == parent_uid), key=lambda p: (p.position, p.node_uid))


def find(placements: Sequence[Placement], node_uid: str) -> Placement | None:
    return next((p for p in placements if p.node_uid == node_uid), None)


def descendants(placements: Sequence[Placement], node_uid: str) -> list[str]:
    """Alle Nachkommen des Knotens, Eltern vor Kindern. Ein Kreis in den Daten wird gemeldet, nicht verfolgt."""
    found: list[str] = []
    seen = {node_uid}
    queue = [node_uid]
    while queue:
        current = queue.pop(0)
        for child in children_of(placements, current):
            if child.node_uid in seen:
                raise MindmapViolation("mindmap_loop", "Die Knoten bilden einen Kreis", node=child.node_uid)
            seen.add(child.node_uid)
            found.append(child.node_uid)
            queue.append(child.node_uid)
    return found


def check_parent(placements: Sequence[Placement], parent_uid: str | None, live: Collection[str]) -> None:
    """Der Parent ist `None` (unter der Wurzel) oder ein lebender Knoten des Baums."""
    if parent_uid is not None and (parent_uid not in live or find(placements, parent_uid) is None):
        raise MindmapViolation(
            "mindmap_parent_missing", "Der Parent-Knoten steht nicht in diesem Baum", parent=parent_uid
        )


def check_new(placements: Sequence[Placement], node_uid: str, parent_uid: str | None, live: Collection[str]) -> None:
    """Darf der Knoten neu in den Baum? Höchstens einmal je Baum."""
    if find(placements, node_uid) is not None:
        raise MindmapViolation("mindmap_node_in_tree", "Der Knoten steht schon in diesem Baum", node=node_uid)
    check_parent(placements, parent_uid, live)


def check_move(placements: Sequence[Placement], node_uid: str, parent_uid: str | None, live: Collection[str]) -> None:
    """Darf der Knoten samt Ast unter `parent_uid`? Nicht unter sich selbst oder einen Nachkommen."""
    if find(placements, node_uid) is None:
        raise MindmapViolation("mindmap_node_not_in_tree", "Der Knoten steht nicht in diesem Baum", node=node_uid)
    check_parent(placements, parent_uid, live)
    if parent_uid is not None and (parent_uid == node_uid or parent_uid in descendants(placements, node_uid)):
        raise MindmapViolation(
            "mindmap_loop", "Ein Knoten lässt sich nicht unter sich selbst oder seine Nachkommen hängen", node=node_uid
        )


def check_project(tree_project_uid: str, node_project_uid: str) -> None:
    """Ein Baum gehört zu einem Projekt; seine Knoten gehören zu demselben."""
    if tree_project_uid != node_project_uid:
        raise MindmapViolation("mindmap_other_project", "Der Knoten gehört zu einem anderen Projekt als der Baum")


def check_tree_free(project_uids_with_tree: Collection[str], project_uid: str) -> None:
    """Je Projekt gibt es einen Projektbaum."""
    if project_uid in project_uids_with_tree:
        raise MindmapViolation("mindmap_tree_exists", "Das Projekt hat schon einen Baum", project=project_uid)


def arrange(
    placements: Sequence[Placement],
    tree_uid: str,
    node_uid: str,
    parent_uid: str | None,
    index: int | None,
    live: Collection[str],
) -> list[Placement]:
    """Stellt den Knoten (neu oder vorhanden) unter `parent_uid` an die Stelle `index` unter den lebenden
    Geschwistern (`None` oder zu groß: ans Ende) und nummeriert die betroffenen Geschwister neu. Gibt nur die
    Platzierungen zurück, die sich ändern. Geschwister im Papierkorb behalten ihre Stelle."""
    if index is not None and index < 0:
        raise MindmapViolation("mindmap_position_invalid", "Die Stelle darf nicht negativ sein", position=index)
    old = find(placements, node_uid)
    result: dict[str, Placement] = {}

    def renumber(parent: str | None, extra: str | None = None) -> None:
        siblings = [
            p.node_uid for p in children_of(placements, parent) if p.node_uid in live and p.node_uid != node_uid
        ]
        if extra is not None:
            at = len(siblings) if index is None else min(index, len(siblings))
            siblings.insert(at, extra)
        for position, uid in enumerate(siblings):
            current = old if uid == node_uid else find(placements, uid)
            wanted = Placement(tree_uid, uid, parent, position)
            if current != wanted:
                result[uid] = wanted

    if old is not None and old.parent_uid != parent_uid:
        renumber(old.parent_uid)
    renumber(parent_uid, node_uid)
    return list(result.values())


def apply(placements: Sequence[Placement], changed: Sequence[Placement]) -> list[Placement]:
    """Die Platzierungen mit den geänderten (nach Knoten ersetzt oder ergänzt)."""
    by_node = {p.node_uid: p for p in placements}
    by_node.update({p.node_uid: p for p in changed})
    return list(by_node.values())


def compacted(placements: Sequence[Placement], live: Collection[str]) -> list[Placement]:
    """Die Platzierungen der lebenden Knoten mit lückenlosen Stellen (ab 0 je Parent). So sieht ein Leser die Stelle
    unter den sichtbaren Geschwistern, auch wenn Geschwister im Papierkorb liegen."""
    visible = [p for p in placements if p.node_uid in live]
    result: list[Placement] = []
    for parent in dict.fromkeys(p.parent_uid for p in visible):
        for position, p in enumerate(children_of(visible, parent)):
            result.append(Placement(p.tree_uid, p.node_uid, p.parent_uid, position))
    return result


def check_mark(value: str | None) -> str | None:
    """Die Markierung eines Knotens: einer der festen Werte, oder leer für „keine“ (dann `None`)."""
    if value is None or value == "":
        return None
    if value not in NODE_MARKS:
        raise MindmapViolation(
            "mindmap_mark_invalid",
            f"Unbekannte Markierung '{value}'",
            field="mark",
            allowed=list(NODE_MARKS),
        )
    return value


def clean_map_name(value: object) -> str:
    """Der Name einer freien Map ist eine Zeile ohne überflüssige Leerzeichen, nicht leer und nicht zu lang."""
    cleaned = " ".join(value.split()) if isinstance(value, str) else ""
    if not cleaned:
        raise MindmapViolation("mindmap_map_name_missing", "Der Name der Map fehlt", field="name")
    if len(cleaned) > MAP_NAME_MAX:
        raise MindmapViolation(
            "mindmap_map_name_too_long", f"Der Name darf höchstens {MAP_NAME_MAX} Zeichen haben", field="name"
        )
    return cleaned


def check_map_name_free(name: str, taken: Collection[str]) -> None:
    """Die freien Maps eines Projekts heißen verschieden (Groß- und Kleinschreibung zählt nicht)."""
    if name.casefold() in {t.casefold() for t in taken}:
        raise MindmapViolation(
            "mindmap_map_name_taken", f"Es gibt in diesem Projekt schon eine Map '{name}'", name=name
        )


def check_renamable(tree: Tree) -> None:
    if tree.kind == TREE_PROJECT:
        raise MindmapViolation(
            "mindmap_project_tree_fixed", "Der Projektbaum heißt wie das Projekt und lässt sich nicht umbenennen"
        )


def check_deletable(tree: Tree) -> None:
    if tree.kind == TREE_PROJECT:
        raise MindmapViolation("mindmap_project_tree_fixed", "Der Projektbaum lässt sich nicht löschen")

"""Items an Knoten hängen: wirksamer Knoten, Summen ohne Doppelzählung und Zustand (reine Funktionen).

Regeln: `docs/todo/items/STORY-100/STORY-100_spec.md`. Die Funktionen bekommen Tatsachen (Items, Zuordnungen, Knoten
und deren Eltern) und rechnen; gelesen und gespeichert wird im Dienst. Nichts davon wird gespeichert: der wirksame
Knoten ergibt sich bei jeder Abfrage neu, darum stellt das Wiederherstellen eines Knotens die Zuordnung von selbst
wieder her.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass

from viewer.plugins.mindmap.domain.model import MindmapViolation

STATE_IDEA = "idea"
STATE_PLANNED = "planned"
STATE_ACTIVE = "in_progress"
STATE_DONE = "done"
STATES = (STATE_IDEA, STATE_PLANNED, STATE_ACTIVE, STATE_DONE)

#: Das Backlog kennt fünf Status; hier werden nur diese drei unterschieden.
_OPEN = "Open"
_COMPLETED = "Completed"
_REJECTED = "Rejected"


@dataclass(frozen=True)
class ItemFact:
    """Was die Zuordnung von einem Item wissen muss."""

    uid: str
    parent_uid: str | None
    status: str
    deleted: bool = False
    #: Die `uid`s der Items, die dieses Item braucht.
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class NodeStats:
    """Zahlen eines Knotens über sich und seine Unterknoten. `total` ist die Zahl der zählenden Items (Statusfilter),
    `done` davon die erledigten; der Zustand hängt vom Filter nicht ab."""

    total: int
    done: int
    state: str


@dataclass(frozen=True)
class Overview:
    """Das Ergebnis für einen Baum."""

    #: Knoten → Zahlen, für jeden lebenden Knoten.
    stats: dict[str, NodeStats]
    #: Item → wirksamer Knoten (nur Items mit Knoten, gelöschte nicht).
    effective: dict[str, str]
    #: Items ohne Knoten, die der Statusfilter durchlässt (nicht gelöscht), nach `uid`.
    unassigned: list[str]


def live_ancestor(node_uid: str, live: Collection[str], parent_of: Mapping[str, str | None]) -> str | None:
    """Der Knoten selbst, wenn er lebt, sonst sein nächster lebender Vorfahre; `None`, wenn es keinen gibt. Ein Kreis
    in den Daten bricht ab."""
    seen: set[str] = set()
    current: str | None = node_uid
    while current is not None and current not in live:
        if current in seen:
            return None
        seen.add(current)
        current = parent_of.get(current)
    return current


def subtree_nodes(node_uid: str, live: Collection[str], parent_of: Mapping[str, str | None]) -> set[str]:
    """Der Knoten und alle lebenden Unterknoten; ein Knoten im Papierkorb reicht seine Kinder an den nächsten
    lebenden Vorfahren weiter (wie bei den Summen). Ein Kreis in den Daten bricht ab."""
    found = {node_uid}
    for uid in live:
        seen = {uid}
        above = parent_of.get(uid)
        current = live_ancestor(above, live, parent_of) if above else None
        while current is not None and current not in seen:
            if current == node_uid:
                found.add(uid)
                break
            seen.add(current)
            above = parent_of.get(current)
            current = live_ancestor(above, live, parent_of) if above else None
    return found


def effective_nodes(
    items: Sequence[ItemFact],
    assigned: Mapping[str, str],
    live: Collection[str],
    parent_of: Mapping[str, str | None],
) -> dict[str, str | None]:
    """Der wirksame Knoten jedes Items: der eigens zugeordnete, sonst der des Item-Parents. Liegt der zugeordnete
    Knoten im Papierkorb, gilt sein nächster lebender Vorfahre; gibt es keinen, ist das Ergebnis, als wäre die
    Zuordnung nie da gewesen (der Knoten des Item-Parents oder keiner). `None` heißt „Nicht zugeordnet“."""
    by_uid = {item.uid: item for item in items}
    result: dict[str, str | None] = {}

    def resolve(uid: str, trail: frozenset[str]) -> str | None:
        if uid in result:
            return result[uid]
        item = by_uid[uid]
        node: str | None = None
        if uid in assigned:
            node = live_ancestor(assigned[uid], live, parent_of)
        if node is None and item.parent_uid in by_uid and item.parent_uid not in trail:
            node = resolve(str(item.parent_uid), trail | {uid})
        result[uid] = node
        return node

    for item in items:
        resolve(item.uid, frozenset({item.uid}))
    return result


def state_of(statuses: Iterable[str]) -> str:
    """Der Zustand aus den Status der Items samt Unterknoten (ohne gelöschte): `Rejected` zählt nicht."""
    counted = [status for status in statuses if status != _REJECTED]
    if not counted:
        return STATE_IDEA
    if all(status == _OPEN for status in counted):
        return STATE_PLANNED
    if all(status == _COMPLETED for status in counted):
        return STATE_DONE
    return STATE_ACTIVE


def overview(
    items: Sequence[ItemFact],
    assigned: Mapping[str, str],
    live: Collection[str],
    parent_of: Mapping[str, str | None],
    statuses: Collection[str] = (),
) -> Overview:
    """Zahlen je Knoten und die Items ohne Knoten.

    `live` sind die lebenden Knoten des Baums, `parent_of` der Parent jedes Knotens des Baums (gelöschte
    eingeschlossen, `None` unter der Wurzel). Zählende Items: nicht gelöscht und vom Statusfilter durchgelassen
    (`statuses` leer: alle). Jedes Item zählt genau einmal, bei seinem wirksamen Knoten; die Summen laufen über
    Unterknoten, auch über leere. Der Zustand nimmt alle nicht gelöschten Items, unabhängig vom Filter."""
    effective = effective_nodes(items, assigned, live, parent_of)
    own: dict[str, list[ItemFact]] = {uid: [] for uid in live}
    unassigned: list[str] = []
    for item in items:
        if item.deleted:
            continue
        node = effective[item.uid]
        if node is None:
            if not statuses or item.status in statuses:
                unassigned.append(item.uid)
            continue
        own.setdefault(node, []).append(item)

    children: dict[str, list[str]] = {uid: [] for uid in live}
    for uid in live:
        above = parent_of.get(uid)
        parent = live_ancestor(above, live, parent_of) if above else None
        if parent is not None and parent != uid:
            children[parent].append(uid)

    subtree: dict[str, dict[str, ItemFact]] = {}

    def collect(uid: str, trail: frozenset[str]) -> dict[str, ItemFact]:
        known = subtree.get(uid)
        if known is not None:
            return known
        found = {item.uid: item for item in own.get(uid, [])}
        for child in children.get(uid, []):
            if child not in trail:  # ein Kreis in den Daten hält die Rechnung nicht auf
                found.update(collect(child, trail | {child}))
        subtree[uid] = found
        return found

    stats: dict[str, NodeStats] = {}
    for uid in sorted(live):
        found = list(collect(uid, frozenset({uid})).values())
        counting = [item for item in found if not statuses or item.status in statuses]
        stats[uid] = NodeStats(
            total=len(counting),
            done=sum(1 for item in counting if item.status == _COMPLETED),
            state=state_of(item.status for item in found),
        )
    return Overview(
        stats,
        {item.uid: node for item in items if not item.deleted and (node := effective[item.uid]) is not None},
        sorted(unassigned),
    )


@dataclass(frozen=True)
class LinkFact:
    """Eine Linie zwischen zwei Knoten: `count` Items von `to_node` brauchen Items von `from_node` (je Abhängigkeit
    eins)."""

    from_node: str
    to_node: str
    count: int


def dependency_links(
    items: Sequence[ItemFact], effective: Mapping[str, str], statuses: Collection[str] = ()
) -> list[LinkFact]:
    """Die Abhängigkeiten der Items, je Knotenpaar zusammengefasst.

    Linie vom Knoten des benötigten Items zum Knoten des abhängigen. `effective` ist der wirksame Knoten je Item
    (`Overview.effective`: nur Items mit Knoten, ohne gelöschte). Es zählen nur Abhängigkeiten, deren beide Enden
    ein solches Item sind und den Statusfilter passieren (`statuses` leer: alle); Abhängigkeiten auf Items außerhalb
    des Projekts und Paare im selben Knoten fallen weg. Sortiert nach (von, nach)."""
    by_uid = {item.uid: item for item in items}
    counts: dict[tuple[str, str], int] = {}
    for item in items:
        target = effective.get(item.uid)
        if item.deleted or target is None or (statuses and item.status not in statuses):
            continue
        for needed_uid in item.dependencies:
            needed = by_uid.get(needed_uid)
            source = effective.get(needed_uid)
            if needed is None or needed.deleted or source is None or source == target:
                continue
            if statuses and needed.status not in statuses:
                continue
            counts[(source, target)] = counts.get((source, target), 0) + 1
    return [LinkFact(a, b, n) for (a, b), n in sorted(counts.items())]


def check_assign(current_nodes: Collection[str], node_uid: str, replace: bool) -> list[str]:
    """Darf das Item an `node_uid`? Es hängt an höchstens einem Knoten. Gibt die Knoten zurück, deren Zuordnung zu
    lösen ist (leer, wenn es schon an `node_uid` hängt oder noch an keinem). Ein anderer Knoten wird abgewiesen,
    außer `replace` ist gesetzt."""
    others = sorted(uid for uid in current_nodes if uid != node_uid)
    if others and not replace:
        raise MindmapViolation(
            "mindmap_item_assigned",
            "Das Item hängt schon an einem anderen Knoten; zum Ersetzen replace angeben",
            node=others[0],
        )
    return others

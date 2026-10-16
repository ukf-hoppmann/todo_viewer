"""Lebenszyklus- und Strukturregeln des Backlog-Formats, über alle Items eines Projekts geprüft.

Eine Änderung wird nur abgewiesen, wenn sie eine Verletzung einführt oder erweitert; Verletzungen, die schon da
waren, blockieren andere Änderungen nicht. Verweise gehen über die `uid`; für die Meldungen stehen die Labels.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from viewer.core.domain.errors import DomainError
from viewer.plugins.backlog.domain.model import FINAL_STATUSES, Item

EPIC = "Epic"
#: Ein Epic verlässt `Open` nur in diesen Status mit einem Pflichtkind (`Rejected` geht auch ohne).
EPIC_NEEDS_REQUIRED_CHILD = frozenset({"In progress", "Awaiting confirmation", "Completed"})
DONE_FOR_AWAITING = frozenset({"Awaiting confirmation", "Completed"})
#: Regeln, die nur vom Item selbst abhängen, nicht von anderen Items.
OWN_RULES = frozenset({"epic_with_parent", "required_for_parent_missing"})

MESSAGES = {
    "epic_without_required_child": "Epic {item} braucht mindestens ein Pflichtkind, bevor es 'Open' verlässt.",
    "required_children_not_done": "Pflichtkinder von {item} sind noch nicht weit genug: {items}.",
    "children_still_active": "{item} lässt sich nicht schließen, solange Kinder aktiv sind: {items}.",
    "parent_closed": "{item} kann unter einem geschlossenen Parent nicht aktiv sein. Zuerst {items} wieder öffnen.",
    "epic_with_parent": "Epic {item} kann keinen Parent haben.",
    "required_for_parent_missing": "{item} hat einen Parent, aber kein 'Pflicht für Parent'.",
    "parent_cycle": "Die Parent-Verweise bilden einen Kreis: {items}.",
    "dependency_cycle": "Die Abhängigkeiten bilden einen Kreis: {items}.",
    "unknown_reference": "{item} verweist auf unbekannte Items: {items}.",
}


class LifecycleViolation(DomainError):
    """Eine Änderung verletzt eine Regel; `code` nennt sie, `details` das Item und die Beteiligten (Labels)."""

    def __init__(self, code: str, item: str, related: Sequence[str] = (), **details: object) -> None:
        items = ", ".join(related)
        message = MESSAGES.get(code, "Regel {code} verletzt von {item}.").format(item=item, items=items, code=code)
        super().__init__(message, code=code, details={"item": item, "items": list(related), **details})


@dataclass(frozen=True, order=True)
class Violation:
    code: str
    uid: str
    related: tuple[str, ...] = ()


def is_closed(item: Item) -> bool:
    return item.status in FINAL_STATUSES


class LifecycleRules:
    def violations(self, items: Sequence[Item]) -> set[Violation]:
        children: dict[str, list[Item]] = {}
        for item in items:
            if item.parent_uid:
                children.setdefault(item.parent_uid, []).append(item)
        known = {item.uid for item in items}
        found: set[Violation] = set()
        for item in items:
            found.update(self._structure(item, known))
            found.update(self._as_parent(item, children.get(item.uid, [])))
        found.update(self._cycles(items, lambda i: [i.parent_uid] if i.parent_uid else [], "parent_cycle"))
        found.update(self._cycles(items, lambda i: list(i.dependencies), "dependency_cycle"))
        return found

    def check_change(self, before: Sequence[Item], after: Sequence[Item], returning: Sequence[Item] = ()) -> None:
        """Wirft `LifecycleViolation` für die erste Verletzung, die die Änderung einführt oder erweitert.

        `returning` sind Items, die wieder in Gebrauch kommen (aus dem Papierkorb): ihre eigenen alten Mängel
        (`OWN_RULES`) gelten nicht als neu, Regeln zwischen Items schon.
        """
        label = {item.uid: item.label for item in (*before, *after, *returning)}
        existing = {(v.code, v.uid): set(v.related) for v in self.violations(before)}
        back = {item.uid for item in returning}
        for v in self.violations([*before, *returning]):
            if v.uid in back and v.code in OWN_RULES:
                existing[(v.code, v.uid)] = set(v.related)
        was_closed = {item.uid for item in before if is_closed(item)}
        for v in sorted(self.violations(after)):
            known = existing.get((v.code, v.uid))
            if known is not None and set(v.related) <= known:
                continue
            related = tuple(label.get(uid, uid) for uid in v.related)
            if v.code == "children_still_active" and v.uid in was_closed:
                # Der Parent blieb geschlossen, ihm wurde ein aktives Kind hinzugefügt (nicht er geschlossen).
                child = next(uid for uid in v.related if uid not in (known or set()))
                chain = closed_ancestors(after, child)
                raise LifecycleViolation(
                    "parent_closed",
                    label[child],
                    tuple(label[uid] for uid in chain),
                    ancestors=[{"uid": uid, "label": label[uid]} for uid in chain],
                )
            raise LifecycleViolation(v.code, label.get(v.uid, v.uid), related)

    @staticmethod
    def _structure(item: Item, known: set[str]) -> Iterable[Violation]:
        if item.type == EPIC and item.parent_uid:
            yield Violation("epic_with_parent", item.uid)
        if item.parent_uid and item.required_for_parent is None:
            yield Violation("required_for_parent_missing", item.uid)
        refs = ([item.parent_uid] if item.parent_uid else []) + list(item.dependencies)
        unknown = tuple(sorted({ref for ref in refs if ref not in known}))
        if unknown:
            yield Violation("unknown_reference", item.uid, unknown)

    @staticmethod
    def _as_parent(parent: Item, children: list[Item]) -> Iterable[Violation]:
        required = [c for c in children if c.required_for_parent is True]
        if parent.type == EPIC and parent.status in EPIC_NEEDS_REQUIRED_CHILD and not required:
            yield Violation("epic_without_required_child", parent.uid)
        if parent.status == "Awaiting confirmation":
            blocking = [c for c in required if c.status not in DONE_FOR_AWAITING]
        elif parent.status == "Completed":
            blocking = [c for c in required if c.status != "Completed"]
        else:
            blocking = []
        if blocking:
            yield Violation("required_children_not_done", parent.uid, _uids(blocking))
        if is_closed(parent):
            active = [c for c in children if not is_closed(c)]
            if active:
                yield Violation("children_still_active", parent.uid, _uids(active))

    @staticmethod
    def _cycles(items: Sequence[Item], edges_of: Callable[[Item], Iterable[str]], code: str) -> Iterable[Violation]:
        known = {item.uid for item in items}
        graph = {item.uid: [t for t in edges_of(item) if t in known] for item in items}
        seen: set[frozenset[str]] = set()
        for start in sorted(graph):
            cycle = _find_cycle(start, graph, [], set(), set())
            if cycle and frozenset(cycle) not in seen:
                seen.add(frozenset(cycle))
                yield Violation(code, min(cycle), tuple(sorted(cycle)))


def _find_cycle(
    node: str, graph: dict[str, list[str]], path: list[str], on_path: set[str], done: set[str]
) -> list[str] | None:
    if node in on_path:
        return path[path.index(node) :]
    if node in done:
        return None
    path.append(node)
    on_path.add(node)
    for target in graph[node]:
        cycle = _find_cycle(target, graph, path, on_path, done)
        if cycle:
            return cycle
    path.pop()
    on_path.discard(node)
    done.add(node)
    return None


def _uids(items: Iterable[Item]) -> tuple[str, ...]:
    return tuple(sorted(item.uid for item in items))


def closed_ancestors(items: Sequence[Item], uid: str) -> tuple[str, ...]:
    """Die geschlossenen Parents über einem Item bis zum ersten offenen, von oben nach unten (so wird geöffnet)."""
    by_uid = {item.uid: item for item in items}
    chain: list[str] = []
    parent = by_uid[uid].parent_uid
    while parent in by_uid and parent not in chain and is_closed(by_uid[parent]):
        chain.append(parent)
        parent = by_uid[parent].parent_uid
    return tuple(reversed(chain))

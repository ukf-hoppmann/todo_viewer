"""Items des Backlogs: feste Wertelisten, Datentypen und die reinen Funktionen (Fortschritt, Filter)."""

from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime

TYPES = ("Epic", "Story", "Task")
#: Status in der Reihenfolge des Ablaufs; `final` sind `Completed` und `Rejected`.
STATUSES = ("Open", "In progress", "Awaiting confirmation", "Completed", "Rejected")
FINAL_STATUSES = frozenset({"Completed", "Rejected"})
#: Priorität → Rang (kleiner = wichtiger).
PRIORITIES = {"Urgent": 1, "Important": 2, "Normal": 3, "Prospective": 4}

#: Elementtyp im Register ↔ Typ des Items.
KIND_BY_TYPE = {"Epic": "epic", "Story": "story", "Task": "task"}
TYPE_BY_KIND = {kind: type_ for type_, kind in KIND_BY_TYPE.items()}


@dataclass(frozen=True)
class Item:
    """Ein Item. `uid`, `label`, `revision` und `deleted_at` gehören dem Register von `workspace`."""

    uid: str
    project_uid: str
    label: str
    type: str
    title: str
    status: str
    priority: str
    area: str | None
    parent_uid: str | None
    required_for_parent: bool | None
    goal: str | None
    completion_criteria: str | None
    summary: str | None
    resolution: str | None
    created: date
    position: int
    revision: int
    deleted_at: datetime | None = None
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    #: Namen der Notiz- und Spec-Dokumente (Namen folgen dem Label).
    notes: tuple[str, ...] = field(default_factory=tuple)
    spec: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Progress:
    done: int
    total: int


@dataclass(frozen=True)
class ItemFilter:
    """Was gezeigt wird; leere Mengen heißen „alles“. Der Text sucht in Label und Titel (ohne Groß/Klein)."""

    statuses: frozenset[str] = frozenset()
    priorities: frozenset[str] = frozenset()
    query: str = ""

    def matches(self, item: Item) -> bool:
        q = self.query.strip().lower()
        return (
            (not self.statuses or item.status in self.statuses)
            and (not self.priorities or item.priority in self.priorities)
            and (not q or q in item.title.lower() or q in item.label.lower())
        )


def counts(item: Item) -> bool:
    """Ein Kind zählt für den Fortschritt seines Elternteils nicht, wenn es optional oder abgelehnt ist."""
    return item.required_for_parent is not False and item.status != "Rejected"


def item_progress(items: Iterable[Item]) -> dict[str, Progress]:
    """Fortschritt (erledigt/gesamt) je Item über alle Nachkommen, unabhängig von Filtern.

    Optionale und abgelehnte Kinder werden samt Unterbaum übersprungen. Items ohne zählende Nachkommen haben keinen
    Eintrag. Ein Kreis in den Eltern-Verweisen hält die Rechnung nicht auf.
    """
    all_items = list(items)
    children: dict[str, list[Item]] = {}
    for item in all_items:
        if item.parent_uid and counts(item):
            children.setdefault(item.parent_uid, []).append(item)
    result: dict[str, Progress] = {}

    def visit(uid: str, seen: frozenset[str]) -> Progress:
        known = result.get(uid)
        if known is not None:
            return known
        done = total = 0
        for child in children.get(uid, []):
            if child.uid in seen:
                continue
            sub = visit(child.uid, seen | {child.uid})
            done += sub.done + (1 if child.status == "Completed" else 0)
            total += sub.total + 1
        progress = Progress(done, total)
        if total > 0:
            result[uid] = progress
        return progress

    for item in all_items:
        visit(item.uid, frozenset({item.uid}))
    return result


def project_progress(items: Iterable[Item]) -> Progress:
    """Fortschritt eines Projekts über alle seine Items; optionale und abgelehnte zählen nicht."""
    counted = [item for item in items if counts(item)]
    return Progress(sum(1 for item in counted if item.status == "Completed"), len(counted))


def valid_values(values: Collection[str], allowed: Collection[str]) -> list[str]:
    """Die Werte, die nicht in `allowed` stehen (für die Prüfung von Filtern)."""
    return [value for value in values if value not in allowed]

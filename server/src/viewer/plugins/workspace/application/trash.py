from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from viewer.core.application.ports import BackupMaker, Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import BackupFailed, NotFound, VersionConflict
from viewer.core.domain.events import Event
from viewer.plugins.workspace.application.ports import (
    ChildrenProvider,
    ElementStore,
    ProjectStore,
    Purger,
    RestoreGuard,
)
from viewer.plugins.workspace.domain.model import Element, NotDeleted, ProjectInTrash

CHANGED_TOPIC = "workspace.element.changed"


@dataclass(frozen=True)
class KindHandlers:
    children: ChildrenProvider | None = None
    restore_guard: RestoreGuard | None = None
    purger: Purger | None = None


@dataclass(frozen=True)
class DeleteOutcome:
    """`has_children`: nichts wurde gelöscht, weil es Nachkommen gibt und `cascade` fehlte; `deleted` zählt die
    in den Papierkorb gelegten Elemente (mit Nachkommen)."""

    has_children: bool
    children: int
    deleted: int


def _deleted_at(at: datetime | None) -> Callable[[Element], bool]:
    return lambda element: element.deleted_at == at


class TrashService:
    """Löschen mit Kaskade, Wiederherstellen und endgültiges Löschen für Elemente aller Plugins."""

    def __init__(
        self,
        elements: ElementStore,
        projects: ProjectStore,
        database: Database,
        clock: Clock,
        events: EventBus,
        backups: BackupMaker,
    ) -> None:
        self._elements = elements
        self._projects = projects
        self._database = database
        self._clock = clock
        self._events = events
        self._backups = backups
        self._handlers: dict[str, KindHandlers] = {}

    # --- Anmeldung der Plugins (`TrashRegistry`) -----------------------------------------------------------------

    def register(
        self,
        kind: str,
        *,
        children: ChildrenProvider | None = None,
        restore_guard: RestoreGuard | None = None,
        purger: Purger | None = None,
    ) -> None:
        self._handlers[kind] = KindHandlers(children, restore_guard, purger)

    # --- Fälle ---------------------------------------------------------------------------------------------------

    def delete_element(self, uid: str, version: int, cascade: bool) -> DeleteOutcome:
        with self._database.transaction() as tx:
            element = self._require(tx, uid)
            if element.deleted_at is not None:
                raise NotFound(f"Element {uid} liegt schon im Papierkorb", details={"uid": uid})
            if element.revision != version:
                raise VersionConflict(
                    "Das Element wurde inzwischen geändert",
                    details={"uid": uid, "expected": version, "current": element.revision},
                )
            descendants = self._descendants(tx, element, lambda e: e.deleted_at is None)
            if descendants and not cascade:
                return DeleteOutcome(True, len(descendants), 0)
            at = self._clock.now()
            for entry in [element, *descendants]:
                self._elements.set_deleted(tx, entry.uid, at, at)
            uids = [entry.uid for entry in [element, *descendants]]
        self._announce("deleted", uids)
        return DeleteOutcome(False, len(descendants), len(uids))

    def list_trash(self, project_uids: Sequence[str] | None, query: str) -> list[Element]:
        with self._database.transaction() as tx:
            return self._elements.list_deleted(tx, project_uids, query)

    def restore_elements(self, uids: Sequence[str]) -> list[str]:
        """Holt die Elemente und ihre mit ihnen gelöschten Nachkommen zurück. Gibt alle wiederhergestellten `uid`s
        zurück."""
        restored: list[str] = []
        with self._database.transaction() as tx:
            for root in self._roots(tx, uids):
                self._ensure_deleted(tx, root)
                project = self._projects.get(tx, root.project_uid)
                if project is None or project.deleted_at is not None:
                    raise ProjectInTrash(
                        "Das Projekt des Elements liegt selbst im Papierkorb", details={"uid": root.uid}
                    )
                same_time = self._descendants(tx, root, _deleted_at(root.deleted_at))
                now = self._clock.now()
                for entry in [root, *same_time]:
                    guard = self._handlers.get(entry.kind, KindHandlers()).restore_guard
                    if guard is not None:
                        guard(tx, entry)
                    self._elements.set_deleted(tx, entry.uid, None, now)
                    restored.append(entry.uid)
        self._announce("restored", restored)
        return restored

    def purge_elements(self, uids: Sequence[str]) -> list[str]:
        """Löscht die Elemente aus dem Papierkorb endgültig, mit allen Nachkommen. Gibt die gelöschten `uid`s zurück.
        Vorher wird die Datenbank gesichert (Architektur §2); scheitert das, bleibt alles stehen."""
        self._back_up()
        purged: list[str] = []
        with self._database.transaction() as tx:
            for root in self._roots(tx, uids):
                self._ensure_deleted(tx, root)
                everything = [root, *self._descendants(tx, root, lambda e: True)]
                for entry in reversed(everything):  # Kinder vor ihren Eltern
                    purger = self._handlers.get(entry.kind, KindHandlers()).purger
                    if purger is not None:
                        purger(tx, entry.uid)
                    self._elements.delete(tx, entry.uid)
                    purged.append(entry.uid)
        self._announce("purged", purged)
        return purged

    # --- Hilfen --------------------------------------------------------------------------------------------------

    def _back_up(self) -> None:
        try:
            self._backups.create("purge")
        except OSError as exc:
            raise BackupFailed(
                "Die Datenbank konnte nicht gesichert werden; nichts wurde gelöscht", details={"reason": str(exc)}
            ) from exc

    def _require(self, tx: Transaction, uid: str) -> Element:
        element = self._elements.get(tx, uid)
        if element is None:
            raise NotFound(f"Element {uid} gibt es nicht", details={"uid": uid})
        return element

    @staticmethod
    def _ensure_deleted(tx: Transaction, element: Element) -> None:
        if element.deleted_at is None:
            raise NotDeleted(f"Element {element.label} liegt nicht im Papierkorb", details={"uid": element.uid})

    def _children(self, tx: Transaction, element: Element) -> list[str]:
        provider = self._handlers.get(element.kind, KindHandlers()).children
        return provider(tx, element.uid) if provider is not None else []

    def _descendants(self, tx: Transaction, root: Element, follow: Callable[[Element], bool]) -> list[Element]:
        """Nachkommen in Breitensuche (Eltern vor Kindern); man steigt nur durch Elemente, für die `follow` gilt."""
        found: list[Element] = []
        seen = {root.uid}
        queue = [root]
        while queue:
            current = queue.pop(0)
            for child_uid in self._children(tx, current):
                if child_uid in seen:
                    continue
                seen.add(child_uid)
                child = self._elements.get(tx, child_uid)
                if child is None or not follow(child):
                    continue
                found.append(child)
                queue.append(child)
        return found

    def _roots(self, tx: Transaction, uids: Sequence[str]) -> list[Element]:
        """Die gewählten Elemente ohne die, die Nachkommen eines anderen gewählten sind (Vorfahren-Regel)."""
        chosen = [self._require(tx, uid) for uid in dict.fromkeys(uids)]
        covered: set[str] = set()
        for element in chosen:
            covered.update(entry.uid for entry in self._descendants(tx, element, lambda e: True))
        return [element for element in chosen if element.uid not in covered]

    def _announce(self, change: str, uids: list[str]) -> None:
        if uids:
            self._events.publish(Event(CHANGED_TOPIC, {"change": change, "uids": uids}, public=True))


__all__ = ["CHANGED_TOPIC", "DeleteOutcome", "KindHandlers", "TrashService"]

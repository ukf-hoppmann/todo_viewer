from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from viewer.core.application.ports import Database, Transaction
from viewer.core.domain.errors import InvalidInput, NotFound
from viewer.plugins.backlog.application.ports import ItemRepository, NotesRepository
from viewer.plugins.backlog.domain.model import PRIORITIES, STATUSES, Item, ItemFilter, Progress, item_progress
from viewer.plugins.backlog.domain.notes import state_of
from viewer.plugins.workspace import ElementRegistry

_LABEL = re.compile(r"^[A-Z]+-\d+$")


@dataclass(frozen=True)
class IndexEntry:
    item: Item
    progress: Progress | None
    #: Zustand des Kopfs der Notes (`current`, `stale`, `missing`); `None` ohne Notes.
    notes_state: str | None = None


@dataclass(frozen=True)
class ItemDetail:
    item: Item
    parent: Item | None
    children: list[Item]
    dependencies: list[Item]
    progress: Progress | None
    notes_state: str | None = None


class ItemService:
    """Lesende Anwendungsfälle des Backlogs."""

    def __init__(
        self, items: ItemRepository, registry: ElementRegistry, database: Database, notes: NotesRepository
    ) -> None:
        self._items = items
        self._registry = registry
        self._database = database
        self._notes = notes

    def list_items(
        self,
        project_uids: Sequence[str] | None,
        statuses: Sequence[str] = (),
        priorities: Sequence[str] = (),
        query: str = "",
    ) -> list[IndexEntry]:
        """Die Items der Projekte, die der Filter durchlässt; der Fortschritt zählt immer über alle Items."""
        self._check_values("status", statuses, STATUSES)
        self._check_values("priority", priorities, tuple(PRIORITIES))
        item_filter = ItemFilter(frozenset(statuses), frozenset(priorities), query)
        with self._database.transaction() as tx:
            everything = self._items.list_in(tx, project_uids)
            shown = [item for item in everything if item_filter.matches(item)]
            notes = self._notes.parts_for(tx, [item.uid for item in shown if item.notes])
        progress = item_progress(everything)
        return [
            IndexEntry(item, progress.get(item.uid), state_of(notes[item.uid]) if item.uid in notes else None)
            for item in shown
        ]

    def get_item(self, ref: str, project_uid: str | None = None) -> ItemDetail:
        """`ref` ist eine `uid` oder ein Label (dann mit Projekt; auch ein früheres Label löst auf)."""
        with self._database.transaction() as tx:
            item = self.resolve(tx, ref, project_uid)
            siblings = self._items.list_in(tx, [item.project_uid], include_deleted=True)
            by_uid = {entry.uid: entry for entry in siblings}
            children = self._items.children(tx, item.uid)
            dependencies = [by_uid[uid] for uid in item.dependencies if uid in by_uid]
            parent = by_uid.get(item.parent_uid) if item.parent_uid else None
            notes = self._notes.get(tx, item.uid)
        progress = item_progress(entry for entry in siblings if entry.deleted_at is None).get(item.uid)
        return ItemDetail(item, parent, children, dependencies, progress, state_of(notes.parts) if notes else None)

    def resolve(self, tx: Transaction, ref: str, project_uid: str | None) -> Item:
        item = self._items.get(tx, ref)
        if item is None and project_uid is not None:
            element = self._registry.find_by_label(tx, project_uid, ref)
            item = self._items.get(tx, element.uid) if element else None
        if item is None:
            if project_uid is None and _LABEL.match(ref.strip()):
                raise InvalidInput(
                    f"'{ref}' ist keine uid; für ein Label braucht es das Projekt", details={"field": "project"}
                )
            raise NotFound(f"Item {ref} gibt es nicht", details={"ref": ref})
        return item

    @staticmethod
    def _check_values(field: str, values: Sequence[str], allowed: Sequence[str]) -> None:
        unknown = [value for value in values if value not in allowed]
        if unknown:
            raise InvalidInput(
                f"Unbekannte Werte für {field}: {', '.join(unknown)}",
                details={"field": field, "allowed": list(allowed)},
            )

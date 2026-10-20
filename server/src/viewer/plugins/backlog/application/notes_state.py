from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.events import Event
from viewer.plugins.backlog.application.items import ItemService
from viewer.plugins.backlog.application.ports import Notes, NotesRepository
from viewer.plugins.backlog.domain.model import Item
from viewer.plugins.backlog.domain.notes import (
    Entry,
    Hint,
    NotesNotFound,
    NotesParts,
    NotesStateMissing,
    hints,
    stamped,
    state_text,
)

CHANGED_TOPIC = "backlog.document.changed"


@dataclass(frozen=True)
class NotesState:
    """Der Kopf der Notes eines Items mit Stempel und Protokoll; `version` ist die Version des Kopfs."""

    notes: Notes
    hints: tuple[Hint, ...] = ()


class NotesStateService:
    """Der Kopf der Item-Notes: lesen ohne Protokoll, ersetzen und bestätigen. Beides setzt den Stempel (STORY-093)."""

    def __init__(
        self, items: ItemService, notes: NotesRepository, database: Database, clock: Clock, events: EventBus
    ) -> None:
        self._items = items
        self._notes = notes
        self._database = database
        self._clock = clock
        self._events = events

    def get(self, ref: str, project_uid: str | None) -> NotesState:
        with self._database.transaction() as tx:
            return NotesState(self._existing(tx, self._items.resolve(tx, ref, project_uid)))

    def put(self, ref: str, project_uid: str | None, content: str, version: int) -> NotesState:
        """Ersetzt den Kopf in `version` und stempelt ihn gegen den letzten Eintrag."""
        text = state_text(content)
        if not text:
            raise InvalidInput("Der Kopf ist leer", details={"field": "content"})
        return self._write(ref, project_uid, version, lambda notes: replace(notes.parts, state=text))

    def confirm(self, ref: str, project_uid: str | None, version: int) -> NotesState:
        """Bestätigt den Kopf unverändert: nur der Stempel zieht auf den letzten Eintrag nach."""

        def same(notes: Notes) -> NotesParts:
            if not notes.parts.state.strip():
                raise NotesStateMissing("Die Notes haben noch keinen Kopf; zuerst einen schreiben")
            return notes.parts

        return self._write(ref, project_uid, version, same)

    def entries(self, ref: str, project_uid: str | None, last: int | None) -> list[tuple[int, Entry]]:
        """Die Protokolleinträge mit Position, mit `last` nur die letzten."""
        with self._database.transaction() as tx:
            notes = self._existing(tx, self._items.resolve(tx, ref, project_uid))
        numbered = list(enumerate(notes.parts.entries))
        return numbered[-last:] if last is not None and last > 0 else numbered

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _write(
        self, ref: str, project_uid: str | None, version: int, change: Callable[[Notes], NotesParts]
    ) -> NotesState:
        with self._database.transaction() as tx:
            item = self._items.resolve(tx, ref, project_uid)
            notes = self._existing(tx, item)
            parts = stamped(change(notes))
            self._notes.save(
                tx,
                item.uid,
                parts,
                expected=notes.revision,
                expected_state=version,
                state_changed=True,
                at=self._clock.now(),
            )
            stored = self._existing(tx, item)
        self._events.publish(
            Event(CHANGED_TOPIC, {"uid": item.uid, "name": stored.name, "change": "updated"}, public=True)
        )
        return NotesState(stored, hints(notes.parts, parts, rewritten=False))

    def _existing(self, tx: Transaction, item: Item) -> Notes:
        notes = self._notes.get(tx, item.uid)
        if notes is None:
            raise NotesNotFound(f"{item.label} hat keine Notes", details={"item": item.label})
        return notes

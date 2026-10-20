from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.events import Event
from viewer.plugins.backlog.application.items import ItemService
from viewer.plugins.backlog.application.ports import (
    Document,
    DocumentRepository,
    ItemRepository,
    Notes,
    NotesRepository,
)
from viewer.plugins.backlog.domain.documents import (
    NOTES,
    DocumentExists,
    DocumentNotFound,
    NotesEntry,
    append_entry,
    new_document_kind,
    notes_header,
    notes_name,
)
from viewer.plugins.backlog.domain.editing import normalize
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules
from viewer.plugins.backlog.domain.model import Item
from viewer.plugins.backlog.domain.notes import NotesParts, assemble, replaced_by_text, split, title_of

CHANGED_TOPIC = "backlog.document.changed"


class DocumentService:
    """Notizen und Specs eines Items. Das Item bekommt mit seinem ersten Notiz-Dokument eine Kurzfassung (Regel).

    Die Notizen liegen in Teilen (Vorspann, Kopf, Protokoll); nach außen sind sie eine zusammengesetzte Datei, deren
    `revision` jede Änderung zählt."""

    def __init__(
        self,
        items: ItemService,
        repository: ItemRepository,
        documents: DocumentRepository,
        notes: NotesRepository,
        registry: Any,
        database: Database,
        clock: Clock,
        events: EventBus,
    ) -> None:
        self._items = items
        self._repository = repository
        self._documents = documents
        self._notes = notes
        self._registry = registry
        self._database = database
        self._clock = clock
        self._events = events
        self._rules = LifecycleRules()

    def list_documents(self, ref: str, project_uid: str | None) -> list[Document]:
        with self._database.transaction() as tx:
            item = self._items.resolve(tx, ref, project_uid)
            notes = self._notes.get(tx, item.uid)
            return [*([_as_document(item, notes)] if notes else []), *self._documents.list_for(tx, item.uid)]

    def get_document(self, ref: str, project_uid: str | None, name: str) -> Document:
        with self._database.transaction() as tx:
            item = self._items.resolve(tx, ref, project_uid)
            return self._existing(tx, item, name)

    def put_document(
        self,
        ref: str,
        project_uid: str | None,
        name: str,
        content: str,
        version: int | None,
        summary: str | None,
    ) -> Document:
        """Ersetzt ein Dokument in `version` oder legt ein neues an (`version` fehlt). Notizen werden zerlegt: ohne
        `## Stand` im Text bleibt der Kopf, den Stempel setzt nur der Server."""
        change = "updated"
        with self._database.transaction() as tx:
            item = self._items.resolve(tx, ref, project_uid)
            now = self._clock.now()
            if version is None:
                kind = new_document_kind(item, name)
                if self._documents.get(tx, item.uid, name) is not None or (
                    kind == NOTES and self._notes.get(tx, item.uid) is not None
                ):
                    raise DocumentExists(f"Das Dokument {name} gibt es schon", details={"name": name})
                self._check_and_summarize(tx, item, summary, add_notes=name if kind == NOTES else None)
                if kind == NOTES:
                    parts = replaced_by_text(NotesParts("", "", None, ()), content)
                    self._notes.insert(tx, Notes(item.uid, name, parts, 1, 1, now))
                else:
                    self._documents.insert(tx, Document(item.uid, name, kind, content, 1, now))
                change = "created"
            else:
                existing = self._existing(tx, item, name)
                self._check_and_summarize(tx, item, summary, add_notes=None)
                if existing.kind == NOTES:
                    notes = self._stored_notes(tx, item)
                    parts = replaced_by_text(notes.parts, content)
                    changed = (parts.state, parts.stamp) != (notes.parts.state, notes.parts.stamp)
                    self._notes.save(tx, item.uid, parts, expected=version, state_changed=changed, at=now)
                else:
                    self._documents.update(tx, item.uid, name, content, version, now)
            document = self._existing(tx, item, name)
        self._changed(item.uid, name, change)
        return document

    def append_note(
        self,
        ref: str,
        project_uid: str | None,
        topic: str,
        discussed: Sequence[str],
        decided: Sequence[str],
        open_points: Sequence[str],
        summary: str | None,
    ) -> Document:
        """Hängt einen datierten Eintrag an die Notizen; der erste Eintrag legt sie an."""
        with self._database.transaction() as tx:
            item = self._items.resolve(tx, ref, project_uid)
            now = self._clock.now()
            entry = NotesEntry.create(now.date(), topic, discussed, decided, open_points)
            existing = self._notes.get(tx, item.uid)
            name = existing.name if existing else notes_name(item.label)
            self._check_and_summarize(tx, item, summary, add_notes=None if existing else name)
            if existing is None:
                parts = split(append_entry(notes_header(item), entry))
                self._notes.insert(tx, Notes(item.uid, name, parts, 1, 1, now))
                change = "created"
            else:
                appended = split(append_entry(assemble(title_of(item), existing.parts), entry))
                parts = replace(existing.parts, preamble=appended.preamble, entries=appended.entries)
                self._notes.save(tx, item.uid, parts, expected=existing.revision, state_changed=False, at=now)
                change = "updated"
            document = self._existing(tx, item, name)
        self._changed(item.uid, name, change)
        return document

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _existing(self, tx: Transaction, item: Item, name: str) -> Document:
        notes = self._notes.get(tx, item.uid)
        if notes is not None and notes.name == name:
            return _as_document(item, notes)
        document = self._documents.get(tx, item.uid, name)
        if document is None:
            raise DocumentNotFound(f"Das Dokument {name} gibt es nicht", details={"name": name, "item": item.label})
        return document

    def _stored_notes(self, tx: Transaction, item: Item) -> Notes:
        notes = self._notes.get(tx, item.uid)
        assert notes is not None
        return notes

    def _check_and_summarize(self, tx: Transaction, item: Item, summary: str | None, *, add_notes: str | None) -> None:
        """Prüft die Regeln für das Item nach der Änderung (Kurzfassung, neues Notiz-Dokument) und schreibt die
        Kurzfassung, falls eine mitkommt."""
        updated = item
        if summary is not None:
            updated = replace(updated, summary=normalize("summary", summary))  # type: ignore[arg-type]
        if add_notes is not None:
            updated = replace(updated, notes=(*updated.notes, add_notes))
        if updated == item:
            return
        before = self._repository.list_in(tx, [item.project_uid])
        self._rules.check_change(before, [updated if entry.uid == item.uid else entry for entry in before])
        if updated.summary != item.summary:
            revision = self._registry.bump_revision(tx, item.uid, item.revision)
            self._repository.update(tx, replace(updated, revision=revision))

    def _changed(self, uid: str, name: str, change: str) -> None:
        self._events.publish(Event(CHANGED_TOPIC, {"uid": uid, "name": name, "change": change}, public=True))


def _as_document(item: Item, notes: Notes) -> Document:
    """Die Notizen als zusammengesetzte Datei; die Titelzeile kommt aus dem Item."""
    content = assemble(title_of(item), notes.parts)
    return Document(item.uid, notes.name, NOTES, content, notes.revision, notes.updated_at)

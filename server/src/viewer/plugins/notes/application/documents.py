"""Dokumente einer Note: Notizen und Specs."""

from __future__ import annotations

from collections.abc import Sequence

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.events import Event
from viewer.plugins.notes.application.common import DOCUMENT_TOPIC, Resolver
from viewer.plugins.notes.application.ports import Document, DocumentRepository
from viewer.plugins.notes.domain.documents import (
    NOTES,
    DocumentExists,
    DocumentNotFound,
    NotesEntry,
    append_entry,
    new_document_kind,
    notes_header,
    notes_name,
)
from viewer.plugins.notes.domain.lifecycle import check_open
from viewer.plugins.notes.domain.model import Note


class DocumentService:
    """Lesen geht bei jeder Note, auch im Archiv und im Papierkorb; Schreiben nur bei einer Note in Gebrauch."""

    def __init__(
        self, documents: DocumentRepository, resolver: Resolver, database: Database, clock: Clock, events: EventBus
    ) -> None:
        self._documents = documents
        self._resolver = resolver
        self._database = database
        self._clock = clock
        self._events = events

    def list_documents(self, ref: str, project_uid: str | None) -> list[Document]:
        with self._database.transaction() as tx:
            return self._documents.list_for(tx, self._resolver.note(tx, ref, project_uid).uid)

    def get_document(self, ref: str, project_uid: str | None, name: str) -> Document:
        with self._database.transaction() as tx:
            return self._existing(tx, self._resolver.note(tx, ref, project_uid), name)

    def put_document(self, ref: str, project_uid: str | None, name: str, content: str, version: int | None) -> Document:
        """Ersetzt ein Dokument in `version` oder legt ein neues an (`version` fehlt)."""
        change = "updated"
        with self._database.transaction() as tx:
            note = self._resolver.note(tx, ref, project_uid)
            check_open(note)
            now = self._clock.now()
            if version is None:
                kind = new_document_kind(note.label, name)
                if self._documents.get(tx, note.uid, name) is not None:
                    raise DocumentExists(f"Das Dokument {name} gibt es schon", details={"name": name})
                self._documents.insert(tx, Document(note.uid, name, kind, content, 1, now))
                change = "created"
            else:
                self._existing(tx, note, name)
                self._documents.update(tx, note.uid, name, content, version, now)
            document = self._existing(tx, note, name)
        self._changed(note.uid, name, change)
        return document

    def append_note(
        self,
        ref: str,
        project_uid: str | None,
        topic: str,
        discussed: Sequence[str],
        decided: Sequence[str],
        open_points: Sequence[str],
    ) -> Document:
        """Hängt einen datierten Eintrag an `<LABEL>_notes.md`; der erste Eintrag legt das Dokument an."""
        with self._database.transaction() as tx:
            note = self._resolver.note(tx, ref, project_uid)
            check_open(note)
            now = self._clock.now()
            entry = NotesEntry.create(now.date(), topic, discussed, decided, open_points)
            name = notes_name(note.label)
            existing = self._documents.get(tx, note.uid, name)
            if existing is None:
                content = append_entry(notes_header(note.label, note.summary), entry)
                self._documents.insert(tx, Document(note.uid, name, NOTES, content, 1, now))
                change = "created"
            else:
                self._documents.update(
                    tx, note.uid, name, append_entry(existing.content, entry), existing.revision, now
                )
                change = "updated"
            document = self._existing(tx, note, name)
        self._changed(note.uid, name, change)
        return document

    def _existing(self, tx: Transaction, note: Note, name: str) -> Document:
        document = self._documents.get(tx, note.uid, name)
        if document is None:
            raise DocumentNotFound(f"Das Dokument {name} gibt es nicht", details={"name": name, "note": note.label})
        return document

    def _changed(self, uid: str, name: str, change: str) -> None:
        self._events.publish(Event(DOCUMENT_TOPIC, {"uid": uid, "name": name, "change": change}, public=True))

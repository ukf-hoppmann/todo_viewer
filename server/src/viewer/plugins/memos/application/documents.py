"""Dokumente einer Note: Notizen und Specs."""

from __future__ import annotations

from collections.abc import Sequence

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import DOCUMENT_TOPIC, Resolver
from viewer.plugins.memos.application.ports import Document, DocumentRepository
from viewer.plugins.memos.domain.documents import (
    NOTES,
    DocumentExists,
    DocumentNotFound,
    NotesEntry,
    append_entry,
    new_document_kind,
    notes_header,
    notes_name,
)
from viewer.plugins.memos.domain.lifecycle import check_open
from viewer.plugins.memos.domain.model import Memo


class DocumentService:
    """Lesen geht bei jedem Memo, auch im Archiv und im Papierkorb; Schreiben nur bei einem Memo in Gebrauch."""

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
            return self._documents.list_for(tx, self._resolver.memo(tx, ref, project_uid).uid)

    def get_document(self, ref: str, project_uid: str | None, name: str) -> Document:
        with self._database.transaction() as tx:
            return self._existing(tx, self._resolver.memo(tx, ref, project_uid), name)

    def put_document(self, ref: str, project_uid: str | None, name: str, content: str, version: int | None) -> Document:
        """Ersetzt ein Dokument in `version` oder legt ein neues an (`version` fehlt)."""
        change = "updated"
        with self._database.transaction() as tx:
            memo = self._resolver.memo(tx, ref, project_uid)
            check_open(memo)
            now = self._clock.now()
            if version is None:
                kind = new_document_kind(memo.label, name)
                if self._documents.get(tx, memo.uid, name) is not None:
                    raise DocumentExists(f"Das Dokument {name} gibt es schon", details={"name": name})
                self._documents.insert(tx, Document(memo.uid, name, kind, content, 1, now))
                change = "created"
            else:
                self._existing(tx, memo, name)
                self._documents.update(tx, memo.uid, name, content, version, now)
            document = self._existing(tx, memo, name)
        self._changed(memo.uid, name, change)
        return document

    def append_memo(
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
            memo = self._resolver.memo(tx, ref, project_uid)
            check_open(memo)
            now = self._clock.now()
            entry = NotesEntry.create(now.date(), topic, discussed, decided, open_points)
            name = notes_name(memo.label)
            existing = self._documents.get(tx, memo.uid, name)
            if existing is None:
                content = append_entry(notes_header(memo.label, memo.summary), entry)
                self._documents.insert(tx, Document(memo.uid, name, NOTES, content, 1, now))
                change = "created"
            else:
                self._documents.update(
                    tx, memo.uid, name, append_entry(existing.content, entry), existing.revision, now
                )
                change = "updated"
            document = self._existing(tx, memo, name)
        self._changed(memo.uid, name, change)
        return document

    def _existing(self, tx: Transaction, memo: Memo, name: str) -> Document:
        document = self._documents.get(tx, memo.uid, name)
        if document is None:
            raise DocumentNotFound(f"Das Dokument {name} gibt es nicht", details={"name": name, "memo": memo.label})
        return document

    def _changed(self, uid: str, name: str, change: str) -> None:
        self._events.publish(Event(DOCUMENT_TOPIC, {"uid": uid, "name": name, "change": change}, public=True))

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from viewer.core.application.ports import Clock, Transaction
from viewer.plugins.backlog.application.editing import ItemDeleted
from viewer.plugins.backlog.application.ports import (
    Document,
    DocumentRepository,
    ItemRepository,
    Notes,
    NotesRepository,
    TrashedDocument,
    TrashedDocumentRepository,
)
from viewer.plugins.backlog.domain.documents import NOTES, DocumentExists
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules
from viewer.plugins.backlog.domain.notes import split, without_title
from viewer.plugins.workspace import TrashEntry

#: Die Art, unter der gelöschte Dokumente im Papierkorb erscheinen.
DOCUMENT_ENTRY = "document"


class DocumentTrash:
    """Die gelöschten Dokumente der Items als Einträge des Papierkorbs (`TrashSource` von `workspace`).

    Wiederherstellen legt Text, bei Notizen auch Kopf und Protokoll, in die Tabellen zurück und gibt dem Item seine
    frühere Kurzfassung wieder, wenn es inzwischen keine hat."""

    def __init__(
        self,
        trashed: TrashedDocumentRepository,
        documents: DocumentRepository,
        notes: NotesRepository,
        items: ItemRepository,
        registry: Any,
        clock: Clock,
    ) -> None:
        self._trashed = trashed
        self._documents = documents
        self._notes = notes
        self._items = items
        self._registry = registry
        self._clock = clock
        self._rules = LifecycleRules()

    def list_deleted(self, tx: Transaction, project_uids: Sequence[str] | None, query: str) -> list[TrashEntry]:
        return [
            _entry(listing.document, listing.project_uid, listing.item_label)
            for listing in self._trashed.list_deleted(tx, project_uids, query)
        ]

    def get(self, tx: Transaction, uid: str) -> TrashEntry | None:
        document = self._trashed.get(tx, uid)
        item = self._items.get(tx, document.item_uid) if document else None
        if document is None or item is None:
            return None
        return _entry(document, item.project_uid, item.label)

    def restore(self, tx: Transaction, uid: str) -> None:
        document = self._trashed.get(tx, uid)
        assert document is not None
        item = self._items.get(tx, document.item_uid)
        assert item is not None
        if item.deleted_at is not None:
            raise ItemDeleted(item.label)
        now = self._clock.now()
        if document.kind == NOTES:
            if self._notes.get(tx, item.uid) is not None:
                raise _exists(document)
            self._notes.insert(tx, Notes(item.uid, document.name, split(without_title(document.content)), 1, 1, now))
            self._restore_summary(tx, item, document)
        else:
            if self._documents.get(tx, item.uid, document.name) is not None:
                raise _exists(document)
            self._documents.insert(tx, Document(item.uid, document.name, document.kind, document.content, 1, now))
        self._trashed.delete(tx, uid)

    def purge(self, tx: Transaction, uid: str) -> None:
        self._trashed.delete(tx, uid)

    def _restore_summary(self, tx: Transaction, item: Any, document: TrashedDocument) -> None:
        if document.summary is None or item.summary is not None:
            return
        updated = replace(item, summary=document.summary, notes=(document.name,))
        before = self._items.list_in(tx, [item.project_uid])
        self._rules.check_change(before, [updated if entry.uid == item.uid else entry for entry in before])
        revision = self._registry.bump_revision(tx, item.uid, item.revision)
        self._items.update(tx, replace(updated, revision=revision))


def _entry(document: TrashedDocument, project_uid: str, label: str) -> TrashEntry:
    return TrashEntry(
        document.uid, project_uid, DOCUMENT_ENTRY, label, document.name, document.deleted_at, document.item_uid
    )


def _exists(document: TrashedDocument) -> DocumentExists:
    return DocumentExists(
        f"Das Dokument {document.name} gibt es schon; das gelöschte lässt sich nicht zurückholen",
        details={"name": document.name},
    )

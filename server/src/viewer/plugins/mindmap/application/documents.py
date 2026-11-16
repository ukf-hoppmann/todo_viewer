"""Dokumente eines Knotens: Notizen und Specs."""

from __future__ import annotations

from collections.abc import Sequence

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.events import Event
from viewer.plugins.mindmap.application.ports import Document, DocumentRepository
from viewer.plugins.mindmap.application.service import MindmapService
from viewer.plugins.mindmap.domain.documents import (
    NOTES,
    DocumentExists,
    DocumentNotFound,
    NotesEntry,
    append_entry,
    new_document_kind,
    notes_header,
    notes_name,
)
from viewer.plugins.mindmap.domain.model import MindmapViolation, Node

DOCUMENT_TOPIC = "mindmap.document.changed"


class DocumentService:
    """Lesen geht bei jedem Knoten, auch im Papierkorb; Schreiben nur bei einem Knoten in Gebrauch."""

    def __init__(
        self,
        documents: DocumentRepository,
        nodes: MindmapService,
        database: Database,
        clock: Clock,
        events: EventBus,
    ) -> None:
        self._documents = documents
        self._nodes = nodes
        self._database = database
        self._clock = clock
        self._events = events

    def list_documents(self, ref: str, project_uid: str | None) -> list[Document]:
        with self._database.transaction() as tx:
            return self._documents.list_for(tx, self._nodes.resolve(tx, ref, project_uid).uid)

    def get_document(self, ref: str, project_uid: str | None, name: str) -> Document:
        with self._database.transaction() as tx:
            return self._existing(tx, self._nodes.resolve(tx, ref, project_uid), name)

    def put_document(self, ref: str, project_uid: str | None, name: str, content: str, version: int | None) -> Document:
        """Ersetzt ein Dokument in `version` oder legt ein neues an (`version` fehlt)."""
        change = "updated"
        with self._database.transaction() as tx:
            node = self._writable(tx, ref, project_uid)
            now = self._clock.now()
            if version is None:
                kind = new_document_kind(node.label, name)
                if self._documents.get(tx, node.uid, name) is not None:
                    raise DocumentExists(f"Das Dokument {name} gibt es schon", details={"name": name})
                self._documents.insert(tx, Document(node.uid, name, kind, content, 1, now))
                change = "created"
            else:
                self._existing(tx, node, name)
                self._documents.update(tx, node.uid, name, content, version, now)
            document = self._existing(tx, node, name)
        self._changed(node, name, change)
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
            node = self._writable(tx, ref, project_uid)
            now = self._clock.now()
            entry = NotesEntry.create(now.date(), topic, discussed, decided, open_points)
            name = notes_name(node.label)
            existing = self._documents.get(tx, node.uid, name)
            if existing is None:
                content = append_entry(notes_header(node.label, node.title), entry)
                self._documents.insert(tx, Document(node.uid, name, NOTES, content, 1, now))
                change = "created"
            else:
                self._documents.update(
                    tx, node.uid, name, append_entry(existing.content, entry), existing.revision, now
                )
                change = "updated"
            document = self._existing(tx, node, name)
        self._changed(node, name, change)
        return document

    def _writable(self, tx: Transaction, ref: str, project_uid: str | None) -> Node:
        node = self._nodes.resolve(tx, ref, project_uid)
        if node.deleted_at is not None:
            raise MindmapViolation("mindmap_node_deleted", f"{node.label} liegt im Papierkorb", node=node.label)
        return node

    def _existing(self, tx: Transaction, node: Node, name: str) -> Document:
        document = self._documents.get(tx, node.uid, name)
        if document is None:
            raise DocumentNotFound(f"Das Dokument {name} gibt es nicht", details={"name": name, "node": node.label})
        return document

    def _changed(self, node: Node, name: str, change: str) -> None:
        payload = {"uid": node.uid, "project_uid": node.project_uid, "name": name, "change": change}
        self._events.publish(Event(DOCUMENT_TOPIC, payload, public=True))

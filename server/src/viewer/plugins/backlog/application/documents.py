from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import InvalidInput, VersionConflict
from viewer.core.domain.events import Event
from viewer.plugins.backlog.application.editing import ItemDeleted
from viewer.plugins.backlog.application.items import ItemService
from viewer.plugins.backlog.application.ports import (
    Document,
    DocumentRepository,
    ItemRepository,
    Notes,
    NotesRepository,
    TrashedDocument,
    TrashedDocumentRepository,
)
from viewer.plugins.backlog.domain.documents import (
    NOTES,
    DocumentExists,
    DocumentNotFound,
    NotesEntry,
    append_entry,
    document_suffix,
    new_document_kind,
    notes_header,
    notes_name,
)
from viewer.plugins.backlog.domain.editing import normalize
from viewer.plugins.backlog.domain.lifecycle import LifecycleRules
from viewer.plugins.backlog.domain.model import Item
from viewer.plugins.backlog.domain.notes import (
    Hint,
    NotesParts,
    assemble,
    hints,
    replaced_by_text,
    split,
    stamped,
    state_of,
    state_text,
    title_of,
)

CHANGED_TOPIC = "backlog.document.changed"


@dataclass(frozen=True)
class DocumentWrite:
    """Ein geschriebenes Dokument; bei Notizen mit dem Zustand des Kopfs danach und Hinweisen (nie Ablehnungen)."""

    document: Document
    notes_state: str | None = None
    hints: tuple[Hint, ...] = ()


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
        trashed: TrashedDocumentRepository,
        registry: Any,
        database: Database,
        clock: Clock,
        events: EventBus,
    ) -> None:
        self._items = items
        self._repository = repository
        self._documents = documents
        self._notes = notes
        self._trashed = trashed
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
    ) -> DocumentWrite:
        """Ersetzt ein Dokument in `version` oder legt ein neues an (`version` fehlt). Notizen werden zerlegt: ohne
        `## State` im Text bleibt der Kopf, den Stempel setzt nur der Server."""
        change = "updated"
        before: NotesParts | None = None
        parts: NotesParts | None = None
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
                    before = notes.parts
                    parts = replaced_by_text(notes.parts, content)
                    changed = (parts.state, parts.stamp) != (notes.parts.state, notes.parts.stamp)
                    self._notes.save(tx, item.uid, parts, expected=version, state_changed=changed, at=now)
                else:
                    self._documents.update(tx, item.uid, name, content, version, now)
            document = self._existing(tx, item, name)
        self._changed(item.uid, name, change)
        if parts is None:
            return DocumentWrite(document)
        return DocumentWrite(document, state_of(parts), hints(before, parts, rewritten=before is not None))

    def delete_document(self, ref: str, project_uid: str | None, name: str, version: int) -> TrashedDocument:
        """Legt ein Dokument in `version` in den Papierkorb (als Schnappschuss). Mit der Notiz gehen ihr Kopf und die
        Kurzfassung des Items; beim Wiederherstellen kommen sie zurück."""
        with self._database.transaction() as tx:
            item = self._items.resolve(tx, ref, project_uid)
            if item.deleted_at is not None:
                raise ItemDeleted(item.label)
            existing = self._existing(tx, item, name)
            if existing.revision != version:
                raise VersionConflict(
                    "Das Dokument wurde inzwischen geändert",
                    details={"name": name, "expected": version, "current": existing.revision},
                )
            is_notes = existing.kind == NOTES
            snapshot = TrashedDocument(
                str(uuid.uuid4()),
                item.uid,
                name,
                existing.kind,
                existing.content,
                item.summary if is_notes else None,
                self._clock.now(),
            )
            self._trashed.insert(tx, snapshot)
            if is_notes:
                self._notes.delete(tx, item.uid)
                self._drop_summary(tx, item)
            else:
                self._documents.delete(tx, item.uid, name)
        suffix = document_suffix(item.label, name)
        self._changed(item.uid, name, "deleted", f"{item.uid}/{suffix}" if suffix else None)
        return snapshot

    def append_note(
        self,
        ref: str,
        project_uid: str | None,
        topic: str,
        discussed: Sequence[str],
        decided: Sequence[str],
        open_points: Sequence[str],
        summary: str | None,
        state: str | None = None,
        state_version: int | None = None,
    ) -> DocumentWrite:
        """Hängt einen datierten Eintrag an die Notizen; der erste Eintrag legt sie an. Mit `state` wird danach im
        selben Schritt der Kopf ersetzt und gegen den neuen Eintrag gestempelt; gibt es schon einen Kopf, braucht das
        dessen Version `state_version`."""
        with self._database.transaction() as tx:
            item = self._items.resolve(tx, ref, project_uid)
            now = self._clock.now()
            entry = NotesEntry.create(now.date(), topic, discussed, decided, open_points)
            existing = self._notes.get(tx, item.uid)
            name = existing.name if existing else notes_name(item.label)
            self._check_and_summarize(tx, item, summary, add_notes=None if existing else name)
            if existing is None:
                parts = self._with_state(split(append_entry(notes_header(item), entry)), state)
                self._notes.insert(tx, Notes(item.uid, name, parts, 1, 1, now))
                change = "created"
            else:
                self._check_state_version(existing, state, state_version)
                appended = split(append_entry(assemble(title_of(item), existing.parts), entry))
                parts = replace(existing.parts, preamble=appended.preamble, entries=appended.entries)
                parts = self._with_state(parts, state)
                self._notes.save(
                    tx,
                    item.uid,
                    parts,
                    expected=existing.revision,
                    expected_state=state_version if state is not None else None,
                    state_changed=state is not None,
                    at=now,
                )
                change = "updated"
            document = self._existing(tx, item, name)
        self._changed(item.uid, name, change)
        return DocumentWrite(
            document, state_of(parts), hints(existing.parts if existing else None, parts, rewritten=False)
        )

    @staticmethod
    def _with_state(parts: NotesParts, state: str | None) -> NotesParts:
        if state is None:
            return parts
        text = state_text(state)
        if not text:
            raise InvalidInput("Der Kopf ist leer", details={"field": "state"})
        return stamped(replace(parts, state=text))

    @staticmethod
    def _check_state_version(notes: Notes, state: str | None, state_version: int | None) -> None:
        """Ein neuer Kopf ersetzt einen vorhandenen nur in dessen Version."""
        if state is None or not notes.parts.state.strip():
            return
        if state_version is None:
            raise InvalidInput(
                "Die Notes haben schon einen Kopf: `state_version` angeben", details={"field": "state_version"}
            )
        if state_version != notes.state_revision:
            raise VersionConflict("Der Kopf wurde inzwischen geändert", details={"expected": state_version})

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

    def _drop_summary(self, tx: Transaction, item: Item) -> None:
        """Nimmt dem Item die Kurzfassung, die nur mit Notizen Pflicht war: die Notizen sind gerade weg."""
        if item.summary is None:
            return
        updated = replace(item, summary=None, notes=())
        before = self._repository.list_in(tx, [item.project_uid])
        self._rules.check_change(before, [updated if entry.uid == item.uid else entry for entry in before])
        revision = self._registry.bump_revision(tx, item.uid, item.revision)
        self._repository.update(tx, replace(updated, revision=revision))

    def _changed(self, uid: str, name: str, change: str, entry_key: str | None = None) -> None:
        payload: dict[str, Any] = {"uid": uid, "name": name, "change": change}
        if entry_key is not None:
            payload["entry_key"] = entry_key
        self._events.publish(Event(CHANGED_TOPIC, payload, public=True))


def _as_document(item: Item, notes: Notes) -> Document:
    """Die Notizen als zusammengesetzte Datei; die Titelzeile kommt aus dem Item."""
    content = assemble(title_of(item), notes.parts)
    return Document(item.uid, notes.name, NOTES, content, notes.revision, notes.updated_at)

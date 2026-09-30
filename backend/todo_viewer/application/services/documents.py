from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from todo_viewer.domain.documents import (
    DocumentKind,
    DocumentRef,
    NotesEntry,
    content_version,
    item_documents,
    new_document,
    new_notes_file,
    notes_key,
)
from todo_viewer.domain.editing import ChangeSet, EditPlanner, Field, FieldValue
from todo_viewer.domain.errors import DocumentNotFoundError, LifecycleViolationError
from todo_viewer.domain.item import Item
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.source import Source
from todo_viewer.domain.trash import live

from ..ports import BacklogRepository, DocumentStore


@dataclass(frozen=True)
class DocumentResult:
    ref: DocumentRef
    content: str

    @property
    def version(self) -> str:
        return content_version(self.content)


class DocumentService:
    """Notes and specs addressed by item id and document name; keeps the item's Notes/Spec fields in sync."""

    def __init__(self, backlogs: BacklogRepository, documents: DocumentStore, planner: EditPlanner,
                 rules: LifecycleRules, today: Callable[[], date] = date.today):
        self._backlogs = backlogs
        self._documents = documents
        self._planner = planner
        self._rules = rules
        self._today = today

    def read(self, source: Source, item_id: str, name: str) -> DocumentResult:
        ref = self._ref(self._backlogs.get(source, item_id), name)
        return DocumentResult(ref, self._documents.read(source, item_id, ref.key))

    def write(self, source: Source, item_id: str, name: str, content: str, version: str | None,
              summary: str | None = None) -> DocumentResult:
        """Replaces a notes or spec document in `version`, or creates one (`version` None).

        A new document is `<ID>_notes.md` (the item's first notes) or `<ID>_spec[_<topic>].md` and is
        listed in the item's Notes/Spec field; first notes need a summary on the item.
        """
        backlog = self._backlogs.load(source)
        item = self._writable(backlog.find(item_id))
        ref = next((d for d in item_documents(item) if d.name == name), None) or new_document(item, name)
        fields: list[tuple[str, FieldValue]] = []
        if ref not in item_documents(item):
            field, keys = (Field.NOTES, item.notes) if ref.kind is DocumentKind.NOTES else (Field.SPEC, item.spec)
            fields.append((field, (*keys, ref.key)))
        if summary is not None:
            fields.append((Field.SUMMARY, self._planner.normalize(Field.SUMMARY, summary)))
        changes = ChangeSet(set_fields=tuple(fields)) if fields else None
        self._check(backlog.items, item, changes)  # before any document is touched
        self._documents.write(source, item.id, ref.key, content, version)
        if changes:
            self._backlogs.apply(source, item, changes)
        return DocumentResult(ref, content)

    def append_notes(self, source: Source, item_id: str, topic: str, discussed: Sequence[str],
                     decided: Sequence[str], open_points: Sequence[str], summary: str | None) -> DocumentResult:
        """Appends a dated entry; the first entry creates the file and needs a summary on the item."""
        backlog = self._backlogs.load(source)
        item = self._writable(backlog.find(item_id))
        entry = NotesEntry.create(self._today().isoformat(), topic, discussed, decided, open_points)
        key = notes_key(item)
        fields: list[tuple[str, FieldValue]] = []
        if not item.notes:
            fields.append((Field.NOTES, (key,)))
        if summary is not None:
            fields.append((Field.SUMMARY, self._planner.normalize(Field.SUMMARY, summary)))
        changes = ChangeSet(set_fields=tuple(fields)) if fields else None
        self._check(backlog.items, item, changes)  # before any document is touched
        content = self._documents.append(source, item.id, key, entry.render(), header=new_notes_file(item))
        if changes:
            self._backlogs.apply(source, item, changes)
        return DocumentResult(DocumentRef(key.rsplit("/", 1)[-1], DocumentKind.NOTES, key), content)

    def _check(self, items: Sequence[Item], item: Item, changes: ChangeSet | None) -> None:
        if changes is not None:
            after = changes.applied_to(item)
            in_use = live(items)
            self._rules.check_change(in_use, [after if i is item else i for i in in_use])

    @staticmethod
    def _writable(item: Item) -> Item:
        if item.deleted:
            raise LifecycleViolationError("item_deleted", item.id)
        return item

    @staticmethod
    def _ref(item: Item, name: str) -> DocumentRef:
        ref = next((d for d in item_documents(item) if d.name == name), None)
        if ref is None:
            raise DocumentNotFoundError(name)
        return ref

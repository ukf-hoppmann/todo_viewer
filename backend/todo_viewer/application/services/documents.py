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
    new_notes_file,
    notes_path,
    spec_path,
)
from todo_viewer.domain.editing import ChangeSet, EditPlanner, Field, FieldValue
from todo_viewer.domain.errors import DocumentNotFoundError, LifecycleViolationError, NotEditableError
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
        return DocumentResult(ref, self._documents.read(source, ref.path))

    def write_spec(self, source: Source, item_id: str, name: str, content: str,
                   version: str | None) -> DocumentResult:
        """Replaces a spec in `version`, or creates a new one (`version` None) and lists it in the item's Spec."""
        backlog = self._backlogs.load(source)
        item = self._writable(backlog.find(item_id))
        known = next((d for d in item_documents(item) if d.name == name), None)
        if known is not None and known.kind is not DocumentKind.SPEC:
            raise NotEditableError(name)
        path = known.path if known else spec_path(item, name)
        changes = None if known else ChangeSet(set_fields=((Field.SPEC, (*item.spec, path)),))
        self._check(backlog.items, item, changes)
        self._documents.write(source, path, content, version)
        if changes:
            self._backlogs.apply(source, item, changes)
        return DocumentResult(DocumentRef(name, DocumentKind.SPEC, path), content)

    def append_notes(self, source: Source, item_id: str, topic: str, discussed: Sequence[str],
                     decided: Sequence[str], open_points: Sequence[str], summary: str | None) -> DocumentResult:
        """Appends a dated entry; the first entry creates the file and needs a summary on the item."""
        backlog = self._backlogs.load(source)
        item = self._writable(backlog.find(item_id))
        entry = NotesEntry.create(self._today().isoformat(), topic, discussed, decided, open_points)
        path = notes_path(item)
        fields: list[tuple[str, FieldValue]] = []
        if not item.notes:
            fields.append((Field.NOTES, (path,)))
        if summary is not None:
            fields.append((Field.SUMMARY, self._planner.normalize(Field.SUMMARY, summary)))
        changes = ChangeSet(set_fields=tuple(fields)) if fields else None
        self._check(backlog.items, item, changes)  # before any file is touched
        content = self._documents.append(source, path, entry.render(), header=new_notes_file(item))
        if changes:
            self._backlogs.apply(source, item, changes)
        return DocumentResult(DocumentRef(path.rsplit("/", 1)[-1], DocumentKind.NOTES, path), content)

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

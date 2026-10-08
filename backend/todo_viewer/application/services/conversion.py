from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date

from todo_viewer.domain.conversion import (
    DEMOTE_RESOLUTION,
    check_demote,
    promotion_entry,
    promotion_fields,
    promotion_marker,
    renamed_document,
    without_header,
)
from todo_viewer.domain.documents import DocumentKind, item_documents, new_notes_file
from todo_viewer.domain.editing import Field
from todo_viewer.domain.errors import (
    ConversionRefusedError,
    ItemNotFoundError,
    LifecycleViolationError,
    SourceGoneError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Status
from todo_viewer.domain.note_lifecycle import check_editable
from todo_viewer.domain.notes import FINISHED_STATUSES, LinkRole, LinkTarget, NoteStatus, TargetKind
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, SourceRepository
from .documents import DocumentService
from .items import ItemResult, ItemService
from .note_documents import NoteDocumentService
from .notes import NoteService, NoteView


@dataclass(frozen=True)
class Promoted:
    note: NoteView
    item: ItemResult


@dataclass(frozen=True)
class Demoted:
    item: ItemResult
    note: NoteView


class ConversionService:
    """Turns a note into an item and an open item back into a note.

    Item and note live in different stores without a common transaction, so the side that is new is created first
    and the `origin` link follows at once: it proves the first step ran. Every later step checks what is there
    already, so repeating a call that stopped halfway finishes the work and never creates a second item or note.
    """

    def __init__(self, items: ItemService, documents: DocumentService, notes: NoteService,
                 note_documents: NoteDocumentService, backlogs: BacklogRepository, sources: SourceRepository,
                 today: Callable[[], date] = date.today):
        self._items = items
        self._documents = documents
        self._notes = notes
        self._note_documents = note_documents
        self._backlogs = backlogs
        self._sources = sources
        self._today = today

    # --- note -> item ---

    def promote(self, project: str, label: str, version: str, item_type: str,
                given: Mapping[str, object]) -> Promoted:
        """Creates the item in the note's project, takes the note's texts over, and closes the note as promoted.

        `given` are the item's fields (`area`, `goal`, `completion_criteria`, optionally `title`, `summary`, `parent`,
        …); the item is created by `ItemService`, so every backlog check applies.
        """
        note = self._notes.show(project, label).note
        check_editable(note)
        if note.version != version:
            raise VersionConflictError(label)
        source = self._source(project)
        item_id = self._origin_of(project, label)
        if item_id is None:
            item_id = self._items.create(source, item_type, promotion_fields(note.summary, given)).item.id
            self._notes.add_link(project, label, LinkTarget(TargetKind.ITEM, project, item_id), LinkRole.ORIGIN)
        elif self._missing(source, item_id):
            raise ConversionRefusedError("promote_origin_missing", label, (item_id,))
        self._take_over_into_item(source, item_id, project, label, note.body)
        view = self._notes.finish(project, label, note.version, NoteStatus.PROMOTED)
        return Promoted(view, self._items.get(source, item_id))

    def _origin_of(self, project: str, label: str) -> str | None:
        link = next((link for link in self._notes.links_of(project, label)
                     if link.role is LinkRole.ORIGIN and link.target.kind is TargetKind.ITEM), None)
        return None if link is None else link.target.label

    def _missing(self, source: Source, item_id: str) -> bool:
        try:
            return self._items.get(source, item_id).item.deleted is not None
        except ItemNotFoundError:
            return True

    def _take_over_into_item(self, source: Source, item_id: str, project: str, label: str, body: str | None) -> None:
        """The long text and the notes of the note become one entry in the item's notes; specs keep their name
        with the item's id. What the item has already is left alone."""
        item = self._items.get(source, item_id).item
        documents = self._note_documents.names(project, label)
        notes_name = f"{item_id}_notes.md" if not item.notes else item.notes[0].rsplit("/", 1)[-1]
        current = self._documents.read(source, item_id, notes_name) if item.notes else None
        if current is None or promotion_marker(label) not in current.content:
            entry = promotion_entry(self._today().isoformat(), label, body).render()
            for name, kind in documents:
                if kind is DocumentKind.NOTES:
                    entry += "\n" + without_header(self._note_documents.read(project, label, name).content) + "\n"
            content = (f"{current.content.rstrip()}\n\n{entry}" if current is not None
                       else f"{new_notes_file(item)}\n{entry}")
            self._documents.write(source, item_id, notes_name, content, None if current is None else current.version)
        present = {ref.name for ref in item_documents(item)}
        for name, kind in documents:
            target = renamed_document(name, label, item_id)
            if kind is DocumentKind.SPEC and target is not None and target not in present:
                self._documents.write(source, item_id, target, self._note_documents.read(project, label, name).content,
                                      None)

    # --- item -> note ---

    def demote(self, source: Source, item_id: str, version: str, topic: str | None = None) -> Demoted:
        """Creates a note from an open item, moves its notes and specs over, and closes the item as rejected."""
        backlog = self._backlogs.load(source)
        item = backlog.find(item_id)
        if item.version != version:
            raise VersionConflictError(item_id)
        if item.deleted is not None:
            raise LifecycleViolationError("item_deleted", item_id)
        check_demote(item, backlog.items)
        unnamed = tuple(ref.name for ref in item_documents(item) if renamed_document(ref.name, item_id, "X") is None)
        if unnamed:
            raise ConversionRefusedError("demote_document_name", item_id, unnamed)
        project = source.project
        label = self._open_note_from(project, item_id)
        if label is None:
            label = self._notes.create(project, item.title, item.summary, topic).note.label
            self._notes.add_link(project, label, LinkTarget(TargetKind.ITEM, project, item_id), LinkRole.ORIGIN)
        self._take_over_into_note(source, item, project, label)
        edited = self._items.edit(source, item_id, version, {Field.STATUS: Status.REJECTED}, DEMOTE_RESOLUTION)
        return Demoted(edited, self._notes.show(project, label))

    def _open_note_from(self, project: str, item_id: str) -> str | None:
        """The note an earlier, unfinished demotion of this item created. A note that is closed was promoted from
        the item and does not count."""
        target = LinkTarget(TargetKind.ITEM, project, item_id)
        for linked in self._notes.notes_linking_to(target):
            note = linked.view.note
            if linked.link.role is LinkRole.ORIGIN and note.status not in FINISHED_STATUSES and not note.archived:
                return note.label
        return None

    def _take_over_into_note(self, source: Source, item: Item, project: str, label: str) -> None:
        present = {name for name, _ in self._note_documents.names(project, label)}
        for ref in item_documents(item):
            target = renamed_document(ref.name, item.id, label)
            if target is not None and target not in present:
                self._note_documents.write(project, label, target, self._documents.read(source, item.id, ref.name)
                                           .content, None)

    def _source(self, project: str) -> Source:
        found = next((s for s in self._sources.all() if s.project == project), None)
        if found is None:
            raise SourceGoneError()
        return found

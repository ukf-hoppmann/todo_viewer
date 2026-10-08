from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from todo_viewer.domain.documents import DocumentKind, NotesEntry, content_version
from todo_viewer.domain.note_lifecycle import check_editable
from todo_viewer.domain.notes import check_note_document_name, note_document_kind

from ..ports import NoteDocumentStore, NoteRepository


@dataclass(frozen=True)
class NoteDocument:
    name: str
    kind: DocumentKind
    content: str

    @property
    def version(self) -> str:
        return content_version(self.content)


class NoteDocumentService:
    """Notes and specs of a note, addressed by project, label, and document name.

    Reading works for every note, also for closed ones and those in the trash; writing needs an open note.
    """

    def __init__(self, notes: NoteRepository, documents: NoteDocumentStore, today: Callable[[], date] = date.today):
        self._notes = notes
        self._documents = documents
        self._today = today

    def names(self, project: str, label: str) -> list[tuple[str, DocumentKind]]:
        self._notes.get_note(project, label)
        return [(name, note_document_kind(name)) for name in self._documents.names(project, label)]

    def read(self, project: str, label: str, name: str) -> NoteDocument:
        self._notes.get_note(project, label)
        return NoteDocument(name, note_document_kind(name), self._documents.read(project, label, name))

    def write(self, project: str, label: str, name: str, content: str, version: str | None) -> NoteDocument:
        """Replaces a document still at `version`, or creates it (`version` None); else version_conflict."""
        check_note_document_name(label, name)
        check_editable(self._notes.get_note(project, label))
        self._documents.write(project, label, name, content, version)
        return NoteDocument(name, note_document_kind(name), content)

    def append_notes(self, project: str, label: str, topic: str, discussed: Sequence[str], decided: Sequence[str],
                     open_points: Sequence[str]) -> NoteDocument:
        """Appends a dated entry to `<LABEL>_notes.md`; the first entry creates the file."""
        note = self._notes.get_note(project, label)
        check_editable(note)
        entry = NotesEntry.create(self._today().isoformat(), topic, discussed, decided, open_points)
        name = f"{label}_notes.md"
        content = self._documents.append(project, label, name, entry.render(), header=f"# {label} — {note.summary}\n")
        return NoteDocument(name, DocumentKind.NOTES, content)

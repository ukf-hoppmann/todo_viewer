from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import DocumentNotFoundError, NoteFormatError, SyncSourceInvalidError
from todo_viewer.domain.notes import LinkRole, LinkTarget, NewTrigger, Note, TargetKind, Topic
from todo_viewer.domain.notes_markdown import (
    ParsedNote,
    TopicLine,
    parse_counters,
    parse_note,
    parse_topics,
    render_counters,
    render_topics,
    to_parsed,
)
from todo_viewer.domain.notes_sync import (
    DOCUMENT,
    NOTE,
    TOPIC,
    NotesSide,
    NoteUnit,
    counters_floor,
    is_labelless,
    label_number,
    note_unit,
    renamed_document,
    rewritten_note,
)
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import Side, Transfer

from ..ports import NoteDocumentStore, NoteRepository, NotesMirror

_NOTE_FILE = re.compile(r"^(NOTE-\d+|new-[A-Za-z0-9.-]+)\.md$")
_DOCUMENT_FILE = re.compile(r"^(NOTE-\d+|new-[A-Za-z0-9.-]+)_(?:notes|spec(?:_[A-Za-z0-9-]+)?)\.md$")
KINDS = (TOPIC, NOTE, DOCUMENT)


@dataclass(frozen=True)
class MarkdownNotes:
    """The notes folder as it was read: parsed, and the raw files (to name what a write replaces)."""

    side: NotesSide
    files: Mapping[str, str]


class NotesSync:
    """Reads the notes of both sides and carries entries over; the sync (`SyncService`) decides which.

    Notes live in the database whatever the primary source of the project is; the notes folder is always the mirror.
    The database gives labels: a note or topic written in the files without one gets the next free label of the
    project when it is imported, references to it are rewritten, and its file is renamed.
    """

    def __init__(self, notes: NoteRepository, documents: NoteDocumentStore, mirror: NotesMirror):
        self._notes = notes
        self._documents = documents
        self._mirror = mirror

    # --- reading ---

    def read_database(self, project: str) -> NotesSide:
        topics = {t.label: TopicLine(t.label, t.name, t.parent, t.due_at, t.created, t.deleted)
                  for t in self._notes.list_topics(project, include_deleted=True)}
        units: dict[str, NoteUnit] = {}
        documents: dict[tuple[str, str], str] = {}
        for note in self._notes.list_notes(project, include_deleted=True):
            units[note.label] = note_unit(note.label, to_parsed(note, self._notes.triggers_of(project, note.label),
                                                                 self._notes.links_of(project, note.label)))
            for name in self._documents.names(project, note.label):
                documents[(note.label, name)] = self._documents.read(project, note.label, name)
        return NotesSide(topics, units, documents, self._notes.counters(project))

    def read_markdown(self, markdown: Source) -> MarkdownNotes:
        """Parses the notes folder; a file that does not follow the format stops the sync (`note_format`)."""
        files = self._mirror.read(markdown)
        try:
            topics = {t.key: t for t in parse_topics(files["topics.md"])} if "topics.md" in files else {}
            counters = parse_counters(files["counters.md"]) if "counters.md" in files else {}
            units: dict[str, NoteUnit] = {}
            documents: dict[tuple[str, str], str] = {}
            for name, text in files.items():
                found = _NOTE_FILE.match(name)
                if found:
                    stem = found.group(1)
                    parsed = parse_note(text, name)
                    if parsed.label is None and not stem.startswith("new-"):
                        raise NoteFormatError("a note without a label belongs in a file new-<name>.md", 1, name)
                    if parsed.label is not None and parsed.label != stem:
                        raise NoteFormatError(f"the file is named {stem} but the note {parsed.label}", 1, name)
                    units[stem] = note_unit(stem, parsed)
                    continue
                found = _DOCUMENT_FILE.match(name)
                if found:
                    documents[(found.group(1), name)] = text
        except NoteFormatError as error:
            raise SyncSourceInvalidError("note_format", error.message) from error
        return MarkdownNotes(NotesSide(topics, units, documents, counters), files)

    # --- applying ---

    def apply(self, project: str, markdown: Source, database: NotesSide, found: MarkdownNotes,
              steps: Sequence[Transfer], files_may_change: bool) -> list[Transfer]:
        """Carries over the steps for topics, notes, and note documents; returns those done.

        An entry without a label is imported only if the files may change too (its file is renamed afterwards).
        """
        steps = [t for t in steps if t.key.kind in KINDS]
        if not files_may_change:
            steps = [t for t in steps if t.to is not Side.DATABASE or not is_labelless(t.key.label)]
        to_database = [t for t in steps if t.to is Side.DATABASE]
        to_markdown = [t for t in steps if t.to is Side.MARKDOWN]
        topic_labels: dict[str, str] = {}
        note_labels: dict[str, str] = {}
        if to_database:
            self._into_database(project, database, found, to_database, topic_labels, note_labels)
        if to_markdown or topic_labels or note_labels:
            self._into_markdown(project, markdown, found, to_markdown, to_database, topic_labels, note_labels)
        return steps

    def _into_database(self, project: str, database: NotesSide, found: MarkdownNotes, steps: Sequence[Transfer],
                       topic_labels: dict[str, str], note_labels: dict[str, str]) -> None:
        side = found.side
        for kind, minimum in counters_floor(side).items():
            self._notes.raise_counter(project, kind, minimum)
        copies = [t for t in steps if not t.delete]
        topic_copies = {t.key.label for t in copies if t.key.kind == TOPIC}
        note_copies = {t.key.label for t in copies if t.key.kind == NOTE}
        for key in side.topics:  # in the order of the file
            if key in topic_copies and is_labelless(key):
                topic_labels[key] = self._notes.next_label(project, "topic")
        for key in sorted(note_copies):
            if is_labelless(key):
                note_labels[key] = self._notes.next_label(project, "note")
        known = set(database.topics)
        for key, line in side.topics.items():
            if key not in topic_copies:
                continue
            label = topic_labels.get(key, key)
            parent = topic_labels.get(line.parent or "", line.parent)
            self._notes.store_topic(project, Topic(project, label, line.name, parent if parent in known else None,
                                                   line.due_at, line.created, line.deleted))
            known.add(label)
        for key in sorted(note_copies):
            label = note_labels.get(key, key)
            parsed = rewritten_note(side.notes[key].parsed, label, topic_labels, note_labels)
            if parsed.topic and parsed.topic not in known:
                parsed = _replace_topic(parsed, None)
            self._store_note(project, parsed)
        stepped = {(t.key.label, t.key.name) for t in copies if t.key.kind == DOCUMENT}
        # a note that is new here (or restored) brings all its documents; the others are copied one by one
        arriving = {(key, name) for (key, name) in side.documents if key in note_copies and key not in database.notes}
        for key, name in sorted(stepped | arriving):
            label = note_labels.get(key, key)
            if key in note_copies or key in database.notes or label in database.notes:
                self._write_document(project, label, renamed_document(name, key, label), side.documents[(key, name)])
        for step in steps:
            if not step.delete:
                continue
            if step.key.kind == NOTE:
                self._notes.purge_note(project, step.key.label)
            elif step.key.kind == DOCUMENT:
                self._documents.delete_document(project, step.key.label, step.key.name)
            else:
                self._notes.purge_topics(project, [step.key.label], [])

    def _store_note(self, project: str, parsed: ParsedNote) -> None:
        label = parsed.label
        assert label is not None
        note = Note(project, label, parsed.summary, parsed.body, parsed.status, parsed.topic, parsed.review_at,
                    parsed.mode, parsed.created, parsed.updated, parsed.archived, parsed.deleted)
        links = [(LinkTarget(link.target.kind, link.target.project or project, link.target.label), link.role)
                 for link in parsed.links if link.role is not LinkRole.TRIGGER]
        triggers = [NewTrigger(t.kind, t.at, None if t.target is None else LinkTarget(
            TargetKind.ITEM, t.target.project or project, t.target.label), t.status, t.fired_at, t.already_met)
            for t in parsed.triggers]
        self._notes.store_note(project, note, links, triggers)
        self._notes.raise_counter(project, "note", label_number(label))

    def _write_document(self, project: str, label: str, name: str, text: str) -> None:
        try:
            current: str | None = self._documents.read(project, label, name)
        except DocumentNotFoundError:
            current = None
        self._documents.write(project, label, name, text, None if current is None else content_version(current))

    def _into_markdown(self, project: str, markdown: Source, found: MarkdownNotes, steps: Sequence[Transfer],
                       imported: Sequence[Transfer], topic_labels: Mapping[str, str],
                       note_labels: Mapping[str, str]) -> None:
        files = found.files
        now = self.read_database(project)  # the database as it is now: what the files must say

        def expected(name: str) -> str | None:
            return content_version(files[name]) if name in files else None

        def write(name: str, text: str) -> None:
            self._mirror.write(markdown, name, text, expected(name))

        def remove(name: str) -> None:
            if name in files:
                self._mirror.delete(markdown, name, content_version(files[name]))

        def prefixed(key: str) -> list[str]:
            return [n for n in files if n.startswith(f"{key}_")]

        written: set[str] = set()
        for step in steps:
            key, name = step.key.label, step.key.name
            if step.key.kind == NOTE and not step.delete:
                write(f"{key}.md", now.notes[key].text)
                written.add(f"{key}.md")
                if f"{key}.md" not in files:  # a note that is new in the folder (or restored) brings its documents
                    for (owner, doc), text in now.documents.items():
                        if owner == key and doc not in files and doc not in written:
                            write(doc, text)
                            written.add(doc)
            elif step.key.kind == DOCUMENT and not step.delete:
                if name not in written:
                    write(name, now.documents[(key, name)])
                    written.add(name)
            elif step.key.kind == NOTE:
                remove(f"{key}.md")
                for doc in prefixed(key):
                    remove(doc)
            elif step.key.kind == DOCUMENT:
                remove(name)
        for key, label in note_labels.items():  # a note given its label: the file is renamed, its documents too
            write(f"{label}.md", now.notes[label].text)
            remove(f"{key}.md")
            for doc in prefixed(key):
                new = renamed_document(doc, key, label)
                write(new, now.documents[(label, new)])
                remove(doc)
        for step in imported:  # a note whose references were rewritten differs from its file now
            key = step.key.label
            if step.key.kind == NOTE and not step.delete and key not in note_labels and f"{key}.md" in files \
                    and now.notes[key].text != found.side.notes[key].text:
                write(f"{key}.md", now.notes[key].text)
        topic_steps = [t for t in steps if t.key.kind == TOPIC]
        if topic_steps or topic_labels:
            self._write_topics(markdown, found, now, topic_steps, topic_labels, write)
        counters = self._notes.counters(project)
        if (steps or note_labels or topic_labels) and counters and counters != found.side.counters:
            write("counters.md", render_counters(counters, _newline(files.get("counters.md", ""))))

    def _write_topics(self, markdown: Source, found: MarkdownNotes, now: NotesSide, steps: Sequence[Transfer],
                      topic_labels: Mapping[str, str], write: Callable[[str, str], None]) -> None:
        gone = {t.key.label for t in steps if t.delete}
        copied = {t.key.label for t in steps if not t.delete}
        lines: list[TopicLine] = []
        for key, line in found.side.topics.items():
            if key in gone or key in topic_labels:
                continue
            lines.append(now.topics[key] if key in copied else line)
        for key in copied:
            if key not in found.side.topics:
                lines.append(now.topics[key])
        lines += [now.topics[label] for label in topic_labels.values()]
        lines = [_with_parent(line, topic_labels) for line in lines]
        write("topics.md", render_topics(lines, _newline(found.files.get("topics.md", ""))))


def _with_parent(line: TopicLine, mapping: Mapping[str, str]) -> TopicLine:
    if line.parent is not None and line.parent in mapping:
        return TopicLine(line.label, line.name, mapping[line.parent], line.due_at, line.created, line.deleted)
    return line


def _replace_topic(parsed: ParsedNote, topic: str | None) -> ParsedNote:
    return dataclasses.replace(parsed, topic=topic)


def _newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


__all__ = ["KINDS", "MarkdownNotes", "NotesSync"]

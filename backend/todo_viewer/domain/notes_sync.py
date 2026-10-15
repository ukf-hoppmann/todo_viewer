"""Notes, topics, and the documents of notes in the sync (STORY-047): what is compared and how labels are given.

Pure functions. A side (the database or the notes folder) is read into a `NotesSide` first; this module turns two of
them into the entries the sync classifies, and rewrites what a label given by the database changes in the files.
"""
from __future__ import annotations

import dataclasses
import re
from collections.abc import Mapping
from dataclasses import dataclass

from .documents import content_version
from .notes import TargetKind
from .notes_markdown import (
    NEW_TOPIC,
    ParsedLink,
    ParsedNote,
    ParsedTarget,
    TopicLine,
    moment_text,
    render_parsed,
    trigger_line,
)
from .sync import EntryKey, ExtraEntry, SideView

TOPIC, NOTE, DOCUMENT = "topic", "note", "note_document"


@dataclass(frozen=True)
class NoteUnit:
    """A note on one side in the form that is compared: its file text, normalized to `\\n`, and what it says."""

    key: str  # its label, or the name of its file without `.md` while it has no label (`new-idea`)
    parsed: ParsedNote
    text: str

    @property
    def version(self) -> str:
        return content_version(self.text)


def note_unit(key: str, parsed: ParsedNote) -> NoteUnit:
    return NoteUnit(key, parsed, render_parsed(parsed, "\n"))


@dataclass(frozen=True)
class NotesSide:
    """The notes of one side: topics and notes by key (label, or a name while without label), documents by note key
    and name, and the label counters."""

    topics: Mapping[str, TopicLine]
    notes: Mapping[str, NoteUnit]
    documents: Mapping[tuple[str, str], str]
    counters: Mapping[str, int]


def topic_version(topic: TopicLine) -> str:
    return content_version("\0".join([topic.label or "", topic.name, topic.parent or "", moment_text(topic.due_at),
                                      moment_text(topic.created), moment_text(topic.deleted)]))


def side_versions(side: NotesSide) -> dict[EntryKey, str]:
    """The version of every entry of the side, to remember what both sides agreed on."""
    versions = {EntryKey(TOPIC, key): topic_version(t) for key, t in side.topics.items()}
    versions.update({EntryKey(NOTE, key): n.version for key, n in side.notes.items()})
    versions.update({EntryKey(DOCUMENT, key, name): content_version(text)
                     for (key, name), text in side.documents.items()})
    return versions


def extra_entries(database: NotesSide, markdown: NotesSide) -> list[ExtraEntry]:
    """Every topic, note, and note document that either side has, with its version and (for conflicts) its fields."""
    entries: list[ExtraEntry] = []
    for key in _union(database.topics, markdown.topics):
        d_topic, m_topic = database.topics.get(key), markdown.topics.get(key)
        entries.append(ExtraEntry(
            EntryKey(TOPIC, key), (d_topic or m_topic).name,  # type: ignore[union-attr]
            None if d_topic is None else topic_version(d_topic), None if m_topic is None else topic_version(m_topic),
            None if d_topic is None else SideView(fields=topic_fields(d_topic)),
            None if m_topic is None else SideView(fields=topic_fields(m_topic))))
    for key in _union(database.notes, markdown.notes):
        d_note, m_note = database.notes.get(key), markdown.notes.get(key)
        entries.append(ExtraEntry(
            EntryKey(NOTE, key), (d_note or m_note).parsed.summary,  # type: ignore[union-attr]
            None if d_note is None else d_note.version, None if m_note is None else m_note.version,
            None if d_note is None else SideView(fields=note_fields(d_note.parsed)),
            None if m_note is None else SideView(fields=note_fields(m_note.parsed))))
    for owner, name in sorted({k for k in (*database.documents, *markdown.documents)}):
        d_text, m_text = database.documents.get((owner, name)), markdown.documents.get((owner, name))
        note = database.notes.get(owner) or markdown.notes.get(owner)
        entries.append(ExtraEntry(
            EntryKey(DOCUMENT, owner, name), note.parsed.summary if note else owner,
            None if d_text is None else content_version(d_text), None if m_text is None else content_version(m_text),
            None if d_text is None else SideView(text=d_text), None if m_text is None else SideView(text=m_text),
            parent=EntryKey(NOTE, owner)))
    return entries


def _union(*sides: Mapping[str, object]) -> list[str]:
    keys: list[str] = []
    for side in sides:
        keys += [k for k in side if k not in keys]
    return keys


def note_fields(note: ParsedNote) -> tuple[tuple[str, str], ...]:
    """All fields of a note as name and text, for the side by side comparison of a conflict."""
    triggers = "\n".join(trigger_line(t)[2:] for t in note.triggers)
    links = "\n".join(f"{link.role.value} {link.target}" for link in note.links)
    return (("summary", note.summary), ("status", note.status.value), ("topic", note.topic or ""),
            ("review", moment_text(note.review_at)), ("mode", note.mode.value),
            ("created", moment_text(note.created)), ("updated", moment_text(note.updated)),
            ("archived", "true" if note.archived else "false"), ("deleted", moment_text(note.deleted)),
            ("triggers", triggers), ("links", links), ("body", note.body or ""))


def topic_fields(topic: TopicLine) -> tuple[tuple[str, str], ...]:
    return (("name", topic.name), ("parent", topic.parent or ""), ("due", moment_text(topic.due_at)),
            ("created", moment_text(topic.created)), ("deleted", moment_text(topic.deleted)))


# --- labels ---

def label_number(label: str) -> int:
    """The number of a label (`NOTE-015` is 15); 0 for something that is no label (`new-idea`, `new:Name`)."""
    found = re.fullmatch(r"[A-Za-z]+-(\d+)", label)
    return int(found.group(1)) if found else 0


def counters_floor(side: NotesSide) -> dict[str, int]:
    """The least value the counters must have: the side's own counters and the highest label it uses."""
    floor = {kind: number for kind, number in side.counters.items()}
    for kind, keys in (("note", side.notes), ("topic", side.topics)):
        highest = max((label_number(k) for k in keys), default=0)
        if highest:
            floor[kind] = max(floor.get(kind, 0), highest)
    return floor


def rewritten_note(note: ParsedNote, label: str, topic_labels: Mapping[str, str],
                   note_labels: Mapping[str, str]) -> ParsedNote:
    """The note with `label` and with every reference to a topic or note that just got its label rewritten."""
    links = tuple(
        ParsedLink(link.role, ParsedTarget(link.target.kind, note_labels.get(link.target.label, link.target.label))
                   if link.target.kind is TargetKind.NOTE else link.target)
        for link in note.links)
    return dataclasses.replace(note, label=label, links=links,
                               topic=topic_labels.get(note.topic, note.topic) if note.topic else None)


def renamed_document(name: str, old_key: str, label: str) -> str:
    """`new-idea_notes.md` becomes `NOTE-012_notes.md` once the note has its label."""
    return label + name[len(old_key):] if name.startswith(old_key) else name


def is_labelless(key: str) -> bool:
    return key.startswith(("new-", NEW_TOPIC))


__all__ = [
    "DOCUMENT",
    "NOTE",
    "TOPIC",
    "NoteUnit",
    "NotesSide",
    "counters_floor",
    "extra_entries",
    "is_labelless",
    "label_number",
    "note_fields",
    "note_unit",
    "renamed_document",
    "rewritten_note",
    "side_versions",
    "topic_fields",
    "topic_version",
]

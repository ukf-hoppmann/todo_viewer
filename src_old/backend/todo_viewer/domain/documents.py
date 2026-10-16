"""Notes and spec documents of an item: names, the notes entry format, and content versions.

Documents are addressed by item id and name (e.g. `STORY-003_spec.md`). Where they are stored is up to
the storage adapter. An item lists its documents by name in its Notes/Spec fields.
"""
from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from .errors import InvalidValueError, ValueRequiredError
from .item import Item


class DocumentKind(StrEnum):
    NOTES = "notes"
    SPEC = "spec"


@dataclass(frozen=True)
class DocumentRef:
    name: str  # as shown to clients
    kind: DocumentKind
    key: str  # as listed in the item's Notes/Spec field and passed to the document store


def item_documents(item: Item) -> list[DocumentRef]:
    return [DocumentRef(_name(k), DocumentKind.NOTES, k) for k in item.notes] + \
        [DocumentRef(_name(k), DocumentKind.SPEC, k) for k in item.spec]


def notes_key(item: Item) -> str:
    """Where notes go: the item's notes document, or `<ID>_notes.md` for the first entry."""
    return item.notes[0] if item.notes else f"{item.id}_notes.md"


def check_spec_name(item: Item, name: str) -> str:
    """Names of new specs are `<ID>_spec.md` or `<ID>_spec_<topic>.md`."""
    if not re.fullmatch(rf"{re.escape(item.id)}_spec(_[A-Za-z0-9-]+)?\.md", name):
        raise InvalidValueError("name", (f"{item.id}_spec.md", f"{item.id}_spec_<topic>.md"))
    return name


def new_document(item: Item, name: str) -> DocumentRef:
    """A new document: `<ID>_notes.md` for the first notes, otherwise a spec name."""
    if name == f"{item.id}_notes.md" and not item.notes:
        return DocumentRef(name, DocumentKind.NOTES, name)
    return DocumentRef(name, DocumentKind.SPEC, check_spec_name(item, name))


def new_notes_file(item: Item) -> str:
    return f"# {item.id} — {item.title}\n"


def content_version(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class NotesEntry:
    """One dated entry of a notes file with the format's Discussed/Decided/Open sections."""

    date: str
    topic: str
    discussed: tuple[str, ...]
    decided: tuple[str, ...]
    open: tuple[str, ...]

    @classmethod
    def create(cls, date: str, topic: str, discussed: Sequence[str], decided: Sequence[str],
               open: Sequence[str]) -> NotesEntry:
        entry = cls(date, _line(topic), _bullets(discussed), _bullets(decided), _bullets(open))
        if not entry.topic:
            raise ValueRequiredError("topic")
        if not (entry.discussed or entry.decided or entry.open):
            raise ValueRequiredError("discussed/decided/open")
        return entry

    def render(self) -> str:
        parts = [f"## {self.date} — {self.topic}\n"]
        for heading, bullets in (("Discussed", self.discussed), ("Decided", self.decided), ("Open", self.open)):
            if bullets:
                parts.append(f"### {heading}\n\n" + "".join(f"- {b}\n" for b in bullets))
        return "\n".join(parts)


def _name(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _line(text: str) -> str:
    return " ".join(text.split())


def _bullets(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(b for b in (_line(v) for v in values) if b)

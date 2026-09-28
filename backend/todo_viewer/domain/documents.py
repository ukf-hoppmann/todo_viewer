"""Notes and spec documents of an item: names, the notes entry format, and content versions.

Documents are addressed by item id and name (the file name, e.g. `STORY-003_spec.md`);
the backlog folder layout `items/<ID>/` is part of the backlog format.
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
    name: str
    kind: DocumentKind
    path: str  # relative to the backlog folder, as written in the item's Notes/Spec field


def item_documents(item: Item) -> list[DocumentRef]:
    return [DocumentRef(_name(p), DocumentKind.NOTES, p) for p in item.notes] + \
        [DocumentRef(_name(p), DocumentKind.SPEC, p) for p in item.spec]


def notes_path(item: Item) -> str:
    """Where notes go: the item's notes file, or `items/<ID>/<ID>_notes.md` for the first entry."""
    return item.notes[0] if item.notes else f"items/{item.id}/{item.id}_notes.md"


def spec_path(item: Item, name: str) -> str:
    """Path of a new spec document; names are `<ID>_spec.md` or `<ID>_spec_<topic>.md`."""
    if not re.fullmatch(rf"{re.escape(item.id)}_spec(_[A-Za-z0-9-]+)?\.md", name):
        raise InvalidValueError("name", (f"{item.id}_spec.md", f"{item.id}_spec_<topic>.md"))
    return f"items/{item.id}/{name}"


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

"""Notizen und Specs eines Items: Namen, Format des Notiz-Eintrags, Umbenennen beim Typwechsel."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from viewer.core.domain.errors import DomainError, InvalidInput
from viewer.plugins.backlog.domain.editing import ValueRequired, rewrite_labels
from viewer.plugins.backlog.domain.model import Item

NOTES = "notes"
SPEC = "spec"


class DocumentExists(DomainError):
    code = "document_exists"


class DocumentNotFound(DomainError):
    code = "document_not_found"


def notes_name(label: str) -> str:
    return f"{label}_notes.md"


def spec_name_pattern(label: str) -> re.Pattern[str]:
    return re.compile(rf"{re.escape(label)}_spec(_[A-Za-z0-9-]+)?\.md")


def new_document_kind(item: Item, name: str) -> str:
    """Art eines neuen Dokuments: `<LABEL>_notes.md` (die erste Notiz) oder `<LABEL>_spec[_<thema>].md`."""
    if name == notes_name(item.label) and not item.notes:
        return NOTES
    if spec_name_pattern(item.label).fullmatch(name):
        return SPEC
    raise InvalidInput(
        f"'{name}' ist kein gültiger Name für ein neues Dokument",
        details={
            "field": "name",
            "allowed": [notes_name(item.label), f"{item.label}_spec.md", f"{item.label}_spec_<thema>.md"],
        },
    )


def notes_header(item: Item) -> str:
    return f"# {item.label} — {item.title}\n"


def _line(text: str) -> str:
    return " ".join(text.split())


def _bullets(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(bullet for bullet in (_line(value) for value in values) if bullet)


@dataclass(frozen=True)
class NotesEntry:
    """Ein datierter Eintrag mit den Abschnitten Discussed, Decided und Open des Formats."""

    when: str
    topic: str
    discussed: tuple[str, ...]
    decided: tuple[str, ...]
    open: tuple[str, ...]

    @classmethod
    def create(
        cls, day: date, topic: str, discussed: Sequence[str], decided: Sequence[str], open_points: Sequence[str]
    ) -> NotesEntry:
        entry = cls(day.isoformat(), _line(topic), _bullets(discussed), _bullets(decided), _bullets(open_points))
        if not entry.topic:
            raise ValueRequired("Ein Notiz-Eintrag braucht ein Thema", details={"field": "topic"})
        if not (entry.discussed or entry.decided or entry.open):
            raise ValueRequired(
                "Ein Notiz-Eintrag braucht mindestens einen Stichpunkt unter Discussed, Decided oder Open",
                details={"field": "discussed/decided/open"},
            )
        return entry

    def render(self) -> str:
        parts = [f"## {self.when} — {self.topic}\n"]
        for heading, bullets in (("Discussed", self.discussed), ("Decided", self.decided), ("Open", self.open)):
            if bullets:
                parts.append(f"### {heading}\n\n" + "".join(f"- {bullet}\n" for bullet in bullets))
        return "\n".join(parts)


def append_entry(existing: str, entry: NotesEntry) -> str:
    """Hängt den Eintrag mit einer Leerzeile Abstand an (das Dokument endet immer mit einem Zeilenumbruch)."""
    base = existing if existing.endswith("\n") or not existing else existing + "\n"
    return f"{base}\n{entry.render()}" if base else entry.render()


def renamed_documents(names: Sequence[str], old_label: str, new_label: str) -> dict[str, str]:
    """Alter Name → neuer Name für Dokumente, deren Name das alte Label enthält (Typwechsel)."""
    changes = {name: rewrite_labels(name, old_label, new_label) for name in names}
    return {old: new for old, new in changes.items() if old != new}

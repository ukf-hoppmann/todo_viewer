"""Dokumente einer Note: Namen, Art und Format des datierten Notiz-Eintrags."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from viewer.core.domain.errors import DomainError, InvalidInput

NOTES = "notes"
SPEC = "spec"


class DocumentExists(DomainError):
    code = "document_exists"


class DocumentNotFound(DomainError):
    code = "document_not_found"


def notes_name(label: str) -> str:
    return f"{label}_notes.md"


def document_kind(label: str, name: str) -> str | None:
    """`notes` für `<LABEL>_notes.md`, `spec` für `<LABEL>_spec[_<thema>].md`, sonst `None`."""
    if name == notes_name(label):
        return NOTES
    if re.fullmatch(rf"{re.escape(label)}_spec(_[A-Za-z0-9-]+)?\.md", name):
        return SPEC
    return None


def new_document_kind(label: str, name: str) -> str:
    kind = document_kind(label, name)
    if kind is None:
        raise InvalidInput(
            f"'{name}' ist kein gültiger Name für ein Dokument",
            details={"field": "name", "allowed": [notes_name(label), f"{label}_spec.md", f"{label}_spec_<thema>.md"]},
        )
    return kind


def notes_header(label: str, summary: str) -> str:
    return f"# {label} — {summary}\n"


def _line(text: str) -> str:
    return " ".join(text.split())


def _bullets(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(bullet for bullet in (_line(value) for value in values) if bullet)


@dataclass(frozen=True)
class NotesEntry:
    """Ein datierter Eintrag mit den Abschnitten Discussed, Decided und Open."""

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
            raise InvalidInput("Ein Notiz-Eintrag braucht ein Thema", details={"field": "topic"})
        if not (entry.discussed or entry.decided or entry.open):
            raise InvalidInput(
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

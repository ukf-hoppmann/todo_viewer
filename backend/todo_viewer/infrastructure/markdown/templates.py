"""Texts of a new, empty backlog (TODO.md and archive.md), following the Claude_Harness templates.

Headings and prose are localized; the format marker, `## Work items` and `No entries.`
stay as the parser expects them.
"""
from __future__ import annotations

from todo_viewer.domain.errors import InvalidValueError
from todo_viewer.domain.item import Location

from .syntax import NO_ENTRIES_LINE

_TEMPLATES: dict[str, dict[Location, str]] = {
    "en": {
        Location.ACTIVE: """# Project Backlog

Active project work: open, in progress, or awaiting a project-owner decision.
Completed and rejected items are moved to `archive.md`; per-item notes and
specs live in `items/<ID>/`.

Format: Claude_Harness backlog format version 1. The rules are defined in the
`todo` skill of the claude-harness plugin (`skills/todo/format.md`).
""",
        Location.ARCHIVE: """# Project Backlog Archive

Completed and rejected work items, moved unchanged from `TODO.md` after the
project owner's decision.

Format: Claude_Harness backlog format version 1. The rules are defined in the
`todo` skill of the claude-harness plugin (`skills/todo/format.md`).
""",
    },
    "de": {
        Location.ACTIVE: """# Projekt-Backlog

Aktive Projektarbeit: offen, in Arbeit oder wartend auf eine Entscheidung des
Projektverantwortlichen. Erledigte und abgelehnte Einträge werden nach
`archive.md` verschoben; Notizen und Specs pro Eintrag liegen in `items/<ID>/`.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).
""",
        Location.ARCHIVE: """# Projekt-Backlog-Archiv

Erledigte und abgelehnte Einträge, nach Entscheidung des Projektverantwortlichen
unverändert aus `TODO.md` hierher verschoben.

Format: Claude_Harness-Backlog-Format Version 1. Die Regeln sind im
`todo`-Skill des claude-harness-Plugins definiert (`skills/todo/format.md`).
""",
    },
}

LANGUAGES = tuple(_TEMPLATES)


class EmptyBacklogTemplates:
    def for_language(self, language: str) -> dict[Location, str]:
        """Full file texts per location; raises InvalidValueError for unknown languages."""
        texts = _TEMPLATES.get(language)
        if texts is None:
            raise InvalidValueError("language", LANGUAGES)
        return {loc: f"{text}\n## Work items\n\n{NO_ENTRIES_LINE}\n" for loc, text in texts.items()}

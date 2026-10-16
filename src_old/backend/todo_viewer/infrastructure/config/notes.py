"""The global options `notes.max_topic_depth` and `notes.review_days` from config.json."""
from __future__ import annotations

from typing import Any

from todo_viewer.domain.notes import NotesSettings

from .json_file import JsonFile


def notes_settings(file: JsonFile) -> NotesSettings:
    """Missing, non-numeric, or non-positive values fall back to the defaults."""
    raw: Any = file.read().get("notes") if file.exists() else None
    section = raw if isinstance(raw, dict) else {}
    defaults = NotesSettings()
    return NotesSettings(
        max_topic_depth=_positive(section.get("max_topic_depth"), defaults.max_topic_depth),
        review_days=_positive(section.get("review_days"), defaults.review_days))


def _positive(value: object, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else default


class JsonNotesSettingsStore:
    """The `notes` section of config.json; the rest of the file stays as it is."""

    def __init__(self, file: JsonFile):
        self._file = file

    def load(self) -> NotesSettings:
        return notes_settings(self._file)

    def save(self, settings: NotesSettings) -> None:
        data: Any = self._file.read() if self._file.exists() else {}
        data = data if isinstance(data, dict) else {}
        section = data.get("notes") if isinstance(data.get("notes"), dict) else {}
        data["notes"] = {**section, "max_topic_depth": settings.max_topic_depth, "review_days": settings.review_days}
        self._file.write(data)

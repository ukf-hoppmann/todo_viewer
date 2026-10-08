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

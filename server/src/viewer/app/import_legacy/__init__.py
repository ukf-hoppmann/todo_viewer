"""Übernahme der Daten aus dem alten Viewer (`configs/todo.db`) in die neue Datenbank (STORY-082)."""

from viewer.app.import_legacy.command import import_legacy, main
from viewer.app.import_legacy.reader import LegacyError

__all__ = ["LegacyError", "import_legacy", "main"]

"""The database keeps no files of a project to copy; its data is exported as markdown instead."""
from __future__ import annotations

from todo_viewer.domain.source import Source


class DatabaseRawBackup:
    def copy(self, source: Source, target: str) -> bool:
        return False

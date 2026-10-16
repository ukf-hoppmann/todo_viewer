from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from todo_viewer.domain.errors import SourceGoneError, ValueRequiredError
from todo_viewer.domain.notes import NotesSettings, Topic

from ..ports import NoteRepository, SourceRepository


class TopicService:
    """Topics of a project: create, read, rename, set a due date, move. Trash and restore: `NoteService`."""

    def __init__(self, notes: NoteRepository, sources: SourceRepository,
                 settings: Callable[[], NotesSettings] | None = None):
        self._notes = notes
        self._sources = sources
        self._settings = settings or NotesSettings

    def list(self, project: str, include_deleted: bool = False) -> list[Topic]:
        self._require_project(project)
        return self._notes.list_topics(project, include_deleted=include_deleted)

    def get(self, project: str, label: str) -> Topic:
        self._require_project(project)
        return self._notes.get_topic(project, label)

    def create(self, project: str, name: str, parent: str | None = None, due_at: datetime | None = None) -> Topic:
        self._require_project(project)
        return self._notes.create_topic(project, _name(name), parent, due_at, self._settings().max_topic_depth)

    def edit(self, project: str, label: str, name: str | None = None, due_at: datetime | None = None,
             clear_due_at: bool = False) -> Topic:
        """Only what is given changes; `clear_due_at` removes the due date."""
        current = self.get(project, label)
        new_due = None if clear_due_at else (due_at or current.due_at)
        return self._notes.update_topic(project, label, current.name if name is None else _name(name), new_due)

    def move(self, project: str, label: str, parent: str | None) -> Topic:
        self._require_project(project)
        return self._notes.move_topic(project, label, parent, self._settings().max_topic_depth)

    def _require_project(self, project: str) -> None:
        if not any(s.project == project for s in self._sources.all()):
            raise SourceGoneError(f"Project '{project}' not found.")


def _name(name: str) -> str:
    stripped = name.strip()
    if not stripped:
        raise ValueRequiredError("name")
    return stripped

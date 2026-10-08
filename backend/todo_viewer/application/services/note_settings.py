from __future__ import annotations

from todo_viewer.domain.notes import NotesSettings, changed_settings

from ..ports import NotesSettingsStore


class NotesSettingsService:
    """The global notes options. Services read `current` on every use, so a change applies at once."""

    def __init__(self, store: NotesSettingsStore):
        self._store = store
        self._current = store.load()

    def current(self) -> NotesSettings:
        return self._current

    def update(self, max_topic_depth: int | None = None, review_days: int | None = None) -> NotesSettings:
        """Saves the given values and uses them from now on. Topics that are nested deeper stay as they are."""
        changed = changed_settings(self._current, max_topic_depth, review_days)
        self._store.save(changed)
        self._current = changed
        return changed

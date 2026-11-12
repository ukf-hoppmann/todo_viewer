"""Die Einstellungen von `memos`: Prüf-Intervall und größte Topic-Tiefe."""

from __future__ import annotations

from viewer.core.application.ports import Database, EventBus
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import SETTINGS_TOPIC
from viewer.plugins.memos.application.ports import SettingsRepository
from viewer.plugins.memos.domain.model import MemosSettings, changed_settings


class SettingsService:
    def __init__(self, settings: SettingsRepository, database: Database, events: EventBus) -> None:
        self._settings = settings
        self._database = database
        self._events = events

    def current(self) -> MemosSettings:
        with self._database.transaction() as tx:
            return self._settings.load(tx)

    def update(self, max_topic_depth: int | None, review_days: int | None) -> MemosSettings:
        """Speichert die genannten Werte. Topics, die tiefer liegen, bleiben, wie sie sind."""
        with self._database.transaction() as tx:
            changed = changed_settings(self._settings.load(tx), max_topic_depth, review_days)
            self._settings.save(tx, changed)
        self._events.publish(Event(SETTINGS_TOPIC, {}, public=True))
        return changed

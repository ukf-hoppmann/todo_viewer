"""Einstellung des Auto-Sync-Takts: lesen, ändern, beim Start anwenden."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from viewer.core.application.ports import EventBus, SettingsStore
from viewer.core.domain.events import Event
from viewer.core.domain.sync_settings import SettingLocked, check_auto_sync_interval

KEY = "auto_sync_interval_seconds"
TOPIC = "core.settings.changed"


class IntervalTarget(Protocol):
    def set_interval(self, seconds: float) -> None: ...


@dataclass(frozen=True)
class GetSyncSettings:
    pass


@dataclass(frozen=True)
class PutSyncSettings:
    auto_sync_interval_seconds: float


@dataclass(frozen=True)
class SyncSettingsOut:
    auto_sync_interval_seconds: float
    #: Die Umgebungsvariable `AUTO_SYNC_INTERVAL` ist gesetzt: der Wert lässt sich nicht ändern.
    locked_by_environment: bool


class SyncSettingsService:
    def __init__(
        self, store: SettingsStore, sync: IntervalTarget, events: EventBus, configured: float, locked: bool
    ) -> None:
        self._store = store
        self._sync = sync
        self._events = events
        self._configured = configured
        self._locked = locked

    def get(self) -> SyncSettingsOut:
        return SyncSettingsOut(self._current(), self._locked)

    def put(self, data: PutSyncSettings) -> SyncSettingsOut:
        if self._locked:
            raise SettingLocked(
                "Der Takt ist durch die Umgebungsvariable AUTO_SYNC_INTERVAL gesetzt", details={"setting": KEY}
            )
        seconds = check_auto_sync_interval(data.auto_sync_interval_seconds)
        self._store.put(KEY, str(seconds))
        self._sync.set_interval(seconds)
        self._events.publish(Event(TOPIC, {}, public=True))
        return SyncSettingsOut(seconds, False)

    def apply_stored(self) -> None:
        """Beim Start: der gespeicherte Wert gilt, solange die Umgebung nichts vorgibt."""
        if not self._locked and self._store.get(KEY) is not None:
            self._sync.set_interval(self._current())

    def _current(self) -> float:
        stored = None if self._locked else self._store.get(KEY)
        return float(stored) if stored is not None else self._configured

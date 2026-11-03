from __future__ import annotations

import pytest
from sync_fakes import EventRecorder
from viewer.core.application.sync_settings import PutSyncSettings, SyncSettingsOut, SyncSettingsService
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.sync_settings import SettingLocked


class MemoryStore:
    def __init__(self, **values: str) -> None:
        self.values = dict(values)

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def put(self, key: str, value: str) -> None:
        self.values[key] = value


class IntervalRecorder:
    def __init__(self) -> None:
        self.seconds: list[float] = []

    def set_interval(self, seconds: float) -> None:
        self.seconds.append(seconds)


def make(store: MemoryStore | None = None, configured: float = 30.0, locked: bool = False):
    store, sync, events = store or MemoryStore(), IntervalRecorder(), EventRecorder()
    return SyncSettingsService(store, sync, events, configured, locked), store, sync, events


def test_without_a_stored_value_the_configured_one_is_shown() -> None:
    service, _, _, _ = make(configured=45.0)
    assert service.get() == SyncSettingsOut(45.0, False)


def test_put_stores_the_value_hands_it_to_the_timer_and_announces_it() -> None:
    service, store, sync, events = make()

    out = service.put(PutSyncSettings(10))

    assert out == SyncSettingsOut(10.0, False)
    assert store.values == {"auto_sync_interval_seconds": "10.0"}
    assert sync.seconds == [10.0]
    assert [(e.topic, e.public) for e in events.events] == [("core.settings.changed", True)]
    assert service.get() == SyncSettingsOut(10.0, False)


def test_zero_switches_the_timer_off_and_is_stored() -> None:
    service, store, sync, _ = make()
    assert service.put(PutSyncSettings(0)).auto_sync_interval_seconds == 0.0
    assert sync.seconds == [0.0] and store.values["auto_sync_interval_seconds"] == "0.0"


def test_an_invalid_value_changes_nothing() -> None:
    service, store, sync, events = make()
    with pytest.raises(InvalidInput):
        service.put(PutSyncSettings(0.2))
    assert store.values == {} and sync.seconds == [] and events.events == []


def test_the_environment_wins_and_blocks_writing() -> None:
    service, store, sync, events = make(configured=5.0, locked=True)

    assert service.get() == SyncSettingsOut(5.0, True)
    with pytest.raises(SettingLocked) as raised:
        service.put(PutSyncSettings(10))

    assert raised.value.code == "setting_locked"
    assert store.values == {} and sync.seconds == [] and events.events == []


def test_apply_stored_hands_the_stored_value_to_the_timer() -> None:
    service, _, sync, _ = make(MemoryStore(auto_sync_interval_seconds="12.0"))
    service.apply_stored()
    assert sync.seconds == [12.0]
    assert service.get().auto_sync_interval_seconds == 12.0


def test_apply_stored_leaves_the_configured_value_alone_when_nothing_is_stored_or_the_environment_sets_it() -> None:
    service, _, sync, _ = make()
    service.apply_stored()
    locked, _, locked_sync, _ = make(MemoryStore(auto_sync_interval_seconds="12.0"), configured=5.0, locked=True)
    locked.apply_stored()
    assert sync.seconds == [] and locked_sync.seconds == []
    assert locked.get() == SyncSettingsOut(5.0, True)

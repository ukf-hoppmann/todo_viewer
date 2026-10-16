"""Fakes der Core-Ports für Tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path


class FixedClock:
    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or datetime(2026, 10, 16, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


class NullDatabase:
    @contextmanager
    def transaction(self) -> Iterator[object]:
        raise AssertionError("Dieser Test darf die Datenbank nicht berühren")
        yield


class NullBackups:
    def create(self, reason: str) -> Path:
        raise AssertionError("Dieser Test darf kein Backup anlegen")


class NullScheduler:
    def schedule(self, owner: str, at: datetime | None, callback: Callable[[], None]) -> None:
        pass

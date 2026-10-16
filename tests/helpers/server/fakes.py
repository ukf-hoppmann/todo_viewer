"""Fakes der Core-Ports für Tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


class FixedClock:
    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or datetime(2026, 10, 16, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta

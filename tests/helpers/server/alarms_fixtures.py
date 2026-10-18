"""Wecker für Tests der Domäne des Plugins `alarms`."""

from __future__ import annotations

from datetime import UTC, datetime

from viewer.plugins.alarms.domain.model import Alarm

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


def alarm(
    uid: str,
    at: datetime = NOW,
    status: str = "Pending",
    snoozed_until: datetime | None = None,
    deleted_at: datetime | None = None,
    targets: tuple[str, ...] = (),
    done_at: datetime | None = None,
) -> Alarm:
    return Alarm(uid, "p", uid.upper(), uid, at, status, targets, None, snoozed_until, 1, deleted_at, done_at)

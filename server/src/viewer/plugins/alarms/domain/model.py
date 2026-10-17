"""Wecker: Status, Datentyp und die reinen Regeln (wann fällig, wann der nächste Termin, Übergänge)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from viewer.core.domain.errors import DomainError

STATUSES = ("Pending", "Due", "Done", "Snoozed")
#: Zurückgestellt wird, wenn nichts anderes gesagt ist, um diese Zeit.
DEFAULT_SNOOZE = timedelta(hours=1)


class AlarmViolation(DomainError):
    """Ein Übergang verletzt eine Regel; `code` nennt sie."""

    def __init__(self, code: str, message: str, **details: object) -> None:
        super().__init__(message, code=code, details=dict(details))


@dataclass(frozen=True)
class Alarm:
    """Ein Wecker. `uid`, `label`, `revision` und `deleted_at` gehören dem Register von `workspace`."""

    uid: str
    project_uid: str
    label: str
    text: str
    at: datetime
    status: str
    #: Das Ziel: ein Element (`target_uid`) oder, wenn es das hier nicht gibt, sein Name als Text; sonst frei.
    target_uid: str | None
    target_text: str | None
    snoozed_until: datetime | None
    revision: int
    deleted_at: datetime | None = None


def utc(moment: datetime) -> datetime:
    """Ein Zeitpunkt ohne Zeitzone gilt als UTC."""
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def alarm_time(alarm: Alarm) -> datetime | None:
    """Wann der Wecker sich meldet: `at`, zurückgestellt `snoozed_until`; `None`, wenn er nichts mehr erwartet."""
    if alarm.deleted_at is not None:
        return None
    if alarm.status == "Pending":
        return utc(alarm.at)
    if alarm.status == "Snoozed" and alarm.snoozed_until is not None:
        return utc(alarm.snoozed_until)
    return None


def due_now(alarms: Sequence[Alarm], now: datetime) -> list[Alarm]:
    """Die Wecker, deren Zeitpunkt erreicht ist und die sich noch nicht gemeldet haben; der früheste zuerst."""
    due = [(alarm_time(a), a) for a in alarms]
    return [a for t, a in sorted(((t, a) for t, a in due if t is not None and t <= utc(now)), key=lambda p: p[0])]


def next_due(alarms: Sequence[Alarm], now: datetime) -> datetime | None:
    """Der früheste Zeitpunkt, auf den noch ein Wecker wartet (auch ein vergangener: er ist verpasst); `None`, wenn
    keiner wartet."""
    times = [t for t in (alarm_time(a) for a in alarms) if t is not None]
    return min(times) if times else None


def snooze(alarm: Alarm, now: datetime, until: datetime | None = None) -> Alarm:
    """Zurückgestellt bis `until` (Standard: eine Stunde); ein erledigter oder gelöschter Wecker bleibt, wie er ist."""
    _open(alarm)
    target = utc(until) if until is not None else utc(now) + DEFAULT_SNOOZE
    if target <= utc(now):
        raise AlarmViolation(
            "snooze_in_past", "Zurückgestellt wird auf einen Zeitpunkt in der Zukunft", until=str(until)
        )
    return replace(alarm, status="Snoozed", snoozed_until=target)


def finish(alarm: Alarm) -> Alarm:
    _open(alarm)
    return replace(alarm, status="Done", snoozed_until=None)


def reschedule(alarm: Alarm, at: datetime) -> Alarm:
    """Ein neuer Zeitpunkt: der Wecker wartet wieder (auch ein erledigter)."""
    if alarm.deleted_at is not None:
        raise AlarmViolation("alarm_deleted", f"{alarm.label} liegt im Papierkorb", alarm=alarm.label)
    return replace(alarm, at=utc(at), status="Pending", snoozed_until=None)


def fire(alarm: Alarm) -> Alarm:
    """Der Wecker meldet sich: `Due` (der Zeitpunkt bleibt)."""
    return replace(alarm, status="Due", snoozed_until=None)


def _open(alarm: Alarm) -> None:
    if alarm.deleted_at is not None:
        raise AlarmViolation("alarm_deleted", f"{alarm.label} liegt im Papierkorb", alarm=alarm.label)
    if alarm.status == "Done":
        raise AlarmViolation("alarm_done", f"{alarm.label} ist schon erledigt", alarm=alarm.label)

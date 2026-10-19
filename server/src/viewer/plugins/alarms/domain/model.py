"""Wecker: Status, Datentyp und die reinen Regeln (wann fällig, wann der nächste Termin, Übergänge, erlöschen,
aufräumen).

Ein Wecker ist eine Erinnerung, kein Planungselement: er erinnert an seine Elemente oder ist eine freie Erinnerung mit
Text. Erledigt (`Done`) oder erloschen (`Expired`, kein Element mehr offen) bleibt er `PURGE_AFTER` sichtbar und wird
dann endgültig gelöscht."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo

from viewer.core.domain.errors import DomainError
from viewer.plugins.alarms.domain import series

STATUSES = ("Pending", "Due", "Done", "Snoozed", "Expired")
#: Wecker, die nichts mehr erwarten: von Hand erledigt oder erloschen.
CLOSED_STATUSES = frozenset({"Done", "Expired"})
#: Zurückgestellt wird, wenn nichts anderes gesagt ist, um diese Zeit.
DEFAULT_SNOOZE = timedelta(hours=1)
#: So lange bleibt ein erledigter oder erloschener Wecker sichtbar (zum Rückgängigmachen), dann wird er gelöscht.
PURGE_AFTER = timedelta(hours=24)


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
    #: Die Elemente, an die er erinnert (`uid`s, in dieser Reihenfolge); leer bei einer freien Erinnerung.
    targets: tuple[str, ...]
    #: Verweise auf Elemente anderer Projekte, die es hier nicht gibt, als Text (`Projekt:LABEL`, komma-getrennt).
    target_text: str | None
    snoozed_until: datetime | None
    revision: int
    deleted_at: datetime | None = None
    #: Wann er erledigt wurde oder erloschen ist; von da an läuft `PURGE_AFTER`.
    done_at: datetime | None = None
    #: Wiederholung (`REPEATS`); bei einer Serie ist `series_from` ihr Startpunkt (UTC), sonst leer.
    repeat: str = "none"
    series_from: datetime | None = None


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


def to_purge(alarms: Sequence[Alarm], now: datetime) -> list[Alarm]:
    """Die erledigten und erloschenen Wecker, deren Frist `PURGE_AFTER` vorbei ist (nicht die im Papierkorb)."""
    return [a for a in alarms if (t := purge_time(a)) is not None and t <= utc(now)]


def purge_time(alarm: Alarm) -> datetime | None:
    if alarm.deleted_at is not None or alarm.status not in CLOSED_STATUSES or alarm.done_at is None:
        return None
    return utc(alarm.done_at) + PURGE_AFTER


def next_wakeup(alarms: Sequence[Alarm], now: datetime) -> datetime | None:
    """Der eine Termin des Plugins: der nächste Wecker, der sich meldet, oder der nächste, der aufgeräumt wird."""
    times = [t for t in (next_due(alarms, now), *(purge_time(a) for a in alarms)) if t is not None]
    return min(times) if times else None


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


def finish(alarm: Alarm, now: datetime, zone: tzinfo) -> Alarm:
    """Erledigt. Ein Serienwecker wird nie `Done`: er wartet auf den ersten Termin der Serie nach jetzt."""
    _open(alarm)
    if alarm.repeat != "none" and alarm.series_from is not None:
        following = series.first_after(alarm.series_from, alarm.repeat, now, zone)
        return replace(alarm, status="Pending", at=following, snoozed_until=None, done_at=None)
    return replace(alarm, status="Done", snoozed_until=None, done_at=utc(now))


def alarm_missed(alarm: Alarm, now: datetime, zone: tzinfo) -> int:
    """Wie viele Termine der Serie seit `at` verpasst sind (abgeleitet, nicht gespeichert); ohne Wiederholung 0."""
    return series.missed(alarm.at, alarm.series_from, alarm.repeat, now, zone)


def with_repeat(alarm: Alarm, repeat: str) -> Alarm:
    """Setzt die Wiederholung. Beginnt eine Serie, ist `at` ihr Startpunkt; eine andere Art behält ihn; `none` leert
    ihn. Ob `repeat` erlaubt ist (`series.REPEATS`), prüft der Aufrufer."""
    if repeat == "none":
        return replace(alarm, repeat="none", series_from=None)
    started = alarm.series_from if alarm.repeat != "none" and alarm.series_from is not None else utc(alarm.at)
    return replace(alarm, repeat=repeat, series_from=started)


def undo(alarm: Alarm, now: datetime) -> Alarm:
    """Rückgängig: ein von Hand erledigter Wecker wartet wieder (`Due`, wenn seine Zeit schon vorbei ist). Ein
    erloschener kommt nur zurück, wenn eins seiner Elemente wieder offen ist."""
    if alarm.deleted_at is not None:
        raise AlarmViolation("alarm_deleted", f"{alarm.label} liegt im Papierkorb", alarm=alarm.label)
    if alarm.status != "Done":
        raise AlarmViolation("alarm_not_done", f"{alarm.label} ist nicht erledigt", alarm=alarm.label)
    return _reopen(alarm, now)


def follow_targets(alarm: Alarm, open_states: Sequence[bool], now: datetime) -> Alarm:
    """Der Wecker folgt seinen Elementen (`open_states` in der Reihenfolge von `targets`): ist keins mehr offen,
    erlischt er; ist ein erloschener wieder an einem offenen Element, kehrt er zurück. Ohne Elemente, erledigt oder
    gelöscht bleibt er, wie er ist."""
    if alarm.deleted_at is not None or not alarm.targets:
        return alarm
    any_open = any(open_states)
    if alarm.status == "Expired" and any_open:
        return _reopen(alarm, now)
    if alarm.status not in CLOSED_STATUSES and not any_open:
        return replace(alarm, status="Expired", snoozed_until=None, done_at=utc(now))
    return alarm


def reschedule(alarm: Alarm, at: datetime) -> Alarm:
    """Ein neuer Zeitpunkt: der Wecker wartet wieder (auch ein erledigter); bei einer Serie beginnt damit eine neue."""
    if alarm.deleted_at is not None:
        raise AlarmViolation("alarm_deleted", f"{alarm.label} liegt im Papierkorb", alarm=alarm.label)
    started = utc(at) if alarm.repeat != "none" else None
    return replace(alarm, at=utc(at), status="Pending", snoozed_until=None, done_at=None, series_from=started)


def fire(alarm: Alarm) -> Alarm:
    """Der Wecker meldet sich: `Due` (der Zeitpunkt bleibt)."""
    return replace(alarm, status="Due", snoozed_until=None)


def _reopen(alarm: Alarm, now: datetime) -> Alarm:
    status = "Due" if utc(alarm.at) <= utc(now) else "Pending"
    return replace(alarm, status=status, snoozed_until=None, done_at=None)


def _open(alarm: Alarm) -> None:
    if alarm.deleted_at is not None:
        raise AlarmViolation("alarm_deleted", f"{alarm.label} liegt im Papierkorb", alarm=alarm.label)
    if alarm.status in CLOSED_STATUSES:
        raise AlarmViolation("alarm_done", f"{alarm.label} ist schon erledigt", alarm=alarm.label)

"""Serientermine eines Weckers: reine Funktionen, die Ortszeit rechnen (Zone als Parameter, Architektur §4).

Termin n ist der Startpunkt plus n Intervalle, immer vom Startpunkt aus gerechnet und nie vom vorigen Termin, damit
nichts wandert. Die Wandzeit bleibt über die Sommerzeit-Umstellung gleich („11 Uhr bleibt 11 Uhr“); am Monatsende wird
gekürzt."""

from __future__ import annotations

import calendar
from datetime import UTC, date, datetime, timedelta, tzinfo

REPEATS = ("none", "daily", "weekly", "monthly", "yearly")


def occurrence(series_from: datetime, repeat: str, n: int, zone: tzinfo) -> datetime:
    """Der n-te Termin (n = 0 ist der Startpunkt) als UTC-Zeitpunkt."""
    start = _local(series_from, zone)
    if repeat == "daily":
        day = start.date() + timedelta(days=n)
    elif repeat == "weekly":
        day = start.date() + timedelta(weeks=n)
    elif repeat == "monthly":
        day = _shift_months(start.date(), n)
    elif repeat == "yearly":
        day = _shift_months(start.date(), 12 * n)
    else:
        raise ValueError(f"keine Wiederholung: {repeat}")
    # `fold=0`: eine doppelte Ortszeit nimmt die erste; eine fehlende rückt um die Länge der Lücke vor.
    wall = datetime.combine(day, start.time(), tzinfo=zone)
    return wall.astimezone(UTC)


def first_after(series_from: datetime, repeat: str, now: datetime, zone: tzinfo) -> datetime:
    """Der erste Termin, der echt nach `now` liegt (mindestens der Startpunkt)."""
    return occurrence(series_from, repeat, max(_index(series_from, repeat, now, zone) + 1, 0), zone)


def missed(at: datetime, series_from: datetime | None, repeat: str, now: datetime, zone: tzinfo) -> int:
    """Wie viele Termine nach `at` bis `now` schon vorbei sind; ohne Wiederholung 0."""
    if repeat == "none" or series_from is None:
        return 0
    return max(_index(series_from, repeat, now, zone) - _index(series_from, repeat, at, zone), 0)


def _index(series_from: datetime, repeat: str, moment: datetime, zone: tzinfo) -> int:
    """Der größte Index n mit Termin n <= `moment`; -1 vor dem Startpunkt. Schätzt aus dem Datum und prüft nach."""
    start, here = _local(series_from, zone).date(), _local(moment, zone).date()
    if repeat == "daily":
        guess = (here - start).days
    elif repeat == "weekly":
        guess = (here - start).days // 7
    elif repeat == "monthly":
        guess = (here.year - start.year) * 12 + here.month - start.month
    else:
        guess = here.year - start.year
    guess = max(guess, -1)
    while occurrence(series_from, repeat, guess + 1, zone) <= moment:
        guess += 1
    while guess >= 0 and occurrence(series_from, repeat, guess, zone) > moment:
        guess -= 1
    return guess


def _local(moment: datetime, zone: tzinfo) -> datetime:
    aware = moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment
    return aware.astimezone(zone)


def _shift_months(day: date, months: int) -> date:
    index = day.year * 12 + day.month - 1 + months
    year, month = divmod(index, 12)
    return date(year, month + 1, min(day.day, calendar.monthrange(year, month + 1)[1]))

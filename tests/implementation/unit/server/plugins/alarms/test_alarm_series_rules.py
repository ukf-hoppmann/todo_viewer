from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from alarms_fixtures import alarm
from viewer.plugins.alarms.domain.model import (
    AlarmViolation,
    alarm_missed,
    finish,
    follow_targets,
    reschedule,
    snooze,
    undo,
    with_repeat,
)

BERLIN = ZoneInfo("Europe/Berlin")


def at(day: int, hour: int = 9) -> datetime:
    """Mai 2026, Berliner Wandzeit (UTC gespeichert)."""
    return datetime(2026, 5, day, hour, tzinfo=BERLIN).astimezone(UTC)


def daily(due_on: int = 1, start: int = 1, status: str = "Due"):  # type: ignore[no-untyped-def]
    return alarm("a", at(due_on), status, repeat="daily", series_from=at(start))


def test_finishing_a_series_alarm_waits_for_the_first_term_after_now() -> None:
    due = daily(due_on=1, start=1, status="Due")

    after = finish(due, at(4, 12), BERLIN)

    assert (after.status, after.at, after.snoozed_until, after.done_at) == ("Pending", at(5), None, None)
    assert after.series_from == at(1)


def test_finishing_a_series_alarm_never_makes_it_done_even_after_a_long_pause() -> None:
    assert finish(daily(), at(1) + timedelta(days=400), BERLIN).status == "Pending"


def test_finishing_a_snoozed_series_alarm_leaves_the_snooze_behind() -> None:
    snoozed = alarm("a", at(1), "Snoozed", at(2), repeat="daily", series_from=at(1))

    after = finish(snoozed, at(1, 12), BERLIN)

    assert (after.status, after.at, after.snoozed_until) == ("Pending", at(2), None)


def test_finishing_without_repetition_still_makes_it_done() -> None:
    after = finish(alarm("a", at(1), "Due"), at(2), BERLIN)

    assert (after.status, after.done_at) == ("Done", at(2))


def test_snoozing_moves_the_next_message_but_not_the_series() -> None:
    snoozed = snooze(daily(), at(1, 10), at(1, 15))

    assert (snoozed.status, snoozed.snoozed_until, snoozed.series_from) == ("Snoozed", at(1, 15), at(1))
    assert finish(snoozed, at(1, 16), BERLIN).at == at(2)


def test_a_series_alarm_cannot_be_undone_because_it_is_never_done() -> None:
    with pytest.raises(AlarmViolation) as caught:
        undo(daily(), at(2))

    assert caught.value.code == "alarm_not_done"


def test_an_expired_series_alarm_ends_its_series_and_comes_back_with_its_elements() -> None:
    series = alarm("a", at(1), "Due", targets=("t",), repeat="daily", series_from=at(1))

    expired = follow_targets(series, [False], at(3))
    with pytest.raises(AlarmViolation):
        finish(expired, at(3), BERLIN)
    back = follow_targets(expired, [True], at(3))

    assert (expired.status, back.status, back.at, back.repeat) == ("Expired", "Due", at(1), "daily")


def test_a_repetition_starts_the_series_at_the_alarms_time() -> None:
    after = with_repeat(alarm("a", at(3)), "weekly")

    assert (after.repeat, after.series_from) == ("weekly", at(3))


def test_changing_the_kind_of_repetition_keeps_the_series_start() -> None:
    after = with_repeat(daily(due_on=5, start=1), "weekly")

    assert (after.repeat, after.series_from) == ("weekly", at(1))


def test_no_repetition_clears_the_series_start() -> None:
    after = with_repeat(daily(), "none")

    assert (after.repeat, after.series_from) == ("none", None)


def test_a_new_time_starts_a_new_series() -> None:
    after = reschedule(daily(due_on=5, start=1), at(9))

    assert (after.at, after.series_from, after.status) == (at(9), at(9), "Pending")


def test_a_new_time_without_repetition_has_no_series() -> None:
    assert reschedule(alarm("a", at(1)), at(9)).series_from is None


def test_missed_terms_are_derived_from_time_and_repetition() -> None:
    assert alarm_missed(daily(due_on=1), at(4, 10), BERLIN) == 3
    assert alarm_missed(alarm("a", at(1), "Due"), at(4, 10), BERLIN) == 0

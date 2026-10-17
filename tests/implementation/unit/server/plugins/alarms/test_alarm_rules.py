from __future__ import annotations

from datetime import timedelta

import pytest
from alarms_fixtures import NOW, alarm
from viewer.plugins.alarms.domain.model import (
    AlarmViolation,
    alarm_time,
    due_now,
    finish,
    fire,
    next_due,
    reschedule,
    snooze,
)

PAST = NOW - timedelta(hours=2)
FUTURE = NOW + timedelta(hours=2)


def test_a_pending_alarm_is_due_when_its_time_is_reached() -> None:
    assert [a.uid for a in due_now([alarm("a", PAST), alarm("b", NOW), alarm("c", FUTURE)], NOW)] == ["a", "b"]


def test_due_alarms_come_earliest_first() -> None:
    late, early = alarm("late", NOW), alarm("early", PAST)
    assert [a.uid for a in due_now([late, early], NOW)] == ["early", "late"]


def test_a_snoozed_alarm_waits_for_its_new_time_not_its_old_one() -> None:
    quiet = alarm("a", PAST, "Snoozed", FUTURE)
    ready = alarm("b", PAST, "Snoozed", PAST)
    assert [a.uid for a in due_now([quiet, ready], NOW)] == ["b"]
    assert alarm_time(quiet) == FUTURE


@pytest.mark.parametrize("status", ["Due", "Done"])
def test_alarms_that_were_fired_or_finished_wait_for_nothing(status: str) -> None:
    waiting = alarm("a", PAST, status)
    assert due_now([waiting], NOW) == [] and next_due([waiting], NOW) is None


def test_an_alarm_in_the_trash_is_ignored() -> None:
    assert due_now([alarm("a", PAST, deleted_at=PAST)], NOW) == []
    assert next_due([alarm("a", PAST, deleted_at=PAST)], NOW) is None


def test_the_next_time_is_the_earliest_that_still_waits_even_if_it_was_missed() -> None:
    alarms = [alarm("a", FUTURE), alarm("b", PAST), alarm("c", NOW + timedelta(days=1)), alarm("d", PAST, "Done")]
    assert next_due(alarms, NOW) == PAST
    assert next_due(
        [alarm("a", FUTURE), alarm("s", PAST, "Snoozed", NOW + timedelta(minutes=5))], NOW
    ) == NOW + timedelta(minutes=5)
    assert next_due([], NOW) is None


def test_a_time_without_zone_counts_as_utc() -> None:
    assert [a.uid for a in due_now([alarm("a", PAST.replace(tzinfo=None))], NOW)] == ["a"]


def test_the_clock_decides() -> None:
    assert due_now([alarm("a", NOW)], NOW - timedelta(seconds=1)) == []
    assert len(due_now([alarm("a", NOW)], NOW)) == 1


def test_snoozing_sets_the_status_and_defaults_to_one_hour() -> None:
    assert (snooze(alarm("a", PAST), NOW).status, snooze(alarm("a", PAST), NOW).snoozed_until) == (
        "Snoozed",
        NOW + timedelta(hours=1),
    )
    assert snooze(alarm("a", PAST, "Due"), NOW, FUTURE).snoozed_until == FUTURE


def test_snoozing_into_the_past_or_a_closed_alarm_is_refused() -> None:
    with pytest.raises(AlarmViolation) as error:
        snooze(alarm("a"), NOW, PAST)
    assert error.value.code == "snooze_in_past"
    for closed, code in ((alarm("a", status="Done"), "alarm_done"), (alarm("a", deleted_at=PAST), "alarm_deleted")):
        with pytest.raises(AlarmViolation) as error:
            snooze(closed, NOW)
        assert error.value.code == code
        with pytest.raises(AlarmViolation):
            finish(closed)


def test_finishing_clears_the_snooze_and_a_new_time_wakes_the_alarm_again() -> None:
    done = finish(alarm("a", PAST, "Snoozed", FUTURE))
    assert (done.status, done.snoozed_until) == ("Done", None)
    again = reschedule(done, FUTURE)
    assert (again.status, again.at, again.snoozed_until) == ("Pending", FUTURE, None)
    with pytest.raises(AlarmViolation):
        reschedule(alarm("a", deleted_at=PAST), FUTURE)


def test_firing_keeps_the_time_and_marks_due() -> None:
    fired = fire(alarm("a", PAST, "Snoozed", PAST))
    assert (fired.status, fired.at, fired.snoozed_until) == ("Due", PAST, None)

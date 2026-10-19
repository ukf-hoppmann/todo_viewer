from __future__ import annotations

from datetime import UTC, timedelta

import pytest
from alarms_fixtures import NOW, alarm
from viewer.plugins.alarms.domain.model import (
    PURGE_AFTER,
    AlarmViolation,
    alarm_time,
    due_now,
    finish,
    fire,
    follow_targets,
    next_due,
    next_wakeup,
    reschedule,
    snooze,
    to_purge,
    undo,
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


@pytest.mark.parametrize("status", ["Due", "Done", "Expired"])
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
            finish(closed, NOW, UTC)


def test_finishing_clears_the_snooze_and_a_new_time_wakes_the_alarm_again() -> None:
    done = finish(alarm("a", PAST, "Snoozed", FUTURE), NOW, UTC)
    assert (done.status, done.snoozed_until, done.done_at) == ("Done", None, NOW)
    again = reschedule(done, FUTURE)
    assert (again.status, again.at, again.snoozed_until, again.done_at) == ("Pending", FUTURE, None, None)
    with pytest.raises(AlarmViolation):
        reschedule(alarm("a", deleted_at=PAST), FUTURE)


def test_firing_keeps_the_time_and_marks_due() -> None:
    fired = fire(alarm("a", PAST, "Snoozed", PAST))
    assert (fired.status, fired.at, fired.snoozed_until) == ("Due", PAST, None)


# --- Erinnerung an Elemente: erlöschen, zurückkehren, aufräumen -------------------------------------------------


def test_an_alarm_expires_when_none_of_its_elements_is_open_any_more() -> None:
    expired = follow_targets(alarm("a", FUTURE, "Snoozed", FUTURE, targets=("x", "y")), [False, False], NOW)
    assert (expired.status, expired.done_at, expired.snoozed_until) == ("Expired", NOW, None)
    assert follow_targets(alarm("a", targets=("x", "y")), [False, True], NOW).status == "Pending"


def test_an_alarm_without_elements_never_expires() -> None:
    assert follow_targets(alarm("a"), [], NOW).status == "Pending"


def test_a_finished_or_deleted_alarm_does_not_follow_its_elements() -> None:
    done = alarm("a", status="Done", targets=("x",), done_at=PAST)
    assert follow_targets(done, [False], NOW) == done
    assert follow_targets(done, [True], NOW) == done
    deleted = alarm("a", targets=("x",), deleted_at=PAST)
    assert follow_targets(deleted, [False], NOW) == deleted


def test_an_expired_alarm_comes_back_when_an_element_opens_again() -> None:
    later = follow_targets(alarm("a", FUTURE, "Expired", targets=("x",), done_at=PAST), [True], NOW)
    assert (later.status, later.done_at) == ("Pending", None)
    missed = follow_targets(alarm("a", PAST, "Expired", targets=("x",), done_at=PAST), [True], NOW)
    assert missed.status == "Due"


def test_undo_reopens_a_finished_alarm_only() -> None:
    assert undo(alarm("a", FUTURE, "Done", done_at=PAST), NOW).status == "Pending"
    assert undo(alarm("a", PAST, "Done", done_at=PAST), NOW).status == "Due"
    for other in (alarm("a"), alarm("a", status="Expired", targets=("x",), done_at=PAST)):
        with pytest.raises(AlarmViolation) as error:
            undo(other, NOW)
        assert error.value.code == "alarm_not_done"


def test_finished_and_expired_alarms_are_purged_a_day_later() -> None:
    fresh = alarm("fresh", status="Done", done_at=NOW - PURGE_AFTER + timedelta(seconds=1))
    old = alarm("old", status="Done", done_at=NOW - PURGE_AFTER)
    gone = alarm("gone", status="Expired", targets=("x",), done_at=NOW - timedelta(days=3))
    trashed = alarm("trashed", status="Done", done_at=NOW - timedelta(days=3), deleted_at=PAST)
    assert [a.uid for a in to_purge([fresh, old, gone, trashed, alarm("open")], NOW)] == ["old", "gone"]


def test_the_timer_wakes_for_the_next_alarm_or_the_next_purge() -> None:
    finished = alarm("d", status="Done", done_at=NOW)
    assert next_wakeup([finished], NOW) == NOW + PURGE_AFTER
    assert next_wakeup([finished, alarm("a", FUTURE)], NOW) == FUTURE
    assert next_wakeup([], NOW) is None

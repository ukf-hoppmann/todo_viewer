from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest
from notes_fixtures import NOW, note, topic, trigger
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.notes.domain.due import check_new_trigger, due_state, hit, reset
from viewer.plugins.notes.domain.model import NotesViolation, Topic
from viewer.plugins.notes.domain.notices import Notice, cause_of_status, check_decision, decision_options

PAST = NOW - timedelta(days=1)
FUTURE = NOW + timedelta(days=1)
FIRED = trigger("fired", fired_at=PAST)
WAITING = trigger("waiting")
TOPIC_PASSED = topic("t", archived_at=None)  # Termin unten gesetzt
PASSED = replace(TOPIC_PASSED, due_at=PAST)
COMING = replace(TOPIC_PASSED, due_at=FUTURE)


@pytest.mark.parametrize(
    "triggers,mode,topic_,notices,review,status,reason",
    [
        # nichts los
        ([], "any", None, 0, FUTURE, "waiting", None),
        ([WAITING], "any", None, 0, FUTURE, "waiting", None),
        # Prüfdatum
        ([], "any", None, 0, PAST, "due", "review_expired"),
        ([WAITING], "any", None, 0, NOW, "due", "review_expired"),
        # Auslöser
        ([FIRED], "any", None, 0, FUTURE, "due", "trigger"),
        ([FIRED, WAITING], "any", None, 0, FUTURE, "due", "trigger"),
        ([FIRED, WAITING], "all", None, 0, FUTURE, "waiting", None),
        ([FIRED, FIRED], "all", None, 0, FUTURE, "due", "trigger"),
        # Hinweis
        ([], "any", None, 1, FUTURE, "due", "notice"),
        ([WAITING], "all", None, 2, PAST, "due", "notice"),
        # Topic-Termin
        ([trigger("d", kind="topic_date", target=None, status=None)], "any", PASSED, 0, FUTURE, "due", "topic_due"),
        ([trigger("d", kind="topic_date", target=None, status=None)], "any", COMING, 0, FUTURE, "waiting", None),
        ([trigger("d", kind="topic_date", target=None, status=None)], "any", PASSED, 1, FUTURE, "due", "notice"),
        (
            [trigger("d", kind="topic_date", target=None, status=None), FIRED],
            "any",
            PASSED,
            0,
            FUTURE,
            "due",
            "trigger",
        ),
        # Reihenfolge: Auslöser vor Hinweis vor Prüfdatum
        ([FIRED], "any", None, 1, PAST, "due", "trigger"),
        ([], "any", None, 1, PAST, "due", "notice"),
    ],
)
def test_due_state_table(triggers, mode, topic_, notices, review, status, reason) -> None:  # type: ignore[no-untyped-def]
    state = due_state(replace(note("n", review_at=review), trigger_mode=mode), triggers, topic_, notices, NOW)
    assert (state.status, state.reason) == (status, reason)


def test_a_snoozed_note_is_due_by_the_same_rules() -> None:
    state = due_state(note("n", status="snoozed", review_at=FUTURE), [FIRED], None, 0, NOW)
    assert (state.status, state.reason, state.fired) == ("due", "trigger", ("fired",))


@pytest.mark.parametrize("status", ["done", "dropped", "promoted"])
def test_finished_notes_are_never_due_whatever_happens(status: str) -> None:
    state = due_state(note("n", status=status, archived=True, review_at=PAST), [FIRED], None, 3, NOW)
    assert (state.status, state.reason, state.fired) == (status, None, ())


def test_an_archived_or_deleted_note_is_never_due() -> None:
    assert due_state(note("n", archived=True, review_at=PAST), [FIRED], None, 1, NOW).status == "waiting"
    assert due_state(note("n", review_at=PAST, deleted_at=PAST), [FIRED], None, 1, NOW).reason is None


def test_all_fired_is_reported_and_needs_triggers() -> None:
    assert due_state(note("n"), [FIRED, FIRED], None, 0, NOW).all_fired is True
    assert due_state(note("n"), [FIRED, WAITING], None, 0, NOW).all_fired is False
    assert due_state(note("n"), [], None, 0, NOW).all_fired is False


def test_a_topic_date_in_the_trash_does_not_arrive() -> None:
    gone = replace(PASSED, deleted_at=PAST)
    state = due_state(note("n"), [trigger("d", kind="topic_date", target=None, status=None)], gone, 0, NOW)
    assert state.status == "waiting"


def test_the_clock_decides() -> None:
    quiet = note("n", review_at=NOW)
    assert due_state(quiet, [], None, 0, NOW - timedelta(seconds=1)).status == "waiting"
    assert due_state(quiet, [], None, 0, NOW).status == "due"


def test_an_event_hits_only_the_waiting_trigger_with_its_status() -> None:
    assert hit(WAITING, "Completed")
    assert not hit(WAITING, "Rejected")
    assert not hit(WAITING, "Open")
    assert not hit(FIRED, "Completed")
    assert not hit(trigger("d", kind="topic_date", target=None, status=None), "Completed")


def test_resetting_clears_fired_events_and_drops_passed_dates() -> None:
    date_passed = trigger("d1", kind="topic_date", target=None, status=None)
    kept, removed = reset([FIRED, WAITING, date_passed], PASSED, NOW)
    assert [(t.uid, t.fired_at) for t in kept] == [("fired", None), ("waiting", None)]
    assert removed == ["d1"]
    kept, removed = reset([date_passed], COMING, NOW)
    assert ([t.uid for t in kept], removed) == (["d1"], [])


def test_new_triggers_follow_the_rules() -> None:
    check_new_trigger(note("n"), "event", "Completed", None)
    check_new_trigger(note("n"), "topic_date", None, COMING)
    for kind, status, topic_ in (("time", None, None), ("event", "Open", None), ("event", None, None)):
        with pytest.raises(InvalidInput):
            check_new_trigger(note("n"), kind, status, topic_)
    topics: list[Topic | None] = [None, TOPIC_PASSED]
    for candidate in topics:
        with pytest.raises(NotesViolation) as error:
            check_new_trigger(note("n"), "topic_date", None, candidate)
        assert error.value.code == "trigger_needs_topic_date"


def _notice(side: str = "note", decided: bool = False) -> Notice:
    return Notice("x", side, "s", "o", "item_completed", NOW, NOW if decided else None)


def test_notice_decisions_belong_to_their_side() -> None:
    assert decision_options("note") == ("keep", "detach", "drop", "promote")
    assert decision_options("item") == ("acknowledge",)
    check_decision(_notice(), "keep")
    check_decision(_notice("item"), "acknowledge")
    for notice, decision in ((_notice(), "acknowledge"), (_notice("item"), "keep")):
        with pytest.raises(InvalidInput):
            check_decision(notice, decision)


def test_a_decided_notice_cannot_be_decided_again() -> None:
    with pytest.raises(NotesViolation) as error:
        check_decision(_notice(decided=True), "keep")
    assert error.value.code == "notice_decided"


def test_only_the_closing_statuses_cause_a_notice() -> None:
    assert [cause_of_status(s) for s in ("Completed", "Rejected", "Open", "In progress")] == [
        "item_completed",
        "item_rejected",
        None,
        None,
    ]

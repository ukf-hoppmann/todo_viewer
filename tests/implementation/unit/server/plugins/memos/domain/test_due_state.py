from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

import pytest
from memos_fixtures import NOW, memo, topic, trigger
from viewer.core.domain.errors import InvalidInput
from viewer.plugins.memos.domain.due import check_new_trigger, due_since, due_state, hit, next_clock_due, reset
from viewer.plugins.memos.domain.hints import Hint, cause_of_status, check_decision, decision_options
from viewer.plugins.memos.domain.model import MemosViolation, Topic

PAST = NOW - timedelta(days=1)
FUTURE = NOW + timedelta(days=1)
FIRED = trigger("fired", fired_at=PAST)
WAITING = trigger("waiting")
TOPIC_PASSED = topic("t", archived_at=None)  # Termin unten gesetzt
PASSED = replace(TOPIC_PASSED, due_at=PAST)
COMING = replace(TOPIC_PASSED, due_at=FUTURE)


@pytest.mark.parametrize(
    "triggers,mode,topic_,hints,review,status,reason",
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
        ([], "any", None, 1, FUTURE, "due", "hint"),
        ([WAITING], "all", None, 2, PAST, "due", "hint"),
        # Topic-Termin
        ([trigger("d", kind="topic_date", target=None, status=None)], "any", PASSED, 0, FUTURE, "due", "topic_due"),
        ([trigger("d", kind="topic_date", target=None, status=None)], "any", COMING, 0, FUTURE, "waiting", None),
        ([trigger("d", kind="topic_date", target=None, status=None)], "any", PASSED, 1, FUTURE, "due", "hint"),
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
        ([], "any", None, 1, PAST, "due", "hint"),
    ],
)
def test_due_state_table(triggers, mode, topic_, hints, review, status, reason) -> None:  # type: ignore[no-untyped-def]
    state = due_state(replace(memo("n", review_at=review), trigger_mode=mode), triggers, topic_, hints, NOW)
    assert (state.status, state.reason) == (status, reason)


def test_a_snoozed_memo_is_due_by_the_same_rules() -> None:
    state = due_state(memo("n", status="snoozed", review_at=FUTURE), [FIRED], None, 0, NOW)
    assert (state.status, state.reason, state.fired) == ("due", "trigger", ("fired",))


@pytest.mark.parametrize("status", ["done", "dropped", "promoted"])
def test_finished_memos_are_never_due_whatever_happens(status: str) -> None:
    state = due_state(memo("n", status=status, archived=True, review_at=PAST), [FIRED], None, 3, NOW)
    assert (state.status, state.reason, state.fired) == (status, None, ())


def test_an_archived_or_deleted_memo_is_never_due() -> None:
    assert due_state(memo("n", archived=True, review_at=PAST), [FIRED], None, 1, NOW).status == "waiting"
    assert due_state(memo("n", review_at=PAST, deleted_at=PAST), [FIRED], None, 1, NOW).reason is None


def test_all_fired_is_reported_and_needs_triggers() -> None:
    assert due_state(memo("n"), [FIRED, FIRED], None, 0, NOW).all_fired is True
    assert due_state(memo("n"), [FIRED, WAITING], None, 0, NOW).all_fired is False
    assert due_state(memo("n"), [], None, 0, NOW).all_fired is False


def test_a_topic_date_in_the_trash_does_not_arrive() -> None:
    gone = replace(PASSED, deleted_at=PAST)
    state = due_state(memo("n"), [trigger("d", kind="topic_date", target=None, status=None)], gone, 0, NOW)
    assert state.status == "waiting"


def test_the_clock_decides() -> None:
    quiet = memo("n", review_at=NOW)
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
    check_new_trigger(memo("n"), "event", "Completed", None)
    check_new_trigger(memo("n"), "topic_date", None, COMING)
    for kind, status, topic_ in (("time", None, None), ("event", "Open", None), ("event", None, None)):
        with pytest.raises(InvalidInput):
            check_new_trigger(memo("n"), kind, status, topic_)
    topics: list[Topic | None] = [None, TOPIC_PASSED]
    for candidate in topics:
        with pytest.raises(MemosViolation) as error:
            check_new_trigger(memo("n"), "topic_date", None, candidate)
        assert error.value.code == "trigger_needs_topic_date"


def _hint(side: str = "memo", decided: bool = False) -> Hint:
    return Hint("x", side, "s", "o", "item_completed", NOW, NOW if decided else None)


def test_hint_decisions_belong_to_their_side() -> None:
    assert decision_options("memo") == ("keep", "detach", "drop", "promote")
    assert decision_options("item") == ("acknowledge",)
    check_decision(_hint(), "keep")
    check_decision(_hint("item"), "acknowledge")
    for hint, decision in ((_hint(), "acknowledge"), (_hint("item"), "keep")):
        with pytest.raises(InvalidInput):
            check_decision(hint, decision)


def test_a_decided_hint_cannot_be_decided_again() -> None:
    with pytest.raises(MemosViolation) as error:
        check_decision(_hint(decided=True), "keep")
    assert error.value.code == "hint_decided"


def test_only_the_closing_statuses_cause_a_hint() -> None:
    assert [cause_of_status(s) for s in ("Completed", "Rejected", "Open", "In progress")] == [
        "item_completed",
        "item_rejected",
        None,
        None,
    ]


def _open_hint(uid: str, created_at: datetime, decided: bool = False) -> Hint:
    return Hint(uid, "memo", "n", "item", "status_changed", created_at, NOW if decided else None)


EARLIER = NOW - timedelta(days=3)


@pytest.mark.parametrize(
    "triggers,topic_,hints,review,expected",
    [
        # Auslöser: das späteste Eintreten, ein Topic-Termin zählt mit seinem Termin
        ([trigger("a", fired_at=EARLIER), FIRED], None, [], FUTURE, PAST),
        (
            [trigger("d", kind="topic_date", target=None, status=None), trigger("a", fired_at=EARLIER)],
            PASSED,
            [],
            FUTURE,
            PAST,
        ),
        # Hinweis: der jüngste offene
        (
            [],
            None,
            [_open_hint("x", EARLIER), _open_hint("y", PAST), _open_hint("z", NOW, decided=True)],
            FUTURE,
            PAST,
        ),
        # Topic-Termin
        ([trigger("d", kind="topic_date", target=None, status=None)], PASSED, [], FUTURE, PAST),
        # Prüfdatum
        ([], None, [], EARLIER, EARLIER),
        # nicht fällig
        ([WAITING], None, [], FUTURE, None),
    ],
)
def test_due_since(triggers, topic_, hints, review, expected) -> None:  # type: ignore[no-untyped-def]
    n = memo("n", review_at=review)
    open_hints = [x for x in hints if x.is_open]
    state = due_state(n, triggers, topic_, len(open_hints), NOW)
    assert due_since(state, n, triggers, topic_, open_hints) == expected


def test_next_clock_due_is_the_earliest_future_review_date_or_topic_date() -> None:
    later = NOW + timedelta(days=5)
    memos = [
        memo("past", review_at=PAST),  # schon fällig: kein Termin mehr
        memo("now", review_at=NOW),  # gerade erreicht: zählt nicht mehr als künftig
        memo("far", review_at=later),
        memo("near", status="snoozed", review_at=FUTURE),
        memo("done", status="done", review_at=NOW + timedelta(hours=1)),
        memo("archived", archived=True, review_at=NOW + timedelta(hours=1)),
        memo("trash", review_at=NOW + timedelta(hours=1), deleted_at=PAST),
    ]
    topics = [
        replace(topic("t1"), due_at=NOW + timedelta(hours=12)),
        replace(topic("old", archived_at=PAST), due_at=NOW + timedelta(hours=2)),
        replace(topic("gone", deleted_at=PAST), due_at=NOW + timedelta(hours=2)),
    ]

    assert next_clock_due(memos, [], NOW) == FUTURE
    assert next_clock_due(memos, topics, NOW) == NOW + timedelta(hours=12)
    assert next_clock_due([memo("past", review_at=PAST)], [], NOW) is None

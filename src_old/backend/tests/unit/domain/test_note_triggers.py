"""Which triggers have arrived and when a note is due: pure functions, the clock is a parameter."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from todo_viewer.domain.item import Status
from todo_viewer.domain.notes import (
    DEFAULT_REVIEW_DAYS,
    LinkTarget,
    Note,
    NoteReason,
    NoteStatus,
    TargetKind,
    Trigger,
    TriggerKind,
    TriggerMode,
    default_review_at,
    evaluate,
    event_hit,
    trigger_arrived,
)

NOW = datetime(2027, 12, 11, 9, 0, tzinfo=UTC)
PAST, FUTURE = NOW - timedelta(hours=1), NOW + timedelta(hours=1)
ITEM = LinkTarget(TargetKind.ITEM, "p", "STORY-001")


def time_trigger(at: datetime, id: int = 1, fired_at: datetime | None = None) -> Trigger:
    return Trigger(id=id, note="NOTE-001", kind=TriggerKind.TIME, at=at, fired_at=fired_at)


def event_trigger(status: str = Status.COMPLETED, id: int = 2, fired_at: datetime | None = None) -> Trigger:
    return Trigger(id=id, note="NOTE-001", kind=TriggerKind.EVENT, target=ITEM, target_status=status,
                   fired_at=fired_at)


def topic_trigger(id: int = 3) -> Trigger:
    return Trigger(id=id, note="NOTE-001", kind=TriggerKind.TOPIC_DUE)


def note(status: NoteStatus = NoteStatus.WAITING, review_at: datetime | None = FUTURE,
         mode: TriggerMode = TriggerMode.ANY) -> Note:
    return Note(project="p", label="NOTE-001", summary="s", status=status, review_at=review_at, trigger_mode=mode)


# ---------- single triggers ----------

def test_a_time_trigger_arrives_at_its_moment():
    assert trigger_arrived(time_trigger(PAST), NOW, None)
    assert trigger_arrived(time_trigger(NOW), NOW, None)
    assert not trigger_arrived(time_trigger(FUTURE), NOW, None)


def test_time_is_compared_as_a_moment_not_as_wall_clock_text():
    plus_two = timezone(timedelta(hours=2))
    assert trigger_arrived(time_trigger(datetime(2027, 12, 11, 10, 30, tzinfo=plus_two)), NOW, None)  # 08:30 UTC
    assert not trigger_arrived(time_trigger(datetime(2027, 12, 11, 11, 30, tzinfo=plus_two)), NOW, None)  # 09:30 UTC


def test_an_event_trigger_arrives_only_once_it_fired():
    assert not trigger_arrived(event_trigger(), NOW, None)
    assert trigger_arrived(event_trigger(fired_at=PAST), NOW, None)


def test_a_topic_trigger_follows_the_due_date_of_the_topic():
    assert not trigger_arrived(topic_trigger(), NOW, None)
    assert not trigger_arrived(topic_trigger(), NOW, FUTURE)
    assert trigger_arrived(topic_trigger(), NOW, PAST)


def test_a_fired_trigger_stays_arrived():
    assert trigger_arrived(time_trigger(FUTURE, fired_at=PAST), NOW, None)


def test_the_result_does_not_depend_on_when_it_is_read():
    trigger = time_trigger(PAST)
    assert trigger_arrived(trigger, NOW, None) and trigger_arrived(trigger, NOW + timedelta(days=400), None)


# ---------- events ----------

def test_an_event_hits_when_the_item_reaches_the_target_status():
    assert event_hit(event_trigger(Status.COMPLETED), Status.COMPLETED)
    assert not event_hit(event_trigger(Status.COMPLETED), Status.REJECTED)


def test_a_trigger_that_has_fired_or_is_no_event_does_not_hit_again():
    assert not event_hit(event_trigger(fired_at=PAST), Status.COMPLETED)
    assert not event_hit(time_trigger(PAST), Status.COMPLETED)


def test_open_is_not_a_target_status():
    assert not event_hit(event_trigger(Status.OPEN), Status.OPEN)


# ---------- review date ----------

def test_the_default_review_date_is_30_days_away():
    assert DEFAULT_REVIEW_DAYS == 30
    assert default_review_at(NOW, DEFAULT_REVIEW_DAYS) == NOW + timedelta(days=30)


def test_the_review_date_follows_the_option():
    assert default_review_at(NOW, 7) == NOW + timedelta(days=7)


# ---------- evaluation ----------

def test_a_note_without_triggers_waits_until_its_review_date():
    assert evaluate(note(review_at=FUTURE), [], None, NOW).status is NoteStatus.WAITING
    due = evaluate(note(review_at=PAST), [], None, NOW)
    assert (due.status, due.reason) == (NoteStatus.DUE, NoteReason.REVIEW_EXPIRED)


def test_the_review_date_applies_to_notes_with_open_triggers_too():
    due = evaluate(note(review_at=PAST), [time_trigger(FUTURE)], None, NOW)
    assert (due.status, due.reason) == (NoteStatus.DUE, NoteReason.REVIEW_EXPIRED)


def test_one_arrived_trigger_makes_the_note_due_in_mode_any():
    result = evaluate(note(), [time_trigger(PAST, 1), event_trigger(id=2)], None, NOW)

    assert (result.status, result.reason, result.fired, result.all_fired) == (
        NoteStatus.DUE, NoteReason.TRIGGER, (1,), False)


def test_mode_all_needs_every_trigger():
    waiting = evaluate(note(mode=TriggerMode.ALL), [time_trigger(PAST, 1), event_trigger(id=2)], None, NOW)
    assert (waiting.status, waiting.fired) == (NoteStatus.WAITING, (1,))

    both = evaluate(note(mode=TriggerMode.ALL), [time_trigger(PAST, 1), event_trigger(id=2, fired_at=PAST)], None, NOW)
    assert (both.status, both.all_fired) == (NoteStatus.DUE, True)


def test_all_arrived_is_reported_in_both_modes():
    triggers = [time_trigger(PAST, 1), event_trigger(id=2, fired_at=PAST)]

    assert evaluate(note(mode=TriggerMode.ANY), triggers, None, NOW).all_fired
    assert evaluate(note(mode=TriggerMode.ALL), triggers, None, NOW).all_fired


def test_a_note_without_triggers_has_not_all_fired():
    assert not evaluate(note(), [], None, NOW).all_fired


def test_a_due_topic_trigger_is_reported_as_topic_due():
    result = evaluate(note(), [topic_trigger()], PAST, NOW)

    assert (result.status, result.reason) == (NoteStatus.DUE, NoteReason.TOPIC_DUE)


def test_a_snoozed_note_is_evaluated_like_a_waiting_one():
    assert evaluate(note(NoteStatus.SNOOZED), [time_trigger(FUTURE)], None, NOW).status is NoteStatus.SNOOZED
    assert evaluate(note(NoteStatus.SNOOZED), [time_trigger(PAST)], None, NOW).status is NoteStatus.DUE


def test_closed_notes_are_never_due():
    for status in (NoteStatus.DONE, NoteStatus.DROPPED, NoteStatus.PROMOTED):
        result = evaluate(note(status, review_at=PAST), [time_trigger(PAST)], None, NOW)
        assert (result.status, result.reason) == (status, None)


def test_a_due_note_stays_due_when_read_later():
    later = NOW + timedelta(days=90)

    assert evaluate(note(review_at=PAST), [], None, NOW).status is NoteStatus.DUE
    assert evaluate(note(review_at=PAST), [], None, later).status is NoteStatus.DUE

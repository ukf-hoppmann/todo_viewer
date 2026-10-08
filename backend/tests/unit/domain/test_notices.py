"""Notices between notes and items: which decisions a side has, and how an open notice makes a note due."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from todo_viewer.domain.errors import (
    DecisionNotAvailableError,
    InvalidValueError,
    NoticeAlreadyDecidedError,
)
from todo_viewer.domain.item import Status
from todo_viewer.domain.notes import (
    LinkTarget,
    Note,
    NoteReason,
    NoteStatus,
    Notice,
    NoticeCause,
    NoticeDecision,
    NoticeSide,
    TargetKind,
    Trigger,
    TriggerKind,
    check_decision,
    evaluate,
    item_status_notice_cause,
)

NOW = datetime(2027, 12, 11, 9, 0, tzinfo=UTC)
PAST = NOW - timedelta(hours=1)
ITEM = LinkTarget(TargetKind.ITEM, "p", "STORY-001")
NOTE_TARGET = LinkTarget(TargetKind.NOTE, "p", "NOTE-001")


def notice(side: NoticeSide = NoticeSide.NOTE, decided_at: datetime | None = None) -> Notice:
    return Notice(id=1, side=side, project="p", label="NOTE-001" if side is NoticeSide.NOTE else "STORY-001",
                  cause=NoticeCause.ITEM_COMPLETED if side is NoticeSide.NOTE else NoticeCause.NOTE_DROPPED,
                  counterpart=ITEM if side is NoticeSide.NOTE else NOTE_TARGET, created_at=PAST,
                  decided_at=decided_at, decision=None if decided_at is None else NoticeDecision.KEEP)


def note(status: NoteStatus = NoteStatus.WAITING, review_at: datetime | None = None,
         deleted: datetime | None = None) -> Note:
    return Note(project="p", label="NOTE-001", summary="s", status=status, review_at=review_at, deleted=deleted)


def test_a_notice_is_open_until_it_is_decided():
    assert notice().is_open
    assert not notice(decided_at=NOW).is_open


def test_only_a_completed_or_rejected_item_causes_a_notice():
    assert item_status_notice_cause(Status.COMPLETED) is NoticeCause.ITEM_COMPLETED
    assert item_status_notice_cause(Status.REJECTED) is NoticeCause.ITEM_REJECTED
    for status in (Status.OPEN, Status.IN_PROGRESS, Status.AWAITING_CONFIRMATION):
        assert item_status_notice_cause(status) is None


@pytest.mark.parametrize("decision", [NoticeDecision.KEEP, NoticeDecision.DETACH, NoticeDecision.DROP])
def test_a_note_side_notice_offers_keep_detach_and_drop(decision: NoticeDecision):
    check_decision(notice(), decision)


def test_promote_is_a_known_option_that_is_not_available_yet():
    with pytest.raises(DecisionNotAvailableError) as unavailable:
        check_decision(notice(), NoticeDecision.PROMOTE)
    assert unavailable.value.code == "decision_not_available"


def test_an_item_side_notice_offers_only_acknowledge():
    check_decision(notice(NoticeSide.ITEM), NoticeDecision.ACKNOWLEDGE)
    for decision in (NoticeDecision.KEEP, NoticeDecision.DETACH, NoticeDecision.DROP):
        with pytest.raises(InvalidValueError):
            check_decision(notice(NoticeSide.ITEM), decision)


def test_a_note_side_notice_does_not_accept_acknowledge():
    with pytest.raises(InvalidValueError):
        check_decision(notice(), NoticeDecision.ACKNOWLEDGE)


def test_a_decided_notice_cannot_be_decided_again():
    with pytest.raises(NoticeAlreadyDecidedError) as decided:
        check_decision(notice(decided_at=NOW), NoticeDecision.KEEP)
    assert decided.value.code == "notice_already_decided"


# --- due by notice ---

def test_a_note_with_an_open_notice_is_due_with_the_reason_notice():
    result = evaluate(note(review_at=NOW + timedelta(days=5)), [], None, NOW, open_notices=1)
    assert (result.status, result.reason) == (NoteStatus.DUE, NoteReason.NOTICE)


def test_a_note_without_an_open_notice_is_not_due_by_notices():
    result = evaluate(note(review_at=NOW + timedelta(days=5)), [], None, NOW, open_notices=0)
    assert (result.status, result.reason) == (NoteStatus.WAITING, None)


@pytest.mark.parametrize("status", [NoteStatus.DONE, NoteStatus.DROPPED, NoteStatus.PROMOTED])
def test_a_closed_note_is_never_due_by_a_notice(status: NoteStatus):
    assert evaluate(note(status), [], None, NOW, open_notices=2).status is status


def test_a_deleted_note_is_never_due_by_a_notice():
    assert evaluate(note(deleted=PAST), [], None, NOW, open_notices=1).reason is None


def test_a_snoozed_note_becomes_due_by_a_notice():
    assert evaluate(note(NoteStatus.SNOOZED), [], None, NOW, open_notices=1).status is NoteStatus.DUE


def test_the_reason_is_the_first_that_applies_trigger_notice_topic_due_review_expired():
    time_trigger = Trigger(id=1, note="NOTE-001", kind=TriggerKind.TIME, at=PAST)
    topic_trigger = Trigger(id=2, note="NOTE-001", kind=TriggerKind.TOPIC_DUE)
    expired = note(review_at=PAST)
    assert evaluate(expired, [time_trigger], None, NOW, open_notices=1).reason is NoteReason.TRIGGER
    assert evaluate(expired, [topic_trigger], PAST, NOW, open_notices=1).reason is NoteReason.NOTICE
    assert evaluate(expired, [topic_trigger], PAST, NOW, open_notices=0).reason is NoteReason.TOPIC_DUE
    assert evaluate(expired, [], None, NOW, open_notices=1).reason is NoteReason.NOTICE
    assert evaluate(expired, [], None, NOW, open_notices=0).reason is NoteReason.REVIEW_EXPIRED

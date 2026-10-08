"""Deciding notices through NoteService: every option ends in the state it promises."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from tests.unit.application.test_note_service import START, P, Q, World, event, story
from todo_viewer.domain.errors import (
    DecisionNotAvailableError,
    InvalidValueError,
    NoteLifecycleError,
    NoticeAlreadyDecidedError,
    NoticeNotFoundError,
    VersionConflictError,
)
from todo_viewer.domain.notes import (
    LinkRole,
    LinkTarget,
    NewNotice,
    NoteReason,
    NoteStatus,
    Notice,
    NoticeCause,
    NoticeDecision,
    NoticeSide,
    TargetKind,
)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def noticed_note(world: World, item: str = "STORY-001", role: LinkRole = LinkRole.REFERENCE) -> tuple[str, Notice]:
    """A note that links to the item and has an open notice about it."""
    label = world.service.create(P, "idea").note.label
    world.service.add_link(P, label, story(item), role)
    notice = world.service.add_notice(NewNotice(NoticeSide.NOTE, P, label, NoticeCause.ITEM_COMPLETED, story(item)))
    return label, notice


def test_an_open_notice_makes_the_note_due_with_the_reason_notice(world: World):
    label, _ = noticed_note(world)

    view = world.service.show(P, label)

    assert (view.evaluation.status, view.evaluation.reason) == (NoteStatus.DUE, NoteReason.NOTICE)
    assert [n.cause for n in view.open_notices] == [NoticeCause.ITEM_COMPLETED]
    assert [v.note.label for v in world.service.due(P)] == [label]


def test_keep_closes_the_notice_keeps_the_link_and_moves_the_review_date(world: World):
    label, notice = noticed_note(world)
    world.clock.advance(days=10)

    result = world.service.decide(notice.id, NoticeDecision.KEEP)

    assert (result.notice.decision, result.notice.decided_at) == (NoticeDecision.KEEP, world.clock.now)
    assert [link.target for link in world.service.links_of(P, label)] == [story()]
    assert result.note is not None
    assert result.note.note.review_at == START + timedelta(days=40)
    assert (result.note.evaluation.status, result.note.open_notices) == (NoteStatus.WAITING, ())


def test_detach_removes_the_reference_link_to_the_item_and_closes_the_notice(world: World):
    label, notice = noticed_note(world)
    world.service.add_link(P, label, story("STORY-002"), LinkRole.REFERENCE)

    result = world.service.decide(notice.id, NoticeDecision.DETACH)

    assert [link.target.label for link in world.service.links_of(P, label)] == ["STORY-002"]
    assert result.notice.decision is NoticeDecision.DETACH and not result.notice.is_open
    assert result.note is not None and result.note.evaluation.status is NoteStatus.WAITING


def test_detach_leaves_a_trigger_link_to_the_same_item_alone(world: World):
    label, notice = noticed_note(world)
    world.service.add_trigger(P, label, event("STORY-001"))

    world.service.decide(notice.id, NoticeDecision.DETACH)

    assert [link.role for link in world.service.links_of(P, label)] == [LinkRole.TRIGGER]


def test_drop_drops_the_note_and_closes_the_notice(world: World):
    label, notice = noticed_note(world)

    result = world.service.decide(notice.id, NoticeDecision.DROP)

    assert result.note is not None
    assert (result.note.note.status, result.note.note.archived) == (NoteStatus.DROPPED, True)
    assert not result.notice.is_open and result.notice.decision is NoticeDecision.DROP


def test_promote_is_refused_until_it_is_connected_and_the_notice_stays_open(world: World):
    label, notice = noticed_note(world)

    with pytest.raises(DecisionNotAvailableError):
        world.service.decide(notice.id, NoticeDecision.PROMOTE)

    assert world.service.show(P, label).evaluation.reason is NoteReason.NOTICE


def test_a_decided_notice_cannot_be_decided_again(world: World):
    _, notice = noticed_note(world)
    world.service.decide(notice.id, NoticeDecision.KEEP)

    with pytest.raises(NoticeAlreadyDecidedError):
        world.service.decide(notice.id, NoticeDecision.DETACH)


def test_an_unknown_notice_is_an_error(world: World):
    with pytest.raises(NoticeNotFoundError):
        world.service.decide(404, NoticeDecision.KEEP)


def test_a_decision_of_the_other_side_is_refused(world: World):
    _, notice = noticed_note(world)

    with pytest.raises(InvalidValueError):
        world.service.decide(notice.id, NoticeDecision.ACKNOWLEDGE)


def test_a_stale_version_is_refused_and_the_notice_stays_open(world: World):
    label, notice = noticed_note(world)
    stale = world.service.show(P, label).note.version
    world.service.edit(P, label, stale, summary="changed")

    with pytest.raises(VersionConflictError):
        world.service.decide(notice.id, NoticeDecision.KEEP, version=stale)

    assert world.service.show(P, label).evaluation.reason is NoteReason.NOTICE


def test_a_closed_note_cannot_keep_or_detach(world: World):
    label, notice = noticed_note(world)
    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DONE)

    with pytest.raises(NoteLifecycleError):
        world.service.decide(notice.id, NoticeDecision.KEEP)


def test_an_item_side_notice_is_only_acknowledged(world: World):
    label = world.service.create(P, "idea").note.label
    notice = world.service.add_notice(NewNotice(NoticeSide.ITEM, P, "STORY-001", NoticeCause.NOTE_DROPPED,
                                                LinkTarget(TargetKind.NOTE, P, label)))
    with pytest.raises(InvalidValueError):
        world.service.decide(notice.id, NoticeDecision.KEEP)

    result = world.service.decide(notice.id, NoticeDecision.ACKNOWLEDGE)

    assert result.note is None
    assert (result.notice.decision, result.notice.is_open) == (NoticeDecision.ACKNOWLEDGE, False)
    assert world.service.show(P, label).evaluation.status is NoteStatus.WAITING  # an item notice never makes it due


def test_notices_are_listed_per_side_and_open(world: World):
    label, notice = noticed_note(world)
    world.service.decide(notice.id, NoticeDecision.KEEP)
    again = world.service.add_notice(NewNotice(NoticeSide.NOTE, P, label, NoticeCause.ITEM_REJECTED, story()))

    assert [n.id for n in world.service.notices(P, label, NoticeSide.NOTE, open_only=True)] == [again.id]
    assert [n.id for n in world.service.notices(P, label, NoticeSide.NOTE, open_only=False)] == [notice.id, again.id]
    assert world.service.notices(Q, "STORY-001", NoticeSide.ITEM, open_only=False) == []


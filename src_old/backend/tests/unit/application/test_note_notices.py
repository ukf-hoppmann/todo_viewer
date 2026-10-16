"""Notices to notes when a linked item completes, is rejected, is deleted, or changes its type.

One row of the matrix per test: cause x link role, the state of the note, the project of the item.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.application.test_note_service import P, Q, World, event, story
from todo_viewer.domain.item import Status
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


def linked_note(world: World, role: LinkRole = LinkRole.REFERENCE, item: str = "STORY-001",
                project: str = P, note_project: str = P) -> str:
    label = world.service.create(note_project, "idea").note.label
    world.service.add_link(note_project, label, story(item, project), role)
    return label


def notices(world: World, label: str, project: str = P) -> list[Notice]:
    return world.service.notices(project, label, NoticeSide.NOTE, open_only=False)


@pytest.mark.parametrize(("status", "cause"), [(Status.COMPLETED, NoticeCause.ITEM_COMPLETED),
                                               (Status.REJECTED, NoticeCause.ITEM_REJECTED)])
def test_a_note_with_a_reference_link_is_told_that_the_item_closed(world: World, status: str, cause: NoticeCause):
    label = linked_note(world)

    world.service.item_status_changed(P, "STORY-001", status)

    [notice] = notices(world, label)
    assert (notice.side, notice.project, notice.label, notice.cause) == (NoticeSide.NOTE, P, label, cause)
    assert notice.counterpart == story() and notice.is_open
    view = world.service.show(P, label)
    assert (view.evaluation.status, view.evaluation.reason) == (NoteStatus.DUE, NoteReason.NOTICE)


@pytest.mark.parametrize("status", [Status.OPEN, Status.IN_PROGRESS, Status.AWAITING_CONFIRMATION])
def test_the_other_statuses_cause_no_notice(world: World, status: str):
    label = linked_note(world)

    world.service.item_status_changed(P, "STORY-001", status)

    assert notices(world, label) == []


def test_a_trigger_link_causes_no_notice_the_trigger_decides(world: World):
    label = world.service.create(P, "idea").note.label
    world.service.add_trigger(P, label, event())

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert notices(world, label) == []
    view = world.service.show(P, label)
    assert (view.evaluation.status, view.evaluation.reason) == (NoteStatus.DUE, NoteReason.TRIGGER)


def test_an_origin_link_never_causes_a_notice(world: World):
    label = linked_note(world, LinkRole.ORIGIN)

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)
    world.service.item_deleted(P, "STORY-001")
    world.service.item_retyped(P, "STORY-001", "TASK-007")

    assert notices(world, label) == []


def test_a_reference_and_a_trigger_link_to_the_same_item_give_one_notice_and_a_trigger(world: World):
    label = linked_note(world)
    world.service.add_trigger(P, label, event())

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert [n.cause for n in notices(world, label)] == [NoticeCause.ITEM_COMPLETED]
    assert world.service.show(P, label).evaluation.reason is NoteReason.TRIGGER  # the trigger comes first


def test_closed_and_deleted_notes_are_not_told(world: World):
    finished = linked_note(world)
    trashed = linked_note(world)
    world.service.finish(P, finished, world.service.show(P, finished).note.version, NoteStatus.DONE)
    world.service.delete_note(P, trashed)

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert notices(world, finished) == [] and notices(world, trashed) == []


def test_every_note_that_links_the_item_is_told_also_from_another_project(world: World):
    here = linked_note(world)
    there = linked_note(world, item="STORY-001", project=P, note_project=Q)  # a note of project Q, item of project P
    elsewhere = linked_note(world, item="STORY-001", project=Q, note_project=Q)  # item of project Q: not this one

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert len(notices(world, here)) == 1
    assert len(notices(world, there, Q)) == 1
    assert notices(world, elsewhere, Q) == []


def test_a_second_change_to_the_same_status_does_not_add_a_second_open_notice(world: World):
    label = linked_note(world)
    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert len(notices(world, label)) == 1


def test_rejecting_after_completing_adds_a_notice_of_the_other_cause(world: World):
    label = linked_note(world)
    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    world.service.item_status_changed(P, "STORY-001", Status.REJECTED)

    assert [n.cause for n in notices(world, label)] == [NoticeCause.ITEM_COMPLETED, NoticeCause.ITEM_REJECTED]


def test_a_deleted_item_tells_the_notes_that_reference_it(world: World):
    label = linked_note(world)
    trigger_note = world.service.create(P, "waiting").note.label
    world.service.add_trigger(P, trigger_note, event())

    world.service.item_deleted(P, "STORY-001")

    [notice] = notices(world, label)
    assert (notice.cause, notice.counterpart) == (NoticeCause.ITEM_DELETED, story())
    assert notices(world, trigger_note) == []


def test_a_retyped_item_tells_its_notes_with_the_new_id_as_the_other_end(world: World):
    label = linked_note(world)
    world.repo.relink_item(P, "STORY-001", "TASK-007")  # what the retype use case does first

    world.service.item_retyped(P, "STORY-001", "TASK-007")

    [notice] = notices(world, label)
    assert (notice.cause, notice.counterpart) == (NoticeCause.ITEM_RETYPED, story("TASK-007"))
    assert world.service.links_of(P, label)[0].target == story("TASK-007")  # the link survived


def test_restoring_an_item_causes_no_notice_and_removes_none(world: World):
    label = linked_note(world)
    world.service.item_deleted(P, "STORY-001")

    world.service.item_status_changed(P, "STORY-001", Status.OPEN)  # a restored item keeps its status

    assert [n.cause for n in notices(world, label)] == [NoticeCause.ITEM_DELETED]
    assert notices(world, label)[0].is_open


def test_a_failure_while_telling_the_notes_does_not_reach_the_caller(world: World, monkeypatch: pytest.MonkeyPatch):
    label = linked_note(world)
    kept = linked_note(world)

    def broken(new: NewNotice) -> Notice:
        raise RuntimeError("database is locked")

    monkeypatch.setattr(world.repo, "add_notice", broken)

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)
    world.service.item_deleted(P, "STORY-001")
    world.service.item_retyped(P, "STORY-001", "TASK-007")

    monkeypatch.undo()
    assert notices(world, label) == [] and notices(world, kept) == []


def test_a_failure_for_one_note_does_not_stop_the_others(world: World, monkeypatch: pytest.MonkeyPatch):
    first, second = linked_note(world), linked_note(world)
    real = world.repo.add_notice

    def fails_once(new: NewNotice) -> Notice:
        if new.label == first:
            raise RuntimeError("boom")
        return real(new)

    monkeypatch.setattr(world.repo, "add_notice", fails_once)

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert notices(world, first) == [] and len(notices(world, second)) == 1



# ---------- the other direction: a note is dropped or promoted ----------

def item_notices(world: World, item: str = "STORY-001", project: str = P) -> list[Notice]:
    return world.service.notices(project, item, NoticeSide.ITEM, open_only=False)


@pytest.mark.parametrize(("target", "cause"), [(NoteStatus.DROPPED, NoticeCause.NOTE_DROPPED),
                                               (NoteStatus.PROMOTED, NoticeCause.NOTE_PROMOTED)])
def test_the_item_of_a_reference_link_is_told_that_the_note_was_dropped_or_promoted(
        world: World, target: NoteStatus, cause: NoticeCause):
    label = linked_note(world)

    world.service.finish(P, label, world.service.show(P, label).note.version, target)

    [notice] = item_notices(world)
    assert (notice.side, notice.project, notice.label, notice.cause) == (NoticeSide.ITEM, P, "STORY-001", cause)
    assert notice.counterpart == LinkTarget(TargetKind.NOTE, P, label) and notice.is_open


def test_a_note_that_is_done_tells_nobody(world: World):
    label = linked_note(world)

    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DONE)

    assert item_notices(world) == []


def test_a_note_with_two_items_tells_both(world: World):
    label = linked_note(world)
    world.service.add_link(P, label, story("STORY-002"), LinkRole.REFERENCE)

    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DROPPED)

    assert len(item_notices(world, "STORY-001")) == 1 and len(item_notices(world, "STORY-002")) == 1


def test_trigger_and_origin_links_tell_no_item(world: World):
    triggering = world.service.create(P, "waits").note.label
    world.service.add_trigger(P, triggering, event())
    origin = linked_note(world, LinkRole.ORIGIN)

    world.service.finish(P, triggering, world.service.show(P, triggering).note.version, NoteStatus.DROPPED)
    world.service.finish(P, origin, world.service.show(P, origin).note.version, NoteStatus.DROPPED)

    assert item_notices(world) == []


def test_links_to_topics_and_other_notes_tell_nobody(world: World):
    label = world.service.create(P, "idea").note.label
    other = world.service.create(P, "other").note.label
    world.service.add_link(P, label, LinkTarget(TargetKind.NOTE, P, other), LinkRole.REFERENCE)

    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DROPPED)

    assert item_notices(world) == []
    assert world.service.notices(P, other, NoticeSide.NOTE, open_only=False) == []


def test_a_note_without_links_tells_nobody(world: World):
    label = world.service.create(P, "idea").note.label

    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DROPPED)

    assert item_notices(world) == []


def test_the_item_of_another_project_is_told_in_its_own_project(world: World):
    label = linked_note(world, item="STORY-001", project=Q, note_project=P)

    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DROPPED)

    assert item_notices(world, project=Q)[0].project == Q
    assert item_notices(world, project=P) == []


def test_an_item_notice_never_makes_a_note_due(world: World):
    label = linked_note(world)
    other = linked_note(world)
    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DROPPED)

    assert world.service.show(P, other).evaluation.status is NoteStatus.WAITING
    assert world.service.due(P) == []


def test_dropping_through_a_notice_decision_tells_the_item_too(world: World):
    label = linked_note(world)
    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)
    [notice] = notices(world, label)

    world.service.decide(notice.id, NoticeDecision.DROP)

    assert [n.cause for n in item_notices(world)] == [NoticeCause.NOTE_DROPPED]


def test_a_failure_while_telling_the_item_does_not_stop_the_drop(world: World, monkeypatch: pytest.MonkeyPatch):
    label = linked_note(world)

    def broken(new: NewNotice) -> Notice:
        raise RuntimeError("database is locked")

    monkeypatch.setattr(world.repo, "add_notice", broken)

    view = world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DROPPED)

    assert (view.note.status, view.note.archived) == (NoteStatus.DROPPED, True)

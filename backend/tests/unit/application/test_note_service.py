"""NoteService: triggers, review date, snoozing, event hook, archive, and trash.

The notes port is the database adapter on a temporary SQLite file (the adapter is covered by the contract suite);
the backlog is the in-memory fake. The clock is fixed and moved by the tests.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tests.fakes import InMemoryBacklogRepository
from todo_viewer.application.services.notes import NoteService
from todo_viewer.domain.errors import (
    InvalidValueError,
    NoteLifecycleError,
    SourceGoneError,
    ValueRequiredError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Status
from todo_viewer.domain.notes import (
    LinkRole,
    LinkTarget,
    NewTrigger,
    NoteReason,
    NotesSettings,
    NoteStatus,
    TargetKind,
    TriggerKind,
    TriggerMode,
)
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.notes import DatabaseNoteRepository

START = datetime(2027, 12, 11, 9, 0, tzinfo=UTC)
P, Q = "proj", "other"


class Clock:
    def __init__(self) -> None:
        self.now = START

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta: float) -> None:
        self.now += timedelta(**delta)


class Sources:
    def all(self) -> list[Source]:
        return [Source(project=P, path="", backend="database", id="s1"),
                Source(project=Q, path="", backend="database", id="s2")]


def item(item_id: str, status: str = Status.OPEN) -> Item:
    return Item(id=item_id, title=item_id, project=P, status=status)


class World:
    def __init__(self, tmp_path: Path, settings: NotesSettings | None = None):
        self.clock = Clock()
        self.repo = DatabaseNoteRepository(Database(f"sqlite:///{tmp_path / 'todo.db'}"), self.clock)
        # The fake serves the same items for every source, so both projects know STORY-001 and STORY-002.
        self.backlogs = InMemoryBacklogRepository([item("STORY-001"), item("STORY-002", Status.COMPLETED)])
        self.service = NoteService(self.repo, Sources(), self.backlogs, settings, self.clock)  # type: ignore[arg-type]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def story(label: str = "STORY-001", project: str = P) -> LinkTarget:
    return LinkTarget(TargetKind.ITEM, project, label)


def event(label: str = "STORY-001", status: str = Status.COMPLETED, project: str = P) -> NewTrigger:
    return NewTrigger(TriggerKind.EVENT, target=story(label, project), target_status=status)


# ---------- review date ----------

def test_a_new_note_gets_a_review_date_30_days_ahead(world: World):
    view = world.service.create(P, "idea")

    assert view.note.review_at == START + timedelta(days=30)
    assert (view.evaluation.status, view.note.status) == (NoteStatus.WAITING, NoteStatus.WAITING)


def test_the_review_days_are_a_global_option(tmp_path: Path):
    world = World(tmp_path, NotesSettings(review_days=7))

    assert world.service.create(P, "idea").note.review_at == START + timedelta(days=7)


def test_a_given_review_date_is_kept(world: World):
    later = START + timedelta(days=3)

    assert world.service.create(P, "idea", review_at=later).note.review_at == later


def test_the_note_is_due_when_the_review_date_has_passed_and_stays_due(world: World):
    note = world.service.create(P, "idea").note
    world.clock.advance(days=31)

    first = world.service.show(P, note.label)
    world.clock.advance(days=60)
    later = world.service.show(P, note.label)

    assert (first.evaluation.status, first.evaluation.reason) == (NoteStatus.DUE, NoteReason.REVIEW_EXPIRED)
    assert later.evaluation.status is NoteStatus.DUE
    assert [v.note.label for v in world.service.due(P)] == [note.label]


def test_changing_the_text_sets_a_new_review_date(world: World):
    note = world.service.create(P, "idea", body="b").note
    world.clock.advance(days=20)

    edited = world.service.edit(P, note.label, note.version, summary="better idea")

    assert edited.note.review_at == world.clock.now + timedelta(days=30)
    assert edited.note.summary == "better idea"


def test_an_edit_without_a_text_change_keeps_the_review_date(world: World):
    note = world.service.create(P, "idea").note
    world.clock.advance(days=20)

    assert world.service.edit(P, note.label, note.version).note.review_at == note.review_at


def test_keeping_moves_the_review_date_only(world: World):
    note = world.service.create(P, "idea").note
    world.clock.advance(days=31)

    kept = world.service.keep(P, note.label, note.version)

    assert kept.evaluation.status is NoteStatus.WAITING
    assert kept.note.review_at == world.clock.now + timedelta(days=30)


def test_a_stale_version_is_refused(world: World):
    note = world.service.create(P, "idea").note
    world.clock.advance(days=1)
    world.service.keep(P, note.label, note.version)

    with pytest.raises(VersionConflictError):
        world.service.keep(P, note.label, note.version)


# ---------- time triggers ----------

def test_a_time_trigger_makes_the_note_due_without_any_session(world: World):
    note = world.service.create(P, "idea").note
    world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=START + timedelta(days=2)))
    assert world.service.show(P, note.label).evaluation.status is NoteStatus.WAITING

    world.clock.advance(days=2)
    view = world.service.show(P, note.label)

    assert (view.evaluation.status, view.evaluation.reason) == (NoteStatus.DUE, NoteReason.TRIGGER)
    assert view.evaluation.fired == (view.triggers[0].id,)


def test_a_time_trigger_needs_a_moment(world: World):
    note = world.service.create(P, "idea").note

    with pytest.raises(ValueRequiredError):
        world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME))


def test_two_triggers_are_reported_one_by_one_and_together(world: World):
    note = world.service.create(P, "idea", trigger_mode=TriggerMode.ALL).note
    first = world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=START + timedelta(days=1)))
    second = world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=START + timedelta(days=2)))

    world.clock.advance(days=1)
    one = world.service.show(P, note.label).evaluation
    world.clock.advance(days=1)
    both = world.service.show(P, note.label).evaluation

    assert (one.status, one.fired, one.all_fired) == (NoteStatus.WAITING, (first.id,), False)
    assert (both.status, both.fired, both.all_fired) == (NoteStatus.DUE, (first.id, second.id), True)


def test_a_topic_trigger_follows_the_topic_date(world: World):
    topic = world.repo.create_topic(P, "release", None, START + timedelta(days=5), 3)
    note = world.service.create(P, "idea", topic=topic.label).note
    world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.TOPIC_DUE))
    assert world.service.show(P, note.label).evaluation.status is NoteStatus.WAITING

    world.clock.advance(days=5)

    assert world.service.show(P, note.label).evaluation.reason is NoteReason.TOPIC_DUE


# ---------- event triggers ----------

def test_an_event_trigger_on_a_target_that_is_not_there_yet_waits(world: World):
    note = world.service.create(P, "idea").note

    trigger = world.service.add_trigger(P, note.label, event())

    assert (trigger.fired_at, trigger.already_met) == (None, False)
    assert trigger.link_id is not None
    assert world.service.show(P, note.label).evaluation.status is NoteStatus.WAITING


def test_an_event_whose_target_is_already_reached_fires_at_once_and_says_so(world: World):
    note = world.service.create(P, "idea").note

    trigger = world.service.add_trigger(P, note.label, event("STORY-002", Status.COMPLETED))

    assert (trigger.fired_at, trigger.already_met) == (START, True)
    assert world.service.show(P, note.label).evaluation.status is NoteStatus.DUE


def test_only_four_statuses_are_targets(world: World):
    note = world.service.create(P, "idea").note

    with pytest.raises(InvalidValueError):
        world.service.add_trigger(P, note.label, event(status=Status.OPEN))


def test_an_event_trigger_needs_a_target(world: World):
    note = world.service.create(P, "idea").note

    with pytest.raises(ValueRequiredError):
        world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.EVENT, target_status=Status.COMPLETED))


def test_an_unknown_project_for_the_target_is_refused(world: World):
    note = world.service.create(P, "idea").note

    with pytest.raises(SourceGoneError):
        world.service.add_trigger(P, note.label, event(project="nowhere"))


def test_a_status_change_fires_the_matching_triggers_only(world: World):
    a = world.service.create(P, "a").note
    b = world.service.create(P, "b").note
    world.service.add_trigger(P, a.label, event("STORY-001", Status.COMPLETED))
    world.service.add_trigger(P, b.label, event("STORY-001", Status.REJECTED))

    world.clock.advance(hours=1)
    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert world.service.show(P, a.label).evaluation.status is NoteStatus.DUE
    assert world.service.show(P, b.label).evaluation.status is NoteStatus.WAITING
    assert world.service.show(P, a.label).triggers[0].fired_at == world.clock.now


def test_a_status_without_a_matching_trigger_changes_nothing(world: World):
    a = world.service.create(P, "a").note
    world.service.add_trigger(P, a.label, event("STORY-001", Status.COMPLETED))

    world.service.item_status_changed(P, "STORY-001", Status.IN_PROGRESS)
    world.service.item_status_changed(P, "STORY-009", Status.COMPLETED)

    assert world.service.show(P, a.label).evaluation.fired == ()


def test_an_event_from_another_project_reaches_the_note(world: World):
    a = world.service.create(P, "a").note
    world.service.add_trigger(P, a.label, event("STORY-001", Status.COMPLETED, project=Q))

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)
    assert world.service.show(P, a.label).evaluation.status is NoteStatus.WAITING  # that is another item

    world.service.item_status_changed(Q, "STORY-001", Status.COMPLETED)
    assert world.service.show(P, a.label).evaluation.status is NoteStatus.DUE


def test_a_fired_trigger_stays_fired_when_the_item_is_reopened(world: World):
    a = world.service.create(P, "a").note
    world.service.add_trigger(P, a.label, event("STORY-001", Status.COMPLETED))
    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)
    fired_at = world.service.show(P, a.label).triggers[0].fired_at

    world.clock.advance(days=1)
    world.service.item_status_changed(P, "STORY-001", Status.IN_PROGRESS)
    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert world.service.show(P, a.label).triggers[0].fired_at == fired_at


def test_a_closed_note_ignores_events(world: World):
    a = world.service.create(P, "a").note
    world.service.add_trigger(P, a.label, event("STORY-001", Status.COMPLETED))
    world.service.finish(P, a.label, world.service.show(P, a.label).note.version, NoteStatus.DONE)

    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)

    assert world.repo.triggers_of(P, a.label)[0].fired_at is None


# ---------- snoozing ----------

def test_snoozing_resets_the_fired_triggers_and_waits_again(world: World):
    note = world.service.create(P, "idea").note
    world.service.add_trigger(P, note.label, event("STORY-001", Status.COMPLETED))
    world.service.item_status_changed(P, "STORY-001", Status.COMPLETED)
    world.service.add_trigger(P, note.label, event("STORY-002", Status.COMPLETED))  # fires at once
    due = world.service.show(P, note.label)
    assert due.evaluation.status is NoteStatus.DUE

    snoozed = world.service.snooze(P, note.label, due.note.version)

    assert snoozed.note.status is NoteStatus.SNOOZED
    assert snoozed.note.review_at == world.clock.now + timedelta(days=30)
    assert all(t.fired_at is None and not t.already_met for t in snoozed.triggers)
    assert snoozed.evaluation.status is NoteStatus.SNOOZED  # waiting again, not due


def test_snoozing_with_a_new_time_replaces_the_old_triggers(world: World):
    note = world.service.create(P, "idea").note
    world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=START + timedelta(days=1)))
    world.clock.advance(days=2)
    tomorrow = world.clock.now + timedelta(days=1)

    snoozed = world.service.snooze(P, note.label, world.service.show(P, note.label).note.version,
                                   trigger=NewTrigger(TriggerKind.TIME, at=tomorrow))

    assert [t.at for t in snoozed.triggers] == [tomorrow]
    assert snoozed.evaluation.status is NoteStatus.SNOOZED
    world.clock.advance(days=1)
    assert world.service.show(P, note.label).evaluation.status is NoteStatus.DUE


def test_snoozing_with_a_new_event_replaces_the_old_triggers(world: World):
    note = world.service.create(P, "idea").note
    world.service.add_trigger(P, note.label, event("STORY-002", Status.COMPLETED))

    snoozed = world.service.snooze(P, note.label, world.service.show(P, note.label).note.version,
                                   trigger=event("STORY-001", Status.IN_PROGRESS))

    assert [t.target for t in snoozed.triggers] == [story("STORY-001")]
    assert snoozed.evaluation.status is NoteStatus.SNOOZED
    world.service.item_status_changed(P, "STORY-001", Status.IN_PROGRESS)
    assert world.service.show(P, note.label).evaluation.status is NoteStatus.DUE


def test_a_snoozed_note_can_be_snoozed_again_and_a_due_one_stays_due_until_handled(world: World):
    note = world.service.create(P, "idea").note
    world.clock.advance(days=31)
    assert world.service.show(P, note.label).evaluation.status is NoteStatus.DUE
    assert world.service.due(P)

    snoozed = world.service.snooze(P, note.label, note.version)
    again = world.service.snooze(P, note.label, snoozed.note.version, review_at=world.clock.now + timedelta(days=1))

    assert again.note.review_at == world.clock.now + timedelta(days=1)
    assert world.service.due(P) == []


# ---------- archive ----------

@pytest.mark.parametrize("target", [NoteStatus.DONE, NoteStatus.DROPPED, NoteStatus.PROMOTED])
def test_a_finished_note_leaves_the_default_lists_and_is_in_the_archive(world: World, target: NoteStatus):
    note = world.service.create(P, "idea").note
    keep = world.service.create(P, "other").note
    world.clock.advance(days=60)

    done = world.service.finish(P, note.label, note.version, target)

    assert (done.note.status, done.note.archived, done.evaluation.status) == (target, True, target)
    assert [v.note.label for v in world.service.overview(P)] == [keep.label]
    assert [v.note.label for v in world.service.due(P)] == [keep.label]
    assert [v.note.label for v in world.service.overview(P, archived=True)] == [note.label]


def test_finishing_needs_a_closing_status_and_an_open_note(world: World):
    note = world.service.create(P, "idea").note

    with pytest.raises(NoteLifecycleError):
        world.service.finish(P, note.label, note.version, NoteStatus.DUE)
    done = world.service.finish(P, note.label, note.version, NoteStatus.DONE)
    with pytest.raises(NoteLifecycleError):
        world.service.finish(P, note.label, done.note.version, NoteStatus.DROPPED)


def test_restoring_from_the_archive_makes_the_note_wait_with_a_new_date(world: World):
    note = world.service.create(P, "idea").note
    done = world.service.finish(P, note.label, note.version, NoteStatus.DONE)
    world.clock.advance(days=100)

    back = world.service.restore_note(P, note.label)

    assert (back.note.status, back.note.archived, back.note.deleted) == (NoteStatus.WAITING, False, None)
    assert back.note.review_at == world.clock.now + timedelta(days=30)
    assert back.note.version != done.note.version
    assert [v.note.label for v in world.service.overview(P)] == [note.label]
    assert world.service.overview(P, archived=True) == []


# ---------- trash ----------

def test_a_deleted_note_is_in_the_trash_and_can_be_restored(world: World):
    note = world.service.create(P, "idea").note

    world.service.delete_note(P, note.label)

    assert world.service.overview(P) == []
    assert [v.note.label for v in world.service.trash(P).notes] == [note.label]
    with pytest.raises(NoteLifecycleError):
        world.service.delete_note(P, note.label)
    back = world.service.restore_note(P, note.label)
    assert back.note.deleted is None and back.note.status is NoteStatus.WAITING
    assert world.service.trash(P).notes == []


def test_a_deleted_note_is_never_due(world: World):
    note = world.service.create(P, "idea").note
    world.service.delete_note(P, note.label)
    world.clock.advance(days=90)

    assert world.service.due(P) == []


def test_the_label_of_a_deleted_note_is_not_reused(world: World):
    note = world.service.create(P, "idea").note
    world.service.delete_note(P, note.label)

    assert world.service.create(P, "next").note.label == "NOTE-002"


def test_only_a_note_in_the_trash_can_be_purged(world: World):
    note = world.service.create(P, "idea").note

    with pytest.raises(NoteLifecycleError):
        world.service.purge_note(P, note.label)
    world.service.delete_note(P, note.label)
    world.service.purge_note(P, note.label)

    assert world.service.trash(P).notes == []
    assert world.service.create(P, "next").note.label == "NOTE-002"


def test_a_topic_with_content_is_deleted_only_with_the_cascade(world: World):
    topic = world.repo.create_topic(P, "t", None, None, 3)
    sub = world.repo.create_topic(P, "sub", topic.label, None, 3)
    note = world.service.create(P, "idea", topic=sub.label).note

    with pytest.raises(NoteLifecycleError) as caught:
        world.service.delete_topic(P, topic.label, cascade=False)
    assert caught.value.code == "topic_has_content"

    world.service.delete_topic(P, topic.label, cascade=True)
    trash = world.service.trash(P)
    assert (world.repo.list_topics(P), world.service.overview(P)) == ([], [])
    assert ([t.label for t in trash.topics], [v.note.label for v in trash.notes]) == (
        [topic.label, sub.label], [note.label])


def test_restoring_a_topic_needs_its_parent_and_brings_back_what_went_with_it(world: World):
    topic = world.repo.create_topic(P, "t", None, None, 3)
    sub = world.repo.create_topic(P, "sub", topic.label, None, 3)
    note = world.service.create(P, "idea", topic=sub.label).note
    world.service.delete_topic(P, topic.label, cascade=True)

    with pytest.raises(NoteLifecycleError) as caught:
        world.service.restore_topic(P, sub.label)
    assert caught.value.code == "topic_deleted"

    world.service.restore_topic(P, topic.label)
    assert [t.label for t in world.repo.list_topics(P)] == [topic.label, sub.label]
    assert [v.note.label for v in world.service.overview(P)] == [note.label]
    assert world.service.trash(P).topics == []


def test_purging_a_topic_removes_it_with_its_notes_in_the_trash(world: World):
    topic = world.repo.create_topic(P, "t", None, None, 3)
    world.service.create(P, "idea", topic=topic.label)
    world.service.delete_topic(P, topic.label, cascade=True)

    world.service.purge_topic(P, topic.label)

    assert world.service.trash(P).topics == [] and world.service.trash(P).notes == []
    assert world.repo.create_topic(P, "next", None, None, 3).label == "TOPIC-002"
    assert world.service.create(P, "next").note.label == "NOTE-002"


def test_links_survive_the_trash(world: World):
    note = world.service.create(P, "idea").note
    world.repo.add_link(P, note.label, story(), LinkRole.REFERENCE)

    world.service.delete_note(P, note.label)
    world.service.restore_note(P, note.label)

    assert [link.target for link in world.repo.links_of(P, note.label)] == [story()]

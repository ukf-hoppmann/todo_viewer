"""Lifecycle of notes: finishing, snoozing, archive, trash, and the topic cascade."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from todo_viewer.domain.errors import NoteLifecycleError
from todo_viewer.domain.note_lifecycle import (
    check_delete_note,
    check_purge_note,
    finish_changes,
    keep_changes,
    plan_topic_delete,
    plan_topic_purge,
    plan_topic_restore,
    restore_note_changes,
    snooze_changes,
)
from todo_viewer.domain.notes import Note, NoteStatus, Topic

NOW = datetime(2027, 12, 11, 9, 0, tzinfo=UTC)
EARLIER = NOW - timedelta(days=3)


def note(status: NoteStatus = NoteStatus.WAITING, label: str = "NOTE-001", topic: str | None = None,
         archived: bool = False, deleted: datetime | None = None) -> Note:
    return Note(project="p", label=label, summary="s", status=status, topic=topic, archived=archived,
                deleted=deleted)


def topic(label: str, parent: str | None = None, deleted: datetime | None = None) -> Topic:
    return Topic(project="p", label=label, name=label, parent=parent, deleted=deleted)


def code(call) -> str:
    with pytest.raises(NoteLifecycleError) as caught:
        call()
    return caught.value.code


# ---------- finishing and the archive ----------

@pytest.mark.parametrize("target", [NoteStatus.DONE, NoteStatus.DROPPED, NoteStatus.PROMOTED])
@pytest.mark.parametrize("start", [NoteStatus.WAITING, NoteStatus.SNOOZED])
def test_finishing_moves_the_note_to_the_archive(start: NoteStatus, target: NoteStatus):
    changes = finish_changes(note(start), target)

    assert (changes.status, changes.archived) == (target, True)


def test_a_note_can_be_closed_from_the_due_state_too():
    # `due` is derived; the stored status is still waiting
    assert finish_changes(note(NoteStatus.WAITING), NoteStatus.DONE).archived is True


@pytest.mark.parametrize("target", [NoteStatus.WAITING, NoteStatus.SNOOZED, NoteStatus.DUE])
def test_only_closing_statuses_finish_a_note(target: NoteStatus):
    assert code(lambda: finish_changes(note(), target)) == "note_target_invalid"


def test_a_closed_note_cannot_be_closed_again():
    assert code(lambda: finish_changes(note(NoteStatus.DONE, archived=True), NoteStatus.DROPPED)) == "note_closed"


def test_a_note_in_the_trash_cannot_be_finished():
    assert code(lambda: finish_changes(note(deleted=EARLIER), NoteStatus.DONE)) == "note_deleted"


# ---------- snoozing and keeping ----------

def test_snoozing_sets_the_state_and_a_new_review_date():
    changes = snooze_changes(note(), NOW, 30)

    assert (changes.status, changes.review_at) == (NoteStatus.SNOOZED, NOW + timedelta(days=30))


def test_snoozing_may_name_the_review_date():
    later = NOW + timedelta(days=2)

    assert snooze_changes(note(), NOW, 30, later).review_at == later


def test_a_closed_note_cannot_be_snoozed():
    assert code(lambda: snooze_changes(note(NoteStatus.DONE, archived=True), NOW, 30)) == "note_closed"


def test_keeping_only_moves_the_review_date():
    changes = keep_changes(note(), NOW, 30)

    assert (changes.review_at, changes.status) == (NOW + timedelta(days=30), None)


def test_a_note_in_the_trash_cannot_be_kept():
    assert code(lambda: keep_changes(note(deleted=EARLIER), NOW, 30)) == "note_deleted"


# ---------- restoring a note ----------

@pytest.mark.parametrize("closed", [NoteStatus.DONE, NoteStatus.DROPPED, NoteStatus.PROMOTED])
def test_a_note_from_the_archive_comes_back_waiting_with_a_new_review_date(closed: NoteStatus):
    changes = restore_note_changes(note(closed, archived=True), [], NOW, 30)

    assert (changes.status, changes.archived, changes.review_at) == (
        NoteStatus.WAITING, False, NOW + timedelta(days=30))


def test_a_note_from_the_trash_comes_back_waiting_too():
    changes = restore_note_changes(note(NoteStatus.SNOOZED, deleted=EARLIER), [], NOW, 30)

    assert (changes.status, changes.archived) == (NoteStatus.WAITING, False)


def test_a_note_that_is_neither_archived_nor_deleted_is_not_restorable():
    assert code(lambda: restore_note_changes(note(), [], NOW, 30)) == "note_not_restorable"


def test_a_note_does_not_come_back_into_a_deleted_topic():
    topics = [topic("TOPIC-001", deleted=EARLIER)]

    assert code(lambda: restore_note_changes(note(topic="TOPIC-001", deleted=EARLIER), topics, NOW, 30)) == (
        "topic_deleted")


def test_a_note_comes_back_into_a_live_topic():
    restore_note_changes(note(topic="TOPIC-001", deleted=EARLIER), [topic("TOPIC-001")], NOW, 30)


# ---------- trash and purge of a note ----------

def test_a_note_in_the_trash_cannot_be_deleted_again():
    check_delete_note(note())
    assert code(lambda: check_delete_note(note(deleted=EARLIER))) == "note_deleted"


def test_only_a_note_in_the_trash_can_be_purged():
    check_purge_note(note(deleted=EARLIER))
    assert code(lambda: check_purge_note(note())) == "note_not_deleted"


# ---------- topics: delete ----------

TREE = [topic("TOPIC-001"), topic("TOPIC-002", "TOPIC-001"), topic("TOPIC-003", "TOPIC-002"), topic("TOPIC-004")]
NOTES = [note(label="NOTE-001", topic="TOPIC-002"), note(label="NOTE-002", topic="TOPIC-004"),
         note(label="NOTE-003", topic="TOPIC-002", deleted=EARLIER), note(label="NOTE-004")]


def test_an_empty_topic_can_be_deleted_alone():
    plan = plan_topic_delete(TREE, NOTES, "TOPIC-003", cascade=False)

    assert (plan.topics, plan.notes) == (("TOPIC-003",), ())


def test_a_topic_with_content_needs_the_cascade():
    with pytest.raises(NoteLifecycleError) as caught:
        plan_topic_delete(TREE, NOTES, "TOPIC-001", cascade=False)

    assert caught.value.code == "topic_has_content"
    assert caught.value.details["items"] == "TOPIC-002, TOPIC-003, NOTE-001"


def test_the_cascade_takes_subtopics_and_their_live_notes_along():
    plan = plan_topic_delete(TREE, NOTES, "TOPIC-001", cascade=True)

    assert (plan.topics, plan.notes) == (("TOPIC-001", "TOPIC-002", "TOPIC-003"), ("NOTE-001",))


def test_a_topic_in_the_trash_cannot_be_deleted_again():
    tree = [topic("TOPIC-001", deleted=EARLIER)]

    assert code(lambda: plan_topic_delete(tree, [], "TOPIC-001", cascade=True)) == "topic_deleted"


# ---------- topics: restore and purge ----------

GONE = [topic("TOPIC-001", deleted=EARLIER), topic("TOPIC-002", "TOPIC-001", deleted=EARLIER),
        topic("TOPIC-003", "TOPIC-001", deleted=EARLIER - timedelta(days=1)), topic("TOPIC-004")]
GONE_NOTES = [note(label="NOTE-001", topic="TOPIC-001", deleted=EARLIER),
              note(label="NOTE-002", topic="TOPIC-001", deleted=EARLIER - timedelta(days=2))]


def test_restoring_a_topic_brings_back_what_was_deleted_with_it():
    plan = plan_topic_restore(GONE, GONE_NOTES, "TOPIC-001")

    assert (plan.topics, plan.notes) == (("TOPIC-001", "TOPIC-002"), ("NOTE-001",))


def test_a_topic_needs_its_parent_to_exist():
    assert code(lambda: plan_topic_restore(GONE, GONE_NOTES, "TOPIC-002")) == "topic_deleted"


def test_a_topic_below_a_live_parent_can_be_restored():
    tree = [topic("TOPIC-001"), topic("TOPIC-002", "TOPIC-001", deleted=EARLIER)]

    assert plan_topic_restore(tree, [], "TOPIC-002").topics == ("TOPIC-002",)


def test_a_live_topic_is_not_in_the_trash():
    assert code(lambda: plan_topic_restore(GONE, GONE_NOTES, "TOPIC-004")) == "topic_not_deleted"
    assert code(lambda: plan_topic_purge(GONE, GONE_NOTES, "TOPIC-004")) == "topic_not_deleted"


def test_purging_takes_the_deleted_subtree_and_its_deleted_notes():
    plan = plan_topic_purge(GONE, GONE_NOTES, "TOPIC-001")

    assert (plan.topics, plan.notes) == (("TOPIC-001", "TOPIC-002", "TOPIC-003"), ("NOTE-001", "NOTE-002"))


def test_an_unknown_topic_is_reported():
    from todo_viewer.domain.errors import TopicNotFoundError

    with pytest.raises(TopicNotFoundError):
        plan_topic_delete(TREE, NOTES, "TOPIC-009", cascade=True)

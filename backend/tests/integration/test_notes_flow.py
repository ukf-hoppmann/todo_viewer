"""Notes with triggers, review, archive, and trash across the real container: database project, no mocks."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from todo_viewer.application.container import Container
from todo_viewer.bootstrap import Settings, build_container
from todo_viewer.domain.errors import NoteLifecycleError
from todo_viewer.domain.item import Status
from todo_viewer.domain.notes import LinkTarget, NewTrigger, NoteReason, NoteStatus, TargetKind, TriggerKind
from todo_viewer.domain.source import Source

PROJECT = "demo"


@pytest.fixture
def container(tmp_path: Path) -> Container:
    settings = Settings(base_dir=tmp_path, config_dir=tmp_path / "config", frontend_dir=tmp_path / "dist",
                        browse_start=None)
    return build_container(settings)


@pytest.fixture
def source(container: Container) -> Source:
    return container.sources.add("", PROJECT, backend="database")


def new_story(container: Container, source: Source) -> str:
    fields = {"title": "Story", "area": "a", "goal": "g", "completion_criteria": "c"}
    return container.items.create(source, "Story", fields).item.id


def test_an_item_status_change_makes_the_note_due_and_snoozing_makes_it_wait_again(container: Container,
                                                                                    source: Source):
    story = new_story(container, source)
    note = container.notes.create(PROJECT, "check the result when the story is in progress").note
    container.notes.add_trigger(PROJECT, note.label, NewTrigger(
        TriggerKind.EVENT, target=LinkTarget(TargetKind.ITEM, PROJECT, story), target_status=Status.IN_PROGRESS))
    assert container.notes.due(PROJECT) == []

    item = container.items.get(source, story).item
    container.items.edit(source, story, item.version, {"status": Status.IN_PROGRESS}, None)

    due = container.notes.due(PROJECT)
    assert [(v.note.label, v.evaluation.reason) for v in due] == [(note.label, NoteReason.TRIGGER)]

    snoozed = container.notes.snooze(PROJECT, note.label, due[0].note.version)
    assert snoozed.evaluation.status is NoteStatus.SNOOZED
    assert container.notes.due(PROJECT) == []


def test_a_time_trigger_is_due_when_the_notes_are_read(container: Container, source: Source):
    note = container.notes.create(PROJECT, "remind me").note
    hour_ago = datetime.now(UTC) - timedelta(hours=1)

    container.notes.add_trigger(PROJECT, note.label, NewTrigger(TriggerKind.TIME, at=hour_ago))

    assert [v.note.label for v in container.notes.due(PROJECT)] == [note.label]


def test_a_new_note_waits_30_days_by_default(container: Container, source: Source):
    note = container.notes.create(PROJECT, "idea").note

    assert note.review_at is not None
    assert timedelta(days=29, hours=23) < note.review_at - datetime.now(UTC) <= timedelta(days=30)


def test_archive_and_trash_with_restore_and_purge(container: Container, source: Source):
    done = container.notes.create(PROJECT, "finished").note
    gone = container.notes.create(PROJECT, "deleted").note

    container.notes.finish(PROJECT, done.label, done.version, NoteStatus.DONE)
    container.notes.delete_note(PROJECT, gone.label)

    assert container.notes.overview(PROJECT) == []
    assert [v.note.label for v in container.notes.overview(PROJECT, archived=True)] == [done.label]
    assert [v.note.label for v in container.notes.trash(PROJECT).notes] == [gone.label]
    with pytest.raises(NoteLifecycleError):
        container.notes.purge_note(PROJECT, done.label)  # only what is in the trash can be purged

    container.notes.restore_note(PROJECT, done.label)
    container.notes.restore_note(PROJECT, gone.label)
    assert [v.note.label for v in container.notes.overview(PROJECT)] == [done.label, gone.label]

    container.notes.delete_note(PROJECT, gone.label)
    container.notes.purge_note(PROJECT, gone.label)
    assert container.notes.trash(PROJECT).notes == []

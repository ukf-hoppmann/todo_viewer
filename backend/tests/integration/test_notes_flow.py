"""Notes with triggers, review, archive, and trash across the real container: database project, no mocks."""
from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from todo_viewer.application.container import Container
from todo_viewer.bootstrap import Settings, build_container
from todo_viewer.domain.errors import LinkProjectUnknownError, LinkTargetNotFoundError, NoteLifecycleError
from todo_viewer.domain.item import Status
from todo_viewer.domain.notes import (
    LinkRole,
    LinkTarget,
    NewTrigger,
    NoteReason,
    NoteStatus,
    NoticeDecision,
    NoticeSide,
    TargetKind,
    TriggerKind,
)
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


def test_a_note_of_another_project_is_told_when_its_item_completes_is_retyped_and_is_deleted(container: Container,
                                                                                            source: Source):
    container.sources.add("other-path", "other", backend="database")
    story = new_story(container, source)
    task = new_story(container, source)
    note = container.notes.create("other", "keep an eye on the story").note
    container.notes.add_link("other", note.label, LinkTarget(TargetKind.ITEM, PROJECT, story), LinkRole.REFERENCE)
    container.notes.add_link("other", note.label, LinkTarget(TargetKind.ITEM, PROJECT, task), LinkRole.REFERENCE)

    def causes() -> list[str]:
        return [n.cause.value for n in container.notes.notices("other", note.label, NoticeSide.NOTE, False)]

    version = container.items.get(source, story).item.version
    container.items.edit(source, story, version, {"status": Status.COMPLETED}, "done")
    assert causes() == ["item_completed"]
    assert [(v.note.label, v.evaluation.reason) for v in container.notes.due("other")] == [
        (note.label, NoteReason.NOTICE)]

    retyped = container.retype.retype(source, story, container.items.get(source, story).item.version, "Task")
    assert causes() == ["item_completed", "item_retyped"]
    assert container.notes.links_of("other", note.label)[0].target.label == retyped.item.id

    container.trash.delete(source, task, container.items.get(source, task).item.version, cascade=False)
    assert causes() == ["item_completed", "item_retyped", "item_deleted"]

    # Nothing was decided, so nothing disappeared: the note stays due until somebody decides.
    assert len(container.notes.due("other")) == 1
    for notice in container.notes.notices("other", note.label, NoticeSide.NOTE, True):
        container.notes.decide(notice.id, NoticeDecision.KEEP)
    assert container.notes.due("other") == []
    assert len(container.notes.links_of("other", note.label)) == 2


def test_a_promoted_note_tells_the_item_it_referenced_but_not_the_item_it_became(container: Container,
                                                                                  source: Source):
    referenced = new_story(container, source)
    note = container.notes.create(PROJECT, "an idea", "Long text.").note
    container.notes.add_link(PROJECT, note.label, LinkTarget(TargetKind.ITEM, PROJECT, referenced))

    done = container.conversion.promote(PROJECT, note.label, note.version, "Task",
                                        {"area": "a", "goal": "g", "completion_criteria": "c"})

    created = done.item.item.id
    assert (done.note.note.status, done.note.note.archived) == (NoteStatus.PROMOTED, True)
    assert [n.cause.value for n in container.notes.notices(PROJECT, referenced, NoticeSide.ITEM)] == ["note_promoted"]
    assert container.notes.notices(PROJECT, created, NoticeSide.ITEM) == []


def test_closing_a_demoted_item_does_not_tell_the_note_it_became(container: Container, source: Source):
    task = container.items.create(source, "Task", {"title": "T", "area": "a", "goal": "g",
                                                   "completion_criteria": "c"}).item

    done = container.conversion.demote(source, task.id, task.version)

    label = done.note.note.label
    assert container.notes.notices(PROJECT, label, NoticeSide.NOTE, open_only=False) == []
    assert container.items.get(source, task.id).item.status == Status.REJECTED


def test_a_trigger_in_one_project_fires_when_an_item_of_another_project_completes(container: Container,
                                                                                  source: Source):
    other = container.sources.add("other-path", "other", backend="database")
    story = new_story(container, other)
    target = LinkTarget(TargetKind.ITEM, "other", story)
    note = container.notes.create(PROJECT, "continue when the other project is done").note
    container.notes.add_trigger(PROJECT, note.label, NewTrigger(TriggerKind.EVENT, target=target,
                                                                target_status=Status.COMPLETED))
    assert container.notes.due(PROJECT) == []

    container.items.edit(other, story, container.items.get(other, story).item.version,
                         {"status": Status.COMPLETED}, "done")

    assert [(v.note.label, v.evaluation.reason) for v in container.notes.due(PROJECT)] == [
        (note.label, NoteReason.TRIGGER)]
    # The way back: the item in the other project knows the note.
    assert [(v.link.project, v.view.note.label) for v in container.notes.notes_linking_to(target)] == [
        (PROJECT, note.label)]


def test_a_target_that_has_the_status_already_is_marked_already_met(container: Container, source: Source):
    other = container.sources.add("other-path", "other", backend="database")
    story = new_story(container, other)
    container.items.edit(other, story, container.items.get(other, story).item.version,
                         {"status": Status.COMPLETED}, "done")
    note = container.notes.create(PROJECT, "already there").note

    trigger = container.notes.add_trigger(PROJECT, note.label, NewTrigger(
        TriggerKind.EVENT, target=LinkTarget(TargetKind.ITEM, "other", story), target_status=Status.COMPLETED))

    assert trigger.already_met and trigger.fired_at is not None


def test_links_to_unknown_projects_and_missing_items_are_refused_with_their_own_errors(container: Container,
                                                                                       source: Source):
    container.sources.add("other-path", "other", backend="database")
    note = container.notes.create(PROJECT, "somewhere").note

    with pytest.raises(LinkProjectUnknownError):
        container.notes.add_link(PROJECT, note.label, LinkTarget(TargetKind.ITEM, "nowhere", "STORY-001"))
    with pytest.raises(LinkProjectUnknownError):
        container.notes.add_trigger(PROJECT, note.label, NewTrigger(
            TriggerKind.EVENT, target=LinkTarget(TargetKind.ITEM, "nowhere", "STORY-001"),
            target_status=Status.COMPLETED))
    with pytest.raises(LinkTargetNotFoundError):
        container.notes.add_link(PROJECT, note.label, LinkTarget(TargetKind.ITEM, "other", "STORY-099"))


def test_a_markdown_project_can_be_the_target_of_a_trigger(container: Container, source: Source, tmp_path: Path):
    folder = tmp_path / "md"
    folder.mkdir()
    shutil.copy(Path(__file__).parents[1] / "fixtures" / "backlog" / "TODO.md", folder / "TODO.md")
    markdown = container.sources.add(str(folder), "md", backend="markdown")
    note = container.notes.create(PROJECT, "wait for the markdown project").note
    container.notes.add_trigger(PROJECT, note.label, NewTrigger(
        TriggerKind.EVENT, target=LinkTarget(TargetKind.ITEM, "md", "STORY-001"), target_status=Status.IN_PROGRESS))

    container.items.edit(markdown, "STORY-001", container.items.get(markdown, "STORY-001").item.version,
                         {"status": Status.IN_PROGRESS}, None)

    assert [v.evaluation.reason for v in container.notes.due(PROJECT)] == [NoteReason.TRIGGER]

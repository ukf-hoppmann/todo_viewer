"""Links to items of projects that are gone or unreadable: reported as unreachable, one notice, never an error.

The notes port is the database adapter on a temporary SQLite file; the backlog is the in-memory fake, which can be
made to fail like an unreadable source. Sources can be removed and added back, like a project leaving and returning.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from tests.fakes import InMemoryBacklogRepository
from todo_viewer.application.services.notes import NoteService
from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.errors import InvalidSourceError
from todo_viewer.domain.item import Item, Status
from todo_viewer.domain.notes import (
    LinkRole,
    LinkTarget,
    NewTrigger,
    NoteReason,
    NoteStatus,
    NoticeCause,
    NoticeDecision,
    NoticeSide,
    TargetKind,
    TriggerKind,
)
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.notes import DatabaseNoteRepository

NOW = datetime(2027, 12, 11, 9, 0, tzinfo=UTC)
P, Q = "proj", "other"


class Sources:
    def __init__(self) -> None:
        self.registered = {P: Source(project=P, path="", backend="database", id="s1"),
                           Q: Source(project=Q, path="", backend="database", id="s2")}

    def all(self) -> list[Source]:
        return list(self.registered.values())


class Backlogs(InMemoryBacklogRepository):
    """The fake backlog that fails on request, for the projects named in `failing`."""

    def __init__(self, items: list[Item]) -> None:
        super().__init__(items)
        self.failing: dict[str, Exception] = {}

    def get(self, source: Source, item_id: str) -> Item:
        if source.project in self.failing:
            raise self.failing[source.project]
        return super().get(source, item_id)

    def load(self, source: Source) -> Backlog:
        if source.project in self.failing:
            raise self.failing[source.project]
        return super().load(source)


class World:
    def __init__(self, tmp_path: Path):
        self.sources = Sources()
        self.backlogs = Backlogs([Item(id="STORY-001", title="s", project=P, status=Status.OPEN)])
        self.repo = DatabaseNoteRepository(Database(f"sqlite:///{tmp_path / 'todo.db'}"), lambda: NOW)
        self.service = NoteService(self.repo, self.sources, self.backlogs, clock=lambda: NOW)  # type: ignore[arg-type]

    def note_linking_to(self, project: str, label: str = "STORY-001", role: LinkRole = LinkRole.REFERENCE) -> str:
        note = self.service.create(P, "waiting for another project").note
        self.service.add_link(P, note.label, LinkTarget(TargetKind.ITEM, project, label), role)
        return note.label

    def notices(self, label: str, open_only: bool = True) -> list[NoticeCause]:
        return [n.cause for n in self.service.notices(P, label, NoticeSide.NOTE, open_only)]

    def project_leaves(self, project: str) -> Source:
        return self.sources.registered.pop(project)


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def test_a_removed_project_makes_the_link_unreachable_with_one_notice_and_no_error(world: World):
    label = world.note_linking_to(Q)
    world.project_leaves(Q)

    infos = world.service.link_infos(P, label)

    assert [(i.link.target.project, i.reachability.reachable) for i in infos] == [(Q, False)]
    assert infos[0].reachability.reason == "project_not_registered"
    assert world.notices(label) == [NoticeCause.PROJECT_UNREACHABLE]

    world.service.link_infos(P, label)
    world.service.show(P, label)
    assert world.notices(label) == [NoticeCause.PROJECT_UNREACHABLE]  # still one


@pytest.mark.parametrize("failure", [OSError("disk gone"), InvalidSourceError("No TODO.md in this folder.",
                                                                              code="no_todo")])
def test_an_unreadable_source_is_handled_like_a_removed_project(world: World, failure: Exception):
    label = world.note_linking_to(Q)
    world.backlogs.failing[Q] = failure

    infos = world.service.link_infos(P, label)

    assert [i.reachability.reachable for i in infos] == [False]
    assert infos[0].reachability.reason == "source_unreadable"
    assert "disk gone" not in str(infos[0].reachability) and "TODO.md" not in str(infos[0].reachability)
    assert world.notices(label) == [NoticeCause.PROJECT_UNREACHABLE]


def test_a_returning_project_clears_the_mark_but_the_notice_stays_open(world: World):
    label = world.note_linking_to(Q)
    source = world.project_leaves(Q)
    world.service.link_infos(P, label)

    world.sources.registered[Q] = source

    assert [i.reachability.reachable for i in world.service.link_infos(P, label)] == [True]
    assert world.notices(label) == [NoticeCause.PROJECT_UNREACHABLE]


def test_an_item_missing_in_a_readable_project_is_not_unreachable(world: World):
    label = world.note_linking_to(Q)
    world.backlogs._items[world.sources.registered[Q].id] = []  # the item is gone from project Q, which is fine

    infos = world.service.link_infos(P, label)

    assert [i.reachability.reachable for i in infos] == [True]
    assert world.notices(label) == []


def test_a_link_inside_the_own_readable_project_is_never_unreachable(world: World):
    label = world.note_linking_to(P)

    assert [i.reachability.reachable for i in world.service.link_infos(P, label)] == [True]
    assert world.notices(label) == []


def test_topic_and_note_links_are_not_part_of_the_check(world: World):
    label = world.note_linking_to(P)
    other = world.service.create(P, "second").note
    world.service.add_link(P, label, LinkTarget(TargetKind.NOTE, P, other.label))
    world.backlogs.failing[P] = OSError("unreadable")

    infos = world.service.link_infos(P, label)

    assert [(i.link.target.kind, i.reachability.reachable) for i in infos] == [
        (TargetKind.ITEM, False), (TargetKind.NOTE, True)]


def test_reading_a_note_reports_its_unreachable_targets_and_the_notice_shows_on_it(world: World):
    note = world.service.create(P, "wait for the other project").note
    target = LinkTarget(TargetKind.ITEM, Q, "STORY-001")
    world.service.add_trigger(P, note.label, NewTrigger(TriggerKind.EVENT, target=target,
                                                        target_status=Status.COMPLETED))
    world.project_leaves(Q)

    view = world.service.show(P, note.label)

    assert not view.reachability[target].reachable
    assert [n.cause for n in view.open_notices] == [NoticeCause.PROJECT_UNREACHABLE]
    assert view.evaluation.reason is NoteReason.NOTICE


def test_the_due_list_picks_up_a_project_that_went_away(world: World):
    label = world.note_linking_to(Q)
    assert world.service.due(P) == []
    world.project_leaves(Q)

    due = world.service.due(P)

    assert [(v.note.label, v.evaluation.reason) for v in due] == [(label, NoteReason.NOTICE)]


def test_the_due_count_path_does_not_check_links(world: World):
    label = world.note_linking_to(Q)
    world.project_leaves(Q)

    assert world.service.due(P, check_links=False) == []
    assert world.notices(label) == []


def test_the_overview_does_not_check_anything(world: World):
    label = world.note_linking_to(Q)
    world.project_leaves(Q)

    views = world.service.overview(P)

    assert [v.note.label for v in views] == [label]
    assert world.notices(label) == []


def test_a_decided_notice_is_not_raised_again_while_the_project_stays_away(world: World):
    label = world.note_linking_to(Q)
    world.project_leaves(Q)
    world.service.link_infos(P, label)
    notice = world.service.notices(P, label, NoticeSide.NOTE)[0]
    world.service.decide(notice.id, NoticeDecision.KEEP)

    world.service.link_infos(P, label)
    world.service.show(P, label)

    assert world.notices(label) == []
    assert world.notices(label, open_only=False) == [NoticeCause.PROJECT_UNREACHABLE]


def test_a_finished_note_gets_no_notice(world: World):
    label = world.note_linking_to(Q)
    world.service.finish(P, label, world.service.show(P, label).note.version, NoteStatus.DONE)
    world.project_leaves(Q)

    world.service.show(P, label)

    assert world.notices(label, open_only=False) == []

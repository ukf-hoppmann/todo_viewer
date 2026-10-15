"""Which side of a mirrored project changed since its last sync, with the real storage adapters."""
from __future__ import annotations

import dataclasses
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from todo_viewer.application.services import BackupService, SyncService, SyncStatusService
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import SyncDirection, SyncState
from todo_viewer.infrastructure.database import (
    Database,
    DatabaseBacklogRepository,
    DatabaseDocumentStore,
    DatabaseRawBackup,
    DatabaseSourceRepository,
    DatabaseSyncStateStore,
)
from todo_viewer.infrastructure.markdown import (
    KeyedLocks,
    MarkdownRawBackup,
    build_markdown_documents,
    build_markdown_repository,
)
from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore, RoutingRawBackup

FIXTURE = Path(__file__).parents[1] / "fixtures" / "backlog"
NOW = datetime(2026, 9, 30, 15, 30, 12).astimezone()
TO_MD, FROM_MD = SyncDirection.TO_MD, SyncDirection.FROM_MD


class World:
    def __init__(self, tmp: Path):
        self.tmp = tmp
        locks = KeyedLocks()
        db = Database(f"sqlite:///{tmp / 'todo.db'}")
        self.backlogs = RoutingBacklogRepository({"markdown": build_markdown_repository(Path("/"), locks),
                                                  "database": DatabaseBacklogRepository(db)})
        self.documents = RoutingDocumentStore({"markdown": build_markdown_documents(Path("/"), locks),
                                               "database": DatabaseDocumentStore(db)})
        self.sources = DatabaseSourceRepository(db)
        self.sync = SyncService(self.backlogs, self.documents, states=DatabaseSyncStateStore(db))
        self.status = SyncStatusService(self.sync, self.sources, lambda: NOW)
        raw = RoutingRawBackup({"markdown": MarkdownRawBackup(LayoutFactory(SourcePathResolver(Path("/")))),
                                "database": DatabaseRawBackup()})
        self.backup = BackupService(raw, self.sync, tmp / "backups", lambda: NOW)

    def add(self, source: Source) -> Source:
        with self.sources.edit() as sources:
            sources.append(source)
        return source

    def stored(self, source: Source) -> Source:
        return next(s for s in self.sources.all() if s.id == source.id)

    def state(self, source: Source) -> SyncState:
        return self.status.status(self.stored(source)).state

    def synced(self, source: Source, direction: SyncDirection) -> None:
        stored = self.stored(source)
        token = self.sync.preview(stored, direction).token
        self.status.run(stored, token, (), direction, "en")

    def retitle(self, source: Source, label: str, title: str = "Edited") -> None:
        """Changes one item of the source's own side."""
        items = self.backlogs.load(source).items
        self.backlogs.write_backlog(source, [dataclasses.replace(i, title=title) if i.id == label else i
                                             for i in items], "en")


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def _database_project(world: World) -> Source:
    """The fixture backlog in the database with a markdown mirror folder that does not exist yet."""
    project = Source(project="Central", path="", backend="database", id="central", sync_path=str(world.tmp / "md"))
    items = build_markdown_repository(Path("/")).load(Source(project="P", path=str(FIXTURE))).items
    world.backlogs.write_backlog(project, items, "en")
    for path in sorted((FIXTURE / "items").glob("*/*.md")):
        world.documents.write(project, path.parent.name, path.name, path.read_text(encoding="utf-8"), None)
    return world.add(project)


def _markdown_side(project: Source) -> Source:
    return dataclasses.replace(project, backend="markdown", path=str(project.sync_path), sync_path=None)


def test_a_project_without_a_mirror_has_none(world: World):
    folder = world.tmp / "docs"
    shutil.copytree(FIXTURE, folder)
    plain = world.add(Source(project="Files", path=str(folder), id="plain"))
    bare = world.add(Source(project="Bare", path="", backend="database", id="bare"))

    assert world.state(plain) is SyncState.NONE and world.state(bare) is SyncState.NONE


def test_a_mirror_that_was_never_synced_is_unknown_while_the_sides_differ(world: World):
    project = _database_project(world)

    status = world.status.status(world.stored(project))

    assert (status.state, status.last_sync_at) == (SyncState.UNKNOWN, None)


def test_equal_sides_are_in_sync_even_without_a_recorded_sync(world: World):
    project = _database_project(world)
    token = world.sync.preview(project, TO_MD).token
    world.sync.run(project, token, (), TO_MD, "en")  # the plain service records nothing

    assert world.state(project) is SyncState.IN_SYNC
    assert world.status.status(world.stored(project)).last_sync_at is None


def test_a_sync_records_the_time_and_puts_the_project_in_sync(world: World):
    project = _database_project(world)

    world.synced(project, TO_MD)

    status = world.status.status(world.stored(project))
    assert (status.state, status.last_sync_at) == (SyncState.IN_SYNC, NOW.isoformat(timespec="seconds"))


def test_the_four_states_follow_the_side_that_changed(world: World):
    project = _database_project(world)
    world.synced(project, TO_MD)
    mirror = _markdown_side(project)

    world.retitle(mirror, "TASK-001")  # someone edits the markdown files
    assert world.state(project) is SyncState.MIRROR_CHANGED

    world.synced(project, FROM_MD)  # the edit is taken over
    assert world.state(project) is SyncState.IN_SYNC

    world.retitle(project, "TASK-002")  # the primary source moves on
    assert world.state(project) is SyncState.PRIMARY_CHANGED

    world.retitle(mirror, "TASK-001", "Edited again")
    assert world.state(project) is SyncState.BOTH_CHANGED


def test_a_changed_document_counts_like_a_changed_item(world: World):
    project = _database_project(world)
    world.synced(project, TO_MD)

    notes = world.tmp / "md" / "items" / "TASK-002" / "notes.md"
    notes.write_text(notes.read_text(encoding="utf-8") + "\nAdded by an AI.\n", encoding="utf-8")

    assert world.state(project) is SyncState.MIRROR_CHANGED


def test_what_a_sync_left_different_on_purpose_is_not_a_change(world: World):
    project = _database_project(world)
    world.synced(project, TO_MD)
    mirror = _markdown_side(project)
    world.backlogs.write_backlog(mirror, [*world.backlogs.load(mirror).items,
                                          Item(id="TASK-070", title="Only in the folder", project="P")], "en")
    world.synced(project, FROM_MD)  # pulls the new entry in ...
    world.backlogs.delete(project, [world.backlogs.get(project, "TASK-070")])
    world.synced(project, TO_MD)  # ... and this push keeps the extra entry in the folder

    assert world.backlogs.get(mirror, "TASK-070")
    assert world.state(project) is SyncState.IN_SYNC
    assert world.status.status(world.stored(project)).conflicts == 1  # the deletion still waits for a decision


def test_a_side_that_cannot_be_read_is_reported_not_raised(world: World):
    project = _database_project(world)
    world.synced(project, TO_MD)
    (world.tmp / "md" / "TODO.md").write_text("not a backlog at all\n", encoding="utf-8")

    assert world.state(project) is SyncState.UNREADABLE


def test_asking_for_the_status_changes_nothing(world: World):
    project = _database_project(world)
    world.synced(project, TO_MD)
    world.retitle(_markdown_side(project), "TASK-001")
    before = ({p.name: p.read_bytes() for p in (world.tmp / "md").rglob("*") if p.is_file()},
              {i.id: i.version for i in world.backlogs.load(project).items}, world.stored(project).baseline)

    for _ in range(3):
        assert world.state(project) is SyncState.MIRROR_CHANGED

    assert before == ({p.name: p.read_bytes() for p in (world.tmp / "md").rglob("*") if p.is_file()},
                      {i.id: i.version for i in world.backlogs.load(project).items}, world.stored(project).baseline)


def test_the_backup_before_a_switch_records_no_sync(world: World):
    project = _database_project(world)

    world.backup.create(world.stored(project))

    assert world.stored(project).baseline is None


def test_a_project_whose_mirror_is_switched_off_has_none_although_its_folder_is_kept(world: World):
    project = _database_project(world)
    world.synced(project, TO_MD)
    with world.sources.edit() as sources:
        sources[0] = dataclasses.replace(sources[0], mirror_disabled=True)

    assert world.state(project) is SyncState.NONE
    assert world.stored(project).markdown_path == str(world.tmp / "md")


def test_the_status_counts_the_conflicts_and_nothing_else_does(world: World):
    project = _database_project(world)
    world.synced(project, TO_MD)
    assert world.status.status(world.stored(project)).conflicts == 0

    world.retitle(project, "TASK-001", "In the database")
    world.retitle(_markdown_side(project), "TASK-001", "In the file")
    world.retitle(_markdown_side(project), "TASK-002")  # one side only: no conflict

    assert world.status.status(world.stored(project)).conflicts == 1
    assert world.state(project) is SyncState.BOTH_CHANGED


def test_a_project_without_a_mirror_has_no_conflicts(world: World):
    bare = world.add(Source(project="Bare", path="", backend="database", id="bare"))

    assert world.status.status(world.stored(bare)).conflicts == 0

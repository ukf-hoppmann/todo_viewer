"""The backup that precedes a switch of the primary source, with the real storage adapters."""
from __future__ import annotations

import dataclasses
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from todo_viewer.application.services import BackupService, SyncService
from todo_viewer.domain.errors import BackupFailedError
from todo_viewer.domain.item import Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.database import Database, DatabaseBacklogRepository, DatabaseDocumentStore
from todo_viewer.infrastructure.database.backup import DatabaseRawBackup
from todo_viewer.infrastructure.markdown import (
    KeyedLocks,
    MarkdownRawBackup,
    build_markdown_documents,
    build_markdown_repository,
)
from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore, RoutingRawBackup

FIXTURE = Path(__file__).parents[1] / "fixtures" / "backlog"
NOW = datetime(2026, 9, 30, 15, 30, 12)


class World:
    def __init__(self, tmp: Path):
        self.tmp = tmp
        locks = KeyedLocks()
        db = Database(f"sqlite:///{tmp / 'todo.db'}")
        self.backlogs = RoutingBacklogRepository({"markdown": build_markdown_repository(Path("/"), locks),
                                                  "database": DatabaseBacklogRepository(db)})
        self.documents = RoutingDocumentStore({"markdown": build_markdown_documents(Path("/"), locks),
                                               "database": DatabaseDocumentStore(db)})
        raw = RoutingRawBackup({"markdown": MarkdownRawBackup(LayoutFactory(SourcePathResolver(Path("/")))),
                                "database": DatabaseRawBackup()})
        self.backup = BackupService(raw, SyncService(self.backlogs, self.documents), tmp / "backups", lambda: NOW)

    def markdown_project(self) -> Source:
        folder = self.tmp / "docs"
        shutil.copytree(FIXTURE, folder)
        return Source(project="Files", path=str(folder), id="aaaaaaaa-1111-4000-8000-000000000001")

    def database_project(self) -> Source:
        """The fixture backlog in the database, with one item in the trash."""
        project = Source(project="Central", path="", backend="database", id="bbbbbbbb-2222-4000-8000-000000000002")
        items = build_markdown_repository(Path("/")).load(Source(project="P", path=str(FIXTURE))).items
        self.backlogs.write_backlog(project, [dataclasses.replace(i, deleted="2026-09-28") if i.id == "TASK-003" else i
                                              for i in items], "en")
        for path in sorted((FIXTURE / "items").glob("*/*.md")):
            self.documents.write(project, path.parent.name, path.name, path.read_text(encoding="utf-8"), None)
        return project

    def versions(self, source: Source) -> dict[str, str]:
        return {i.id: i.version for i in self.backlogs.load(source).items}


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def _files(folder: Path) -> dict[str, bytes]:
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_a_markdown_project_is_backed_up_byte_for_byte_and_the_backup_reads_as_the_same_backlog(world: World):
    project = world.markdown_project()
    (Path(project.path) / "TODO.md").write_bytes((FIXTURE / "TODO.md").read_bytes() + b"\n\n  hand written   \n")

    location = Path(world.backup.create(project))

    assert location == world.tmp / "backups" / "Files_aaaaaaaa" / "20260930-153012"
    assert _files(location) == _files(Path(project.path))
    assert world.versions(dataclasses.replace(project, path=str(location))) == world.versions(project)


def test_a_database_project_is_exported_and_the_backup_restores_the_old_state(world: World):
    project = world.database_project()

    location = Path(world.backup.create(project))

    restored = Source(project="Restored", path=str(location))
    assert world.versions(restored) == world.versions(project)
    assert world.backlogs.get(restored, "TASK-003").deleted == "2026-09-28"
    assert world.backlogs.get(restored, "TASK-000").location is Location.ARCHIVE
    assert world.documents.read(restored, "TASK-002", "notes.md") == world.documents.read(project, "TASK-002",
                                                                                          "notes.md")


def test_a_second_backup_in_the_same_second_gets_its_own_folder(world: World):
    project = world.markdown_project()

    first, second = world.backup.create(project), world.backup.create(project)

    assert first != second and Path(first).is_dir() and Path(second).is_dir()


def test_a_backup_that_cannot_be_written_fails_with_the_reason_and_leaves_nothing_behind(world: World):
    project = world.markdown_project()
    (world.tmp / "backups").write_text("a file, not a folder", encoding="utf-8")

    with pytest.raises(BackupFailedError) as error:
        world.backup.create(project)

    assert error.value.code == "backup_failed" and error.value.details["reason"]
    assert (world.tmp / "backups").read_text(encoding="utf-8") == "a file, not a folder"


def test_a_failed_export_removes_what_it_began(world: World):
    project = world.database_project()
    original = world.backlogs.write_backlog

    def broken(source: Source, items: object, language: str) -> None:
        original(source, items, language)  # type: ignore[arg-type]
        raise OSError("disk full")

    world.backlogs.write_backlog = broken  # type: ignore[method-assign]

    with pytest.raises(BackupFailedError, match="disk full"):
        world.backup.create(project)

    assert not any((world.tmp / "backups").rglob("TODO.md"))

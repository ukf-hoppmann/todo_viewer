"""The sync service with the real storage adapters: a SQLite database and markdown folders on disk."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path

import pytest

from todo_viewer.application.services import SyncService
from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import SyncPathMissingError, SyncSameBackendError, SyncSourceInvalidError, SyncStaleError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import SyncDirection
from todo_viewer.infrastructure.database.documents import DatabaseDocumentStore
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.repository import DatabaseBacklogRepository
from todo_viewer.infrastructure.markdown import KeyedLocks, build_markdown_documents, build_markdown_repository
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore

FIXTURE = Path(__file__).parents[1] / "fixtures" / "backlog"
TO_MD, FROM_MD = SyncDirection.TO_MD, SyncDirection.FROM_MD


@dataclass
class Setup:
    service: SyncService
    backlogs: RoutingBacklogRepository
    documents: RoutingDocumentStore
    tmp: Path
    project: Source  # database project with the fixture backlog, synced with tmp/md

    def database_project(self, name: str, sync_folder: Path) -> Source:
        source = Source(project="P", path="", backend="database", id=name, sync_path=str(sync_folder))
        self.backlogs.initialize(source, "en")
        return source

    def versions(self, source: Source) -> dict[str, str]:
        return {i.id: i.version for i in self.backlogs.load(source).items}

    def files(self, folder: Path) -> dict[str, str]:
        return {str(p.relative_to(folder)): p.read_text(encoding="utf-8")
                for p in sorted(folder.rglob("*")) if p.is_file()}


@pytest.fixture
def setup(tmp_path: Path) -> Setup:
    locks = KeyedLocks()
    db = Database(f"sqlite:///{tmp_path / 'todo.db'}")
    backlogs = RoutingBacklogRepository({"markdown": build_markdown_repository(Path("/"), locks),
                                         "database": DatabaseBacklogRepository(db)})
    documents = RoutingDocumentStore({"markdown": build_markdown_documents(Path("/"), locks),
                                      "database": DatabaseDocumentStore(db)})
    fixture = build_markdown_repository(Path("/")).load(Source(project="P", path=str(FIXTURE))).items
    project = Source(project="P", path="", backend="database", id="central", sync_path=str(tmp_path / "md"))
    backlogs.write_backlog(project, fixture, "en")
    for path in sorted((FIXTURE / "items").glob("*/*.md")):
        documents.write(project, path.parent.name, path.name, path.read_text(encoding="utf-8"), None)
    for name in ("spec.md", "extra.md"):  # listed by TASK-002 in the fixture, but not part of its files
        documents.write(project, "TASK-002", name, f"# {name}\n", None)
    return Setup(SyncService(backlogs, documents), backlogs, documents, tmp_path, project)


def test_a_preview_changes_nothing(setup: Setup):
    before = setup.versions(setup.project)

    preview = setup.service.preview(setup.project, TO_MD)

    assert len(preview.created) == len(before) and preview.changed == () and preview.missing == ()
    assert not (setup.tmp / "md").exists()
    assert setup.versions(setup.project) == before


def test_export_import_export_gives_identical_files_and_items(setup: Setup):
    md1, md2 = setup.tmp / "md", setup.tmp / "md2"
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")

    copy = setup.database_project("copy", md1)
    setup.service.run(copy, FROM_MD, setup.service.preview(copy, FROM_MD).token, False, "en")
    assert setup.versions(copy) == setup.versions(setup.project)
    again = dataclasses.replace(copy, sync_path=str(md2))
    setup.service.run(again, TO_MD, setup.service.preview(again, TO_MD).token, False, "en")

    assert setup.files(md2) == setup.files(md1)
    assert "items/TASK-002/extra.md" in setup.files(md1)  # topic specs travel with their item


def test_a_second_sync_finds_nothing_to_do(setup: Setup):
    for direction in (TO_MD, FROM_MD):
        setup.service.run(setup.project, direction, setup.service.preview(setup.project, direction).token, False, "en")

    preview = setup.service.preview(setup.project, FROM_MD)

    assert (preview.created, preview.changed, preview.missing) == ((), (), ())
    assert (preview.created_documents, preview.changed_documents, preview.missing_documents) == ((), (), ())


def test_the_trash_stays_the_trash_and_the_archive_stays_the_archive(setup: Setup):
    trashed = dataclasses.replace(setup.backlogs.get(setup.project, "TASK-003"), deleted="2026-09-28")
    items = [trashed if i.id == "TASK-003" else i for i in setup.backlogs.load(setup.project).items]
    setup.backlogs.write_backlog(setup.project, items, "en")
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")

    copy = setup.database_project("copy", setup.tmp / "md")
    setup.service.run(copy, FROM_MD, setup.service.preview(copy, FROM_MD).token, False, "en")

    assert setup.backlogs.get(copy, "TASK-003").deleted == "2026-09-28"
    assert setup.backlogs.get(copy, "TASK-000").location is Location.ARCHIVE


def test_changes_on_the_source_side_overwrite_the_target(setup: Setup):
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")
    item = setup.backlogs.get(setup.project, "TASK-001")
    setup.backlogs.write_backlog(setup.project, [dataclasses.replace(i, title="Edited") if i.id == item.id else i
                                                 for i in setup.backlogs.load(setup.project).items], "en")
    old = setup.documents.read(setup.project, "TASK-002", "notes.md")
    setup.documents.write(setup.project, "TASK-002", "notes.md", "# new\n", content_version(old))

    preview = setup.service.preview(setup.project, TO_MD)
    setup.service.run(setup.project, TO_MD, preview.token, False, "en")

    assert [e.label for e in preview.changed] == ["TASK-001"]
    assert [(e.label, e.name) for e in preview.changed_documents] == [("TASK-002", "notes.md")]
    assert "**Edited**" in (setup.tmp / "md" / "TODO.md").read_text(encoding="utf-8")
    assert (setup.tmp / "md" / "items" / "TASK-002" / "notes.md").read_text(encoding="utf-8") == "# new\n"


def _stray_copy(setup: Setup) -> Source:
    """A database project that holds an item and a document the folder does not have."""
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")
    copy = setup.database_project("copy", setup.tmp / "md")
    setup.service.run(copy, FROM_MD, setup.service.preview(copy, FROM_MD).token, False, "en")
    setup.backlogs.create(copy, Item(id="TASK-070", title="Only here", project="P", notes=["TASK-070_notes.md"]))
    setup.documents.write(copy, "TASK-070", "TASK-070_notes.md", "# n\n", None)
    setup.documents.write(copy, "TASK-001", "TASK-001_spec.md", "# stray\n", None)
    return copy


def test_missing_entries_are_reported_and_stay_without_confirmation(setup: Setup):
    copy = _stray_copy(setup)

    preview = setup.service.preview(copy, FROM_MD)
    result = setup.service.run(copy, FROM_MD, preview.token, delete_missing=False, language="en")

    assert [e.label for e in preview.missing] == ["TASK-070"]
    assert [e.label for e in result.kept] == ["TASK-070"] and result.deleted == ()
    assert setup.backlogs.get(copy, "TASK-070").title == "Only here"
    assert setup.documents.read(copy, "TASK-070", "TASK-070_notes.md") == "# n\n"


def test_missing_entries_are_deleted_only_when_asked_for(setup: Setup):
    copy = _stray_copy(setup)

    preview = setup.service.preview(copy, FROM_MD)
    result = setup.service.run(copy, FROM_MD, preview.token, delete_missing=True, language="en")

    assert {e.label for e in result.deleted} == {"TASK-070"}
    assert setup.versions(copy) == setup.versions(setup.project)
    assert setup.documents.read(setup.project, "TASK-002", "notes.md")  # the other side is untouched


def _without_extra_spec(setup: Setup) -> Path:
    """Exported once; then the database item stops listing (and has) one of its documents. Returns its file."""
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")
    setup.documents.delete_document(setup.project, "TASK-002", "extra.md")
    setup.backlogs.write_backlog(setup.project, [dataclasses.replace(i, spec=["spec.md"]) if i.id == "TASK-002" else i
                                                 for i in setup.backlogs.load(setup.project).items], "en")
    return setup.tmp / "md" / "items" / "TASK-002" / "extra.md"


def test_a_document_missing_on_the_source_stays_without_confirmation(setup: Setup):
    stray = _without_extra_spec(setup)

    preview = setup.service.preview(setup.project, TO_MD)
    result = setup.service.run(setup.project, TO_MD, preview.token, False, "en")

    assert [e.name for e in preview.missing_documents] == ["extra.md"]
    assert [e.name for e in result.kept] == ["extra.md"] and stray.is_file()


def test_a_document_missing_on_the_source_is_deleted_when_asked_for(setup: Setup):
    stray = _without_extra_spec(setup)

    result = setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, True, "en")

    assert [e.name for e in result.deleted] == ["extra.md"] and not stray.exists()
    assert (stray.parent / "spec.md").is_file()


def test_an_unreadable_folder_stops_before_anything_is_changed(setup: Setup):
    md = setup.tmp / "md"
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")
    (md / "TODO.md").write_text("Not a backlog.\n", encoding="utf-8")
    before = setup.versions(setup.project)

    with pytest.raises(SyncSourceInvalidError) as error:
        setup.service.preview(setup.project, FROM_MD)
    with pytest.raises(SyncSourceInvalidError):
        setup.service.run(setup.project, FROM_MD, "x", True, "en")
    with pytest.raises(SyncSourceInvalidError):
        setup.service.run(setup.project, TO_MD, "x", True, "en")  # the target cannot be read either

    assert error.value.code == "sync_source_invalid"
    assert setup.versions(setup.project) == before
    assert (md / "TODO.md").read_text(encoding="utf-8") == "Not a backlog.\n"


def test_a_change_after_the_preview_makes_it_stale(setup: Setup):
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")
    preview = setup.service.preview(setup.project, TO_MD)
    md_before = setup.files(setup.tmp / "md")
    setup.backlogs.write_backlog(setup.project, [dataclasses.replace(i, title="Late") for i in
                                                 setup.backlogs.load(setup.project).items], "en")

    with pytest.raises(SyncStaleError):
        setup.service.run(setup.project, TO_MD, preview.token, False, "en")
    with pytest.raises(SyncStaleError):
        setup.service.run(setup.project, TO_MD, None, False, "en")

    assert setup.files(setup.tmp / "md") == md_before


def test_the_target_folder_is_created_in_the_given_language(setup: Setup):
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "de")

    assert (setup.tmp / "md" / "archive.md").read_text(encoding="utf-8").startswith("# Projekt-Backlog-Archiv")


def test_from_md_needs_an_existing_backlog(setup: Setup):
    with pytest.raises(SyncSourceInvalidError) as error:
        setup.service.preview(setup.project, FROM_MD)

    assert error.value.details["reason"] == "not_found"


def test_projects_without_a_sync_folder_or_in_markdown_are_refused(setup: Setup):
    with pytest.raises(SyncPathMissingError):
        setup.service.preview(dataclasses.replace(setup.project, sync_path=None), TO_MD)
    with pytest.raises(SyncSameBackendError):
        setup.service.preview(Source(project="P", path=str(FIXTURE), id="m"), TO_MD)


def test_a_markdown_project_is_read_into_the_database_under_its_id(setup: Setup):
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")
    moving = Source(project="P", path=str(setup.tmp / "md"), id="moving")

    preview = setup.service.preview(moving, FROM_MD)
    setup.service.run(moving, FROM_MD, preview.token, False, "en")

    assert len(preview.created) == len(setup.versions(setup.project))
    database = dataclasses.replace(moving, backend="database", path="")
    assert setup.versions(database) == setup.versions(setup.project)
    assert setup.documents.read(database, "TASK-002", "notes.md").startswith("# Notes for TASK-002")


def test_a_project_is_in_sync_when_nothing_would_change(setup: Setup):
    assert not setup.service.in_sync(setup.project, TO_MD)  # the folder does not exist yet
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")

    assert setup.service.in_sync(setup.project, TO_MD)
    assert setup.service.in_sync(setup.project, FROM_MD)


def test_a_difference_in_either_direction_or_in_a_document_is_not_in_sync(setup: Setup):
    setup.service.run(setup.project, TO_MD, setup.service.preview(setup.project, TO_MD).token, False, "en")
    (setup.tmp / "md" / "items" / "TASK-002" / "notes.md").write_text("# other\n", encoding="utf-8")
    assert not setup.service.in_sync(setup.project, TO_MD)

    setup.service.run(setup.project, FROM_MD, setup.service.preview(setup.project, FROM_MD).token, False, "en")
    setup.backlogs.create(setup.project, Item(id="TASK-071", title="Only in the database", project="P"))

    assert not setup.service.in_sync(setup.project, TO_MD)  # would be created in the folder
    assert not setup.service.in_sync(setup.project, FROM_MD)  # would be missing in the folder


def test_in_sync_of_a_broken_folder_is_an_error_not_a_no(setup: Setup):
    with pytest.raises(SyncSourceInvalidError):
        setup.service.in_sync(setup.project, FROM_MD)

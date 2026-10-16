"""The sync service with the real storage adapters: a SQLite database and markdown folders on disk."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path

import pytest

from todo_viewer.application.services import SyncService
from todo_viewer.application.services.sync import SyncResult
from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import (
    DatabaseBackupFailedError,
    DocumentNotFoundError,
    SyncPathMissingError,
    SyncSameBackendError,
    SyncSourceInvalidError,
    SyncStaleError,
)
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import Choice, EntryKey, EntryState, Resolution, SyncDirection
from todo_viewer.infrastructure.database.documents import DatabaseDocumentStore
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.repository import DatabaseBacklogRepository
from todo_viewer.infrastructure.database.sync_state import DatabaseSyncStateStore
from todo_viewer.infrastructure.markdown import KeyedLocks, build_markdown_documents, build_markdown_repository
from todo_viewer.infrastructure.routing import RoutingBacklogRepository, RoutingDocumentStore

FIXTURE = Path(__file__).parents[1] / "fixtures" / "backlog"
TO_MD, FROM_MD = SyncDirection.TO_MD, SyncDirection.FROM_MD
DB, MD, LATER = Choice.DATABASE, Choice.MARKDOWN, Choice.DEFER


def sync(setup: Setup, source: Source | None = None, *resolutions: Resolution, direction: SyncDirection | None = None,
         service: SyncService | None = None) -> SyncResult:
    """Preview, then confirm that preview."""
    service, source = service or setup.service, source or setup.project
    return service.run(source, service.preview(source, direction).token, resolutions, direction, "en")


def decide(kind: str, label: str, choice: Choice, name: str | None = None) -> Resolution:
    return Resolution(kind, label, name, choice)


@dataclass
class Setup:
    service: SyncService
    backlogs: RoutingBacklogRepository
    documents: RoutingDocumentStore
    tmp: Path
    project: Source  # database project with the fixture backlog, synced with tmp/md
    states: DatabaseSyncStateStore

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
    states = DatabaseSyncStateStore(db)
    return Setup(SyncService(backlogs, documents, states=states), backlogs, documents, tmp_path, project, states)


def edit_item(setup: Setup, source: Source, label: str, **fields: object) -> None:
    items = setup.backlogs.load(source).items
    setup.backlogs.write_backlog(source, [dataclasses.replace(i, **fields) if i.id == label else i for i in items],
                                 "en")


def write_doc(setup: Setup, source: Source, label: str, name: str, text: str) -> None:
    try:
        current: str | None = setup.documents.read(source, label, name)
    except Exception:
        current = None
    setup.documents.write(source, label, name, text, None if current is None else content_version(current))


@pytest.fixture
def md_project(setup: Setup) -> Source:
    """The folder side of the project, as an editor outside the viewer (or a cloud session) sees it."""
    return dataclasses.replace(setup.project, backend="markdown", path=str(setup.tmp / "md"), sync_path=None)


@pytest.fixture
def synced(setup: Setup) -> Setup:
    """The project exported once, so database and folder agree and every entry has a stored state."""
    sync(setup)
    return setup


def test_a_preview_changes_nothing(setup: Setup):
    before = setup.versions(setup.project)

    preview = setup.service.preview(setup.project)

    assert len(preview.created) == len(before) and preview.changed == () and preview.conflicts == ()
    assert {e.origin.value for e in preview.created if e.origin} == {"database"}
    assert not (setup.tmp / "md").exists()
    assert setup.versions(setup.project) == before
    assert setup.states.load(setup.project.id, str(setup.tmp / "md")) == {}


def test_export_import_export_gives_identical_files_and_items(setup: Setup):
    md1, md2 = setup.tmp / "md", setup.tmp / "md2"
    sync(setup)

    copy = setup.database_project("copy", md1)
    sync(setup, copy)
    assert setup.versions(copy) == setup.versions(setup.project)
    again = dataclasses.replace(copy, sync_path=str(md2))
    sync(setup, again)

    assert setup.files(md2) == setup.files(md1)
    assert "items/TASK-002/extra.md" in setup.files(md1)  # topic specs travel with their item


def test_a_second_sync_finds_nothing_to_do(synced: Setup):
    preview = synced.service.preview(synced.project)

    assert (preview.created, preview.changed, preview.conflicts) == ((), (), ())
    assert (preview.created_documents, preview.changed_documents) == ((), ())
    assert synced.service.in_sync(synced.project)


def test_the_trash_stays_the_trash_and_the_archive_stays_the_archive(setup: Setup):
    edit_item(setup, setup.project, "TASK-003", deleted="2026-09-28")
    sync(setup)

    copy = setup.database_project("copy", setup.tmp / "md")
    sync(setup, copy)

    assert setup.backlogs.get(copy, "TASK-003").deleted == "2026-09-28"
    assert setup.backlogs.get(copy, "TASK-000").location is Location.ARCHIVE


def test_a_change_in_the_database_is_carried_to_the_folder_and_one_in_the_folder_to_the_database(
        synced: Setup, md_project: Source):
    edit_item(synced, synced.project, "TASK-001", title="Edited in the database")
    write_doc(synced, md_project, "TASK-002", "notes.md", "# edited in the folder\n")

    preview = synced.service.preview(synced.project)
    result = sync(synced)

    assert [(e.label, e.origin.value) for e in preview.changed if e.origin] == [("TASK-001", "database")]
    assert [(e.name, e.origin.value) for e in preview.changed_documents if e.origin] == [("notes.md", "markdown")]
    assert "**Edited in the database**" in (synced.tmp / "md" / "TODO.md").read_text(encoding="utf-8")
    assert synced.documents.read(synced.project, "TASK-002", "notes.md") == "# edited in the folder\n"
    assert {e.label for e in result.resolved} == {"TASK-001", "TASK-002"} and result.deferred == ()
    assert synced.service.in_sync(synced.project)


def test_scenario_the_folder_changes_one_item_and_the_database_another_and_both_survive(
        synced: Setup, md_project: Source):
    edit_item(synced, md_project, "TASK-001", title="A in the file")
    edit_item(synced, synced.project, "TASK-002", title="B in the database")

    result = sync(synced)

    assert synced.backlogs.get(synced.project, "TASK-001").title == "A in the file"
    assert synced.backlogs.get(md_project, "TASK-002").title == "B in the database"
    assert result.deferred == () and synced.service.in_sync(synced.project)


def test_scenario_both_sides_create_the_same_id_and_nothing_is_overwritten(synced: Setup, md_project: Source):
    synced.backlogs.create(synced.project, Item(id="TASK-070", title="From the database", project="P"))
    synced.backlogs.create(md_project, Item(id="TASK-070", title="From the file", project="P"))

    preview = synced.service.preview(synced.project)
    result = sync(synced)

    [conflict] = preview.conflicts
    assert (conflict.entry.label, conflict.reason.value) == ("TASK-070", "both_new")
    assert synced.backlogs.get(synced.project, "TASK-070").title == "From the database"
    assert synced.backlogs.get(md_project, "TASK-070").title == "From the file"
    assert [e.label for e in result.deferred] == ["TASK-070"] and result.resolved == ()
    assert [c.entry.label for c in synced.service.preview(synced.project).conflicts] == ["TASK-070"]  # reported again


@pytest.mark.parametrize("choice, winner", [(DB, "In the database"), (MD, "In the file")])
def test_a_conflict_is_decided_for_the_side_chosen(synced: Setup, md_project: Source, choice: Choice, winner: str):
    edit_item(synced, synced.project, "TASK-001", title="In the database")
    edit_item(synced, md_project, "TASK-001", title="In the file")
    edit_item(synced, synced.project, "TASK-002", title="Free change")  # carried without any decision

    result = sync(synced, synced.project, decide("item", "TASK-001", choice))

    assert synced.backlogs.get(synced.project, "TASK-001").title == winner
    assert synced.backlogs.get(md_project, "TASK-001").title == winner
    assert synced.backlogs.get(md_project, "TASK-002").title == "Free change"
    assert {e.label for e in result.resolved} == {"TASK-001", "TASK-002"} and result.deferred == ()
    assert synced.service.in_sync(synced.project)


def test_a_conflict_without_a_decision_or_with_defer_is_left_alone_and_comes_back(synced: Setup, md_project: Source):
    edit_item(synced, synced.project, "TASK-001", title="In the database")
    edit_item(synced, md_project, "TASK-001", title="In the file")
    edit_item(synced, synced.project, "TASK-002", title="Free change")

    for resolutions in ((), (decide("item", "TASK-001", LATER),)):
        result = sync(synced, synced.project, *resolutions)

        assert [e.label for e in result.deferred] == ["TASK-001"]
        assert synced.backlogs.get(synced.project, "TASK-001").title == "In the database"
        assert synced.backlogs.get(md_project, "TASK-001").title == "In the file"
        assert [c.entry.label for c in synced.service.preview(synced.project).conflicts] == ["TASK-001"]
    assert synced.backlogs.get(md_project, "TASK-002").title == "Free change"


def test_a_conflict_that_was_made_equal_by_hand_is_none_any_more(synced: Setup, md_project: Source):
    edit_item(synced, synced.project, "TASK-001", title="Same")
    edit_item(synced, md_project, "TASK-001", title="Different")
    assert len(synced.service.preview(synced.project).conflicts) == 1

    edit_item(synced, md_project, "TASK-001", title="Same")

    assert synced.service.preview(synced.project).conflicts == ()
    sync(synced)
    edit_item(synced, synced.project, "TASK-001", title="Later")  # the state was refreshed: one side only
    assert synced.service.preview(synced.project).conflicts == ()


def test_a_document_conflict_is_decided_on_its_own(synced: Setup, md_project: Source):
    write_doc(synced, synced.project, "TASK-002", "notes.md", "# database\n")
    write_doc(synced, md_project, "TASK-002", "notes.md", "# file\n")

    preview = synced.service.preview(synced.project)
    sync(synced, synced.project, decide("item", "TASK-002", DB))  # names the item, not the document: no effect
    assert synced.documents.read(md_project, "TASK-002", "notes.md") == "# file\n"
    sync(synced, synced.project, decide("document", "TASK-002", MD, "notes.md"))

    assert [(c.entry.kind, c.entry.name) for c in preview.conflicts] == [("document", "notes.md")]
    assert (preview.conflicts[0].database.text, preview.conflicts[0].markdown.text) == (  # type: ignore[union-attr]
        "# database\n", "# file\n")
    assert synced.documents.read(synced.project, "TASK-002", "notes.md") == "# file\n"


@pytest.mark.parametrize("gone_from", ["database", "markdown"])
def test_a_deleted_item_is_a_conflict_that_nothing_deletes_or_revives_without_a_decision(
        synced: Setup, md_project: Source, gone_from: str):
    gone, kept = (synced.project, md_project) if gone_from == "database" else (md_project, synced.project)
    synced.backlogs.write_backlog(gone, [i for i in synced.backlogs.load(gone).items if i.id != "TASK-002"], "en")

    preview = synced.service.preview(synced.project)
    result = sync(synced)

    assert [(c.entry.label, c.reason.value) for c in preview.conflicts] == [("TASK-002", f"{gone_from}_deleted")]
    assert synced.backlogs.get(kept, "TASK-002")
    assert [e.label for e in result.kept] == ["TASK-002"] and result.deleted == ()
    assert "TASK-002" not in {i.id for i in synced.backlogs.load(gone).items}


@pytest.mark.parametrize("gone_from", ["database", "markdown"])
def test_the_decision_for_a_deleted_item_deletes_it_with_its_documents_or_restores_it(
        synced: Setup, md_project: Source, gone_from: str):
    gone, kept = (synced.project, md_project) if gone_from == "database" else (md_project, synced.project)
    synced.backlogs.write_backlog(gone, [i for i in synced.backlogs.load(gone).items if i.id != "TASK-002"], "en")
    synced.documents.delete_documents(gone, "TASK-002")
    restore = gone_from  # the state of the side where it is gone holds: delete it on the other side
    revive = "markdown" if gone_from == "database" else "database"

    sync(synced, synced.project, decide("item", "TASK-002", Choice(revive)))  # the surviving side holds: restore
    assert synced.backlogs.get(gone, "TASK-002")
    assert synced.documents.read(gone, "TASK-002", "notes.md").startswith("# Notes for TASK-002")

    synced.backlogs.write_backlog(gone, [i for i in synced.backlogs.load(gone).items if i.id != "TASK-002"], "en")
    synced.documents.delete_documents(gone, "TASK-002")
    result = sync(synced, synced.project, decide("item", "TASK-002", Choice(restore)))

    assert [e.label for e in result.deleted] == ["TASK-002"]
    assert "TASK-002" not in {i.id for i in synced.backlogs.load(kept).items}
    with pytest.raises(DocumentNotFoundError):
        synced.documents.read(kept, "TASK-002", "notes.md")
    assert synced.service.in_sync(synced.project)


@pytest.mark.parametrize("choice", [DB, MD])
def test_a_deleted_document_is_a_conflict_too(synced: Setup, md_project: Source, choice: Choice):
    (synced.tmp / "md" / "items" / "TASK-002" / "extra.md").unlink()

    preview = synced.service.preview(synced.project)
    kept = sync(synced)
    assert [(c.entry.kind, c.entry.name, c.reason.value) for c in preview.conflicts] == [
        ("document", "extra.md", "markdown_deleted")]
    assert synced.documents.read(synced.project, "TASK-002", "extra.md")  # nothing was deleted
    assert [e.name for e in kept.kept] == ["extra.md"]

    sync(synced, synced.project, decide("document", "TASK-002", choice, "extra.md"))

    if choice is DB:  # the database state holds: the file is written again
        assert (synced.tmp / "md" / "items" / "TASK-002" / "extra.md").is_file()
    else:  # the file state holds: the document goes from the database
        with pytest.raises(DocumentNotFoundError):
            synced.documents.read(synced.project, "TASK-002", "extra.md")


def test_the_state_is_stored_only_for_entries_both_sides_agree_on(synced: Setup, md_project: Source):
    folder = str(synced.tmp / "md")
    edit_item(synced, synced.project, "TASK-001", title="In the database")
    edit_item(synced, md_project, "TASK-001", title="In the file")
    before = synced.states.load(synced.project.id, folder)

    sync(synced)
    assert synced.states.load(synced.project.id, folder) == before  # the conflict keeps its old state

    sync(synced, synced.project, decide("item", "TASK-001", DB))
    version = synced.backlogs.get(synced.project, "TASK-001").version
    assert synced.states.load(synced.project.id, folder)[EntryKey("item", "TASK-001")] == EntryState(version, version)


def test_a_run_that_fails_half_way_leaves_no_wrong_state(synced: Setup, md_project: Source):
    class Failing:
        """The document store, except that writing into the folder fails."""

        def __getattr__(self, name: str) -> object:
            return getattr(synced.documents, name)

        def write(self, source: Source, item_id: str, name: str, content: str,
                  expected_version: str | None) -> None:
            if source.backend == "markdown":
                raise OSError("disk full")
            synced.documents.write(source, item_id, name, content, expected_version)

    broken = SyncService(synced.backlogs, Failing(), states=synced.states)  # type: ignore[arg-type]
    edit_item(synced, synced.project, "TASK-001", title="Changed")
    write_doc(synced, synced.project, "TASK-002", "notes.md", "# changed\n")

    with pytest.raises(OSError):
        sync(synced, service=broken)

    preview = synced.service.preview(synced.project)  # still plainly "changed in the database", never a conflict
    assert preview.conflicts == () and len(preview.changed) == 1 and len(preview.changed_documents) == 1


def test_the_direction_restricts_which_side_is_written(synced: Setup, md_project: Source):
    edit_item(synced, synced.project, "TASK-001", title="In the database")
    edit_item(synced, md_project, "TASK-002", title="In the file")

    sync(synced, direction=TO_MD)
    assert synced.backlogs.get(md_project, "TASK-001").title == "In the database"
    assert synced.backlogs.get(synced.project, "TASK-002").title != "In the file"

    sync(synced, direction=FROM_MD)
    assert synced.backlogs.get(synced.project, "TASK-002").title == "In the file"


def test_an_unreadable_folder_stops_before_anything_is_changed(synced: Setup):
    md = synced.tmp / "md"
    (md / "TODO.md").write_text("Not a backlog.\n", encoding="utf-8")
    before = synced.versions(synced.project)

    with pytest.raises(SyncSourceInvalidError) as error:
        synced.service.preview(synced.project, FROM_MD)
    with pytest.raises(SyncSourceInvalidError):
        synced.service.run(synced.project, "x", (), FROM_MD, "en")
    with pytest.raises(SyncSourceInvalidError):
        synced.service.run(synced.project, "x", (), TO_MD, "en")  # the target cannot be read either

    assert error.value.code == "sync_source_invalid"
    assert synced.versions(synced.project) == before
    assert (md / "TODO.md").read_text(encoding="utf-8") == "Not a backlog.\n"


def test_a_change_after_the_preview_makes_it_stale(synced: Setup):
    edit_item(synced, synced.project, "TASK-001", title="Planned")
    preview = synced.service.preview(synced.project)
    md_before = synced.files(synced.tmp / "md")
    edit_item(synced, synced.project, "TASK-001", title="Late")

    with pytest.raises(SyncStaleError):
        synced.service.run(synced.project, preview.token, (), None, "en")
    with pytest.raises(SyncStaleError):
        synced.service.run(synced.project, None, (), None, "en")

    assert synced.files(synced.tmp / "md") == md_before


def test_a_change_of_the_stored_state_makes_the_preview_stale_too(synced: Setup):
    preview = synced.service.preview(synced.project)
    synced.states.save(synced.project.id, str(synced.tmp / "md"), {}, [EntryKey("item", "TASK-001")])

    with pytest.raises(SyncStaleError):
        synced.service.run(synced.project, preview.token, (), None, "en")


def test_the_target_folder_is_created_in_the_given_language(setup: Setup):
    setup.service.run(setup.project, setup.service.preview(setup.project).token, (), TO_MD, "de")

    assert (setup.tmp / "md" / "archive.md").read_text(encoding="utf-8").startswith("# Projekt-Backlog-Archiv")


def test_reading_from_a_missing_folder_is_an_error_but_a_full_sync_creates_it(setup: Setup):
    with pytest.raises(SyncSourceInvalidError) as error:
        setup.service.preview(setup.project, FROM_MD)

    assert error.value.details["reason"] == "not_found"
    assert len(setup.service.preview(setup.project).created) > 0


def test_projects_without_a_sync_folder_or_in_markdown_are_refused(setup: Setup):
    with pytest.raises(SyncPathMissingError):
        setup.service.preview(dataclasses.replace(setup.project, sync_path=None), TO_MD)
    with pytest.raises(SyncSameBackendError):
        setup.service.preview(Source(project="P", path=str(FIXTURE), id="m"), TO_MD)


def test_a_markdown_project_is_read_into_the_database_under_its_id(setup: Setup):
    sync(setup)
    moving = Source(project="P", path=str(setup.tmp / "md"), id="moving")

    preview = setup.service.preview(moving)
    setup.service.run(moving, preview.token, (), None, "en")

    assert len(preview.created) == len(setup.versions(setup.project)) and preview.conflicts == ()
    database = dataclasses.replace(moving, backend="database", path="")
    assert setup.versions(database) == setup.versions(setup.project)
    assert setup.documents.read(database, "TASK-002", "notes.md").startswith("# Notes for TASK-002")


def test_a_project_is_in_sync_when_nothing_would_change(setup: Setup):
    assert not setup.service.in_sync(setup.project, TO_MD)  # the folder does not exist yet
    sync(setup)

    assert setup.service.in_sync(setup.project, TO_MD)
    assert setup.service.in_sync(setup.project, FROM_MD)


def test_a_difference_in_either_side_or_in_a_document_is_not_in_sync(synced: Setup, md_project: Source):
    (synced.tmp / "md" / "items" / "TASK-002" / "notes.md").write_text("# other\n", encoding="utf-8")
    assert not synced.service.in_sync(synced.project, TO_MD)

    sync(synced)
    synced.backlogs.create(synced.project, Item(id="TASK-071", title="Only in the database", project="P"))

    assert not synced.service.in_sync(synced.project, TO_MD)  # would be created in the folder
    assert not synced.service.in_sync(synced.project, FROM_MD)


def test_in_sync_of_a_broken_folder_is_an_error_not_a_no(synced: Setup):
    (synced.tmp / "md" / "TODO.md").write_text("Not a backlog.\n", encoding="utf-8")

    with pytest.raises(SyncSourceInvalidError):
        synced.service.in_sync(synced.project, FROM_MD)


# A markdown project that keeps a database mirror: the folder is the primary source.

def _markdown_primary(setup: Setup) -> tuple[Source, Source]:
    """The folder holds the fixture backlog with one trashed item; returns the project and its database mirror."""
    edit_item(setup, setup.project, "TASK-003", deleted="2026-09-28")
    sync(setup)
    project = Source(project="P", path=str(setup.tmp / "md"), backend="markdown", id="folder", mirror_database=True)
    mirror = dataclasses.replace(project, backend="database", path="", mirror_database=False)
    return project, mirror


def test_the_mirror_of_a_markdown_project_takes_over_everything_including_archive_trash_and_documents(setup: Setup):
    project, mirror = _markdown_primary(setup)

    preview = setup.service.preview(project)
    setup.service.run(project, preview.token, (), None, "en")

    assert setup.versions(mirror) == setup.versions(setup.project)
    assert setup.backlogs.get(mirror, "TASK-003").deleted == "2026-09-28"
    assert setup.backlogs.get(mirror, "TASK-000").location is Location.ARCHIVE
    assert setup.documents.read(mirror, "TASK-002", "notes.md") == setup.documents.read(setup.project, "TASK-002",
                                                                                          "notes.md")
    assert setup.service.in_sync(project, FROM_MD) and setup.service.in_sync(project, TO_MD)


def test_a_change_in_the_mirror_is_carried_into_the_folder_of_a_markdown_project(setup: Setup):
    project, mirror = _markdown_primary(setup)
    sync(setup, project)
    edit_item(setup, mirror, "TASK-001", title="Edited in mirror")

    preview = setup.service.preview(project)
    sync(setup, project)

    assert [e.label for e in preview.changed] == ["TASK-001"]
    assert "**Edited in mirror**" in (setup.tmp / "md" / "TODO.md").read_text(encoding="utf-8")
    assert setup.service.in_sync(project, FROM_MD)


def test_what_only_the_mirror_has_is_carried_to_the_folder_and_nothing_is_deleted(setup: Setup):
    project, mirror = _markdown_primary(setup)
    sync(setup, project)
    setup.backlogs.create(mirror, Item(id="TASK-070", title="Only in the mirror", project="P"))

    result = sync(setup, project)

    assert [e.label for e in result.resolved] == ["TASK-070"]
    assert setup.backlogs.get(dataclasses.replace(project), "TASK-070").title == "Only in the mirror"
    assert setup.versions(mirror) == setup.versions(project)


def test_a_markdown_project_without_a_database_mirror_is_only_read_into_the_database(setup: Setup):
    sync(setup)
    moving = Source(project="P", path=str(setup.tmp / "md"), id="moving")

    result = sync(setup, moving)

    assert len(result.resolved) > 0 and all(e.origin and e.origin.value == "markdown" for e in result.resolved)


class Heard:
    """Records what the sync tells the listener about items whose status changed."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def item_status_changed(self, project: str, item_id: str, status: str) -> None:
        self.calls.append((project, item_id, status))

    def item_deleted(self, project: str, item_id: str) -> None: ...


def _listening(setup: Setup, listener: object) -> SyncService:
    return SyncService(setup.backlogs, setup.documents, listener, states=setup.states)  # type: ignore[arg-type]


def _completed_in_markdown(setup: Setup, md_project: Source) -> Item:
    """Sets one open item to Completed in the exported folder, as an editor outside would."""
    open_item = next(i for i in setup.backlogs.load(md_project).items if i.status != "Completed")
    edit_item(setup, md_project, open_item.id, status="Completed")
    return open_item


def test_a_status_change_that_the_sync_brings_into_the_primary_source_is_announced(synced: Setup, md_project: Source):
    heard = Heard()
    changed = _completed_in_markdown(synced, md_project)

    sync(synced, service=_listening(synced, heard))

    assert heard.calls == [("P", changed.id, "Completed")]


def test_a_sync_into_the_mirror_or_without_status_changes_announces_nothing(synced: Setup, md_project: Source):
    heard = Heard()
    edit_item(synced, synced.project, "TASK-001", status="Completed")  # a database project: the folder is the mirror

    sync(synced, service=_listening(synced, heard))
    sync(synced, service=_listening(synced, heard))  # now equal

    assert heard.calls == []


def test_a_listener_that_fails_does_not_fail_the_sync(synced: Setup, md_project: Source):
    class Broken(Heard):
        def item_status_changed(self, project: str, item_id: str, status: str) -> None:
            raise RuntimeError("boom")

    _completed_in_markdown(synced, md_project)

    result = sync(synced, service=_listening(synced, Broken()))

    assert len(result.resolved) == 1


# --- backup of the database before a sync writes to it (TASK-031) ---

class RecordingBackup:
    def __init__(self, fail: bool = False) -> None:
        self.reasons: list[str] = []
        self.fail = fail

    def create(self, reason: str) -> str | None:
        if self.fail:
            raise DatabaseBackupFailedError("disk full")
        self.reasons.append(reason)
        return "backup.db"


def _with_backup(setup: Setup, backup: RecordingBackup) -> SyncService:
    return SyncService(setup.backlogs, setup.documents, db_backup=backup, states=setup.states)


def test_a_sync_into_the_database_makes_a_backup_first(synced: Setup, md_project: Source):
    backup = RecordingBackup()
    edit_item(synced, md_project, "TASK-001", title="From the file")

    sync(synced, service=_with_backup(synced, backup))

    assert backup.reasons == ["sync"]


def test_no_backup_for_a_preview_for_a_sync_into_the_folder_or_when_nothing_changes(synced: Setup):
    backup = RecordingBackup()
    service = _with_backup(synced, backup)
    edit_item(synced, synced.project, "TASK-001", title="From the database")

    service.preview(synced.project)
    sync(synced, service=service)  # writes the folder only
    sync(synced, service=service)  # nothing left to change

    assert backup.reasons == []


def test_a_failed_backup_leaves_the_database_and_the_folder_unchanged(synced: Setup, md_project: Source):
    service = _with_backup(synced, RecordingBackup(fail=True))
    edit_item(synced, md_project, "TASK-001", title="From the file")
    files_before, versions_before = synced.files(synced.tmp / "md"), synced.versions(synced.project)
    token = service.preview(synced.project).token

    with pytest.raises(DatabaseBackupFailedError):
        service.run(synced.project, token, (), None, "en")

    assert synced.versions(synced.project) == versions_before
    assert synced.files(synced.tmp / "md") == files_before


# --- the automatic mode (STORY-059): strict reading, merge markers, backup reason ---

class Markers:
    def __init__(self, files: list[str] | None = None) -> None:
        self.files = files or []

    def files_with_markers(self, source: Source) -> list[str]:
        assert source.backend == "markdown"
        return self.files


def _auto(setup: Setup, backup: RecordingBackup | None = None, markers: Markers | None = None) -> SyncService:
    return SyncService(setup.backlogs, setup.documents, db_backup=backup, states=setup.states,
                       markers=markers or Markers())


def test_an_automatic_run_does_not_create_a_missing_folder(setup: Setup):
    service = _auto(setup)

    with pytest.raises(SyncSourceInvalidError) as error:
        service.preview(setup.project, auto=True)

    assert error.value.details["reason"] == "not_found"
    assert len(service.preview(setup.project).created) > 0  # a manual sync would create it


def test_an_automatic_run_stops_at_files_with_merge_markers_and_changes_nothing(synced: Setup, md_project: Source):
    edit_item(synced, md_project, "TASK-001", title="From the file")
    service = _auto(synced, markers=Markers(["TODO.md"]))
    versions = synced.versions(synced.project)

    with pytest.raises(SyncSourceInvalidError) as error:
        service.preview(synced.project, auto=True)
    with pytest.raises(SyncSourceInvalidError):
        service.run(synced.project, "x", auto=True)

    assert error.value.details["reason"] == "merge_markers" and "TODO.md" in error.value.message
    assert synced.versions(synced.project) == versions
    assert len(service.preview(synced.project).changed) == 1  # a manual sync is not stopped by the check


def test_an_automatic_run_carries_conflict_free_changes_only_and_never_deletes(synced: Setup, md_project: Source):
    backup = RecordingBackup()
    service = _auto(synced, backup)
    edit_item(synced, md_project, "TASK-001", title="Free change from the file")
    edit_item(synced, synced.project, "TASK-002", title="In the database")
    edit_item(synced, md_project, "TASK-002", title="In the file")
    gone = [i for i in synced.backlogs.load(md_project).items if i.id != "TASK-003"]
    synced.backlogs.write_backlog(md_project, gone, "en")  # a deletion on the file side

    preview = service.preview(synced.project, auto=True)
    result = service.run(synced.project, preview.token, auto=True)

    assert {e.label for e in result.resolved} == {"TASK-001"}
    assert {e.label for e in result.deferred} == {"TASK-002", "TASK-003"} and result.deleted == ()
    assert synced.backlogs.get(synced.project, "TASK-003")  # still in the database
    assert synced.backlogs.get(synced.project, "TASK-001").title == "Free change from the file"
    assert backup.reasons == ["auto"]


def test_an_automatic_run_without_a_write_to_the_database_makes_no_backup(synced: Setup):
    backup = RecordingBackup()
    service = _auto(synced, backup)
    edit_item(synced, synced.project, "TASK-001", title="Only in the database")

    service.run(synced.project, service.preview(synced.project, auto=True).token, auto=True)

    assert backup.reasons == []
    assert "**Only in the database**" in (synced.tmp / "md" / "TODO.md").read_text(encoding="utf-8")

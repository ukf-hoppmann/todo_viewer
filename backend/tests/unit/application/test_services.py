"""Service tests against in-memory fakes of the ports: no files, no web framework."""
from __future__ import annotations

import itertools
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import date

import pytest

from todo_viewer.application.services import ItemService, RetypeService, SourceLookup, SourceService, TrashService
from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.creation import ItemFactory
from todo_viewer.domain.editing import ChangeSet, EditPlanner
from todo_viewer.domain.errors import (
    BackupFailedError,
    ConfigMissingError,
    DocumentNotFoundError,
    DuplicateSourceError,
    FileChangedError,
    InvalidSourceError,
    InvalidValueError,
    ItemNotFoundError,
    LifecycleViolationError,
    NotEditableError,
    SourceGoneError,
    SyncPathMissingError,
    SyncRequiredError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.retype import RetypePlanner
from todo_viewer.domain.source import Source, SourceProblem
from todo_viewer.domain.sync import SyncDirection
from todo_viewer.domain.trash import TrashPlanner


class InMemorySources:
    def __init__(self, sources: list[Source] | None):
        self.sources = sources

    def all(self) -> list[Source]:
        if self.sources is None:
            raise ConfigMissingError()
        return list(self.sources)

    @contextmanager
    def edit(self) -> Iterator[list[Source]]:
        working = list(self.sources or [])
        yield working
        self.sources = working


class FakeBacklogs:
    def __init__(self, items: list[Item] | None = None, archive: bool = True):
        self.items = items or []
        self.archive = archive
        self.applied: list[ChangeSet] = []
        self.fail_apply_all = False
        self.initialized: list[tuple[str, str]] = []

    def initialize(self, source: Source, language: str) -> None:
        self.initialized.append((source.path, language))

    def check(self, source: Source) -> SourceProblem | None:
        if not source.path and source.backend == "markdown":
            return SourceProblem("missing_path", "Path is missing.")
        return SourceProblem("no_todo", "No TODO.md in this folder.") if "plain" in source.path else None

    def load(self, source: Source) -> Backlog:
        return Backlog(items=self.items, archive_available=self.archive)

    def get(self, source: Source, item_id: str) -> Item:
        found = next((i for i in self.items if i.id == item_id), None)
        if found is None:
            raise ItemNotFoundError(item_id)
        return found

    def archive_available(self, source: Source) -> bool:
        return self.archive

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        self.applied.append(changes)
        return item

    def create(self, source: Source, item: Item) -> Item:
        self.items.append(item)
        return item

    def apply_all(self, source: Source, plan: list[tuple[Item, ChangeSet]]) -> list[Item]:
        if self.fail_apply_all:
            raise FileChangedError()
        changed = [(i.id, c.applied_to(i)) for i, c in plan]
        by_old_id = dict(changed)
        self.items = [by_old_id.get(i.id, i) for i in self.items]
        return [i for _, i in changed]

    def delete(self, source: Source, items: list[Item]) -> None:
        for item in items:
            self.items.remove(item)


class FakeDocuments:
    """Documents keyed `<item id>/<name>`."""

    def __init__(self, files: dict[str, str] | None = None) -> None:
        self.deleted: list[str] = []
        self.files = files or {}
        self.renamed: list[tuple[str, str, dict[str, str]]] = []

    def read(self, source: Source, item_id: str, name: str) -> str:
        if f"{item_id}/{name}" not in self.files:
            raise DocumentNotFoundError(name)
        return self.files[f"{item_id}/{name}"]

    def write(self, source: Source, item_id: str, name: str, content: str, expected_version: str | None) -> None:
        self.files[f"{item_id}/{name}"] = content

    def append(self, source: Source, item_id: str, name: str, text: str, header: str) -> str:
        return text

    def delete_documents(self, source: Source, item_id: str) -> None:
        self.deleted.append(item_id)

    def relabel_documents(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        self.renamed.append((old_id, new_id, dict(renames)))
        for key in [k for k in self.files if k.startswith(f"{old_id}/")]:
            name = key.split("/", 1)[1]
            self.files[f"{new_id}/{renames.get(name, name)}"] = self.files.pop(key)


class Names:
    def suggest(self, path: str) -> str:
        return "suggested"


class FakeSync:
    """Says whether a project is in sync; remembers what it was asked."""

    def __init__(self, in_sync: bool = True):
        self.in_sync_result = in_sync
        self.asked: list[tuple[Source, SyncDirection]] = []

    def in_sync(self, source: Source, direction: SyncDirection) -> bool:
        self.asked.append((source, direction))
        return self.in_sync_result


class FakeBackup:
    def __init__(self, error: BackupFailedError | None = None):
        self.error = error
        self.created: list[Source] = []

    def create(self, source: Source) -> str:
        if self.error:
            raise self.error
        self.created.append(source)
        return "/backups/x"


def _ids() -> Callable[[], str]:
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


def _sources(initial: list[Source] | None = None, sync: FakeSync | None = None, backup: FakeBackup | None = None
             ) -> tuple[SourceService, InMemorySources]:
    repo = InMemorySources(initial)
    return SourceService(repo, FakeBacklogs(), Names(), sync or FakeSync(), backup or FakeBackup(), _ids()), repo


def test_add_source_trims_and_suggests_name():
    service, repo = _sources()

    added = service.add(" /repo/docs/ ", "  ")

    assert added == Source("suggested", "/repo/docs", id="id-1")
    assert repo.sources == [added]


def test_add_source_rejects_problems_and_duplicates():
    service, _ = _sources([Source("A", "/a")])

    with pytest.raises(InvalidSourceError) as missing:
        service.add("  ", None)
    with pytest.raises(InvalidSourceError) as no_todo:
        service.add("/plain", None)
    with pytest.raises(DuplicateSourceError):
        service.add("/a", "B")

    assert (missing.value.code, no_todo.value.code) == ("missing_path", "no_todo")


def test_create_backlog_initializes_folder_and_adds_source():
    backlogs = FakeBacklogs()
    repo = InMemorySources([Source("A", "/a", id="a")])
    service = SourceService(repo, backlogs, Names(), FakeSync(), FakeBackup(), _ids())

    created = service.create_backlog(" /new/docs/todo/ ", None, "de")
    with pytest.raises(DuplicateSourceError):
        service.create_backlog("/a", None, "en")
    with pytest.raises(InvalidSourceError) as missing:
        service.create_backlog(" ", None, "en")

    assert created == Source("suggested", "/new/docs/todo", id="id-1")
    assert repo.sources == [Source("A", "/a", id="a"), created]
    assert backlogs.initialized == [("/new/docs/todo", "de")]
    assert missing.value.code == "missing_path"


def test_update_keeps_extra_fields_and_remove_by_id():
    a, b = Source("A", "/a", id="a", extra={"color": "red"}), Source("B", "/b", id="b")
    service, repo = _sources([a, b])

    updated = service.update(a.id, "/a2", "A2")
    with pytest.raises(SourceGoneError):
        service.remove("unknown")
    removed = service.remove(b.id)

    assert updated.extra == {"color": "red"}
    assert removed == b
    assert repo.sources == [Source("A2", "/a2", id=a.id)]


def test_a_markdown_project_moves_into_the_database_once_its_folder_is_read_in():
    md = Source("A", "/a", id="a", extra={"color": "red"})
    sync = FakeSync()
    service, repo = _sources([Source("Z", "/z", id="z"), md], sync)

    switched = service.update("a", "ignored", None, "database", "ignored too")

    assert switched == Source("A", "", backend="database", id="a", sync_path="/a")
    assert switched.extra == {"color": "red"}
    assert repo.sources[1] == switched and repo.sources[0].id == "z"
    assert sync.asked == [(md, SyncDirection.FROM_MD)]


def test_a_database_project_moves_back_to_its_sync_folder_once_it_is_written_out():
    db = Source("A", "", backend="database", id="a", sync_path="/a")
    sync = FakeSync()
    service, repo = _sources([db], sync)

    switched = service.update("a", "", "Renamed", "markdown", None)

    assert switched == Source("Renamed", "/a", backend="markdown", id="a", sync_path=None, mirror_database=True)
    assert repo.sources == [switched]
    assert sync.asked == [(db, SyncDirection.TO_MD)]


def test_a_markdown_project_can_keep_a_database_mirror_from_the_start():
    service, repo = _sources()

    added = service.add("/repo/docs", "P", mirror="database")

    assert added.mirror_database is True and repo.sources == [added]


def test_the_database_mirror_of_a_markdown_project_is_switched_on_and_off_and_otherwise_kept():
    service, repo = _sources([Source("A", "/a", id="a")])

    on = service.update("a", "/a", None, mirror="database")
    kept = service.update("a", "/a", "Renamed")
    off = service.update("a", "/a", None, mirror="none")

    assert (on.mirror, kept.mirror, off.mirror) == ("database", "database", "none")
    assert repo.sources == [off]


def test_the_markdown_mirror_of_a_database_project_needs_a_folder_and_goes_with_it():
    db = Source("A", "", backend="database", id="a", sync_path="/a")
    service, repo = _sources([db])

    with pytest.raises(SyncPathMissingError):
        service.update("a", "", "A", mirror="markdown", sync_path=None)
    off = service.update("a", "", "A", mirror="none", sync_path="/a")
    on = service.update("a", "", "A", mirror="markdown", sync_path="/b")

    assert (off.mirror, off.sync_path, on.mirror, on.sync_path) == ("none", None, "markdown", "/b")
    assert repo.sources == [on]


def test_a_mirror_on_the_primary_side_is_refused():
    service, repo = _sources([Source("A", "/a", id="a"), Source("B", "", backend="database", id="b")])

    with pytest.raises(InvalidValueError):
        service.update("a", "/a", None, mirror="markdown")
    with pytest.raises(InvalidValueError):
        service.update("b", "", "B", mirror="database")
    with pytest.raises(InvalidValueError):
        service.add("/c", "C", mirror="other")

    assert [s.mirror for s in repo.sources] == ["none", "none"]


def test_the_backend_is_not_switched_while_the_sides_differ():
    md = Source("A", "/a", id="a")
    service, repo = _sources([md], FakeSync(in_sync=False))

    with pytest.raises(SyncRequiredError):
        service.update("a", "/a", None, "database", None)

    assert repo.sources == [md]


def test_a_switch_to_markdown_cannot_take_a_folder_another_project_uses():
    other, db = Source("B", "/a", id="b"), Source("A", "", backend="database", id="a", sync_path="/a")
    service, repo = _sources([other, db])

    with pytest.raises(DuplicateSourceError):
        service.update("a", "", None, "markdown", None)

    assert repo.sources == [other, db]


def test_the_current_primary_source_is_backed_up_before_the_switch():
    md = Source("A", "/a", id="a")
    backup = FakeBackup()
    service, repo = _sources([md], backup=backup)

    switched = service.update("a", "/a", None, "database", None)

    assert backup.created == [md] and repo.sources == [switched]


def test_no_backup_is_made_when_the_switch_is_refused_anyway():
    md = Source("A", "/a", id="a")
    other, db = Source("B", "/a", id="b"), Source("C", "", backend="database", id="c", sync_path="/a")
    backup = FakeBackup()

    with pytest.raises(SyncRequiredError):
        _sources([md], FakeSync(in_sync=False), backup)[0].update("a", "/a", None, "database", None)
    with pytest.raises(DuplicateSourceError):
        _sources([other, db], backup=backup)[0].update("c", "", None, "markdown", None)

    assert backup.created == []


def test_a_failed_backup_stops_the_switch_and_changes_nothing():
    db = Source("A", "", backend="database", id="a", sync_path="/a")
    service, repo = _sources([db], backup=FakeBackup(BackupFailedError("disk full")))

    with pytest.raises(BackupFailedError) as error:
        service.update("a", "", None, "markdown", None)

    assert error.value.details == {"reason": "disk full"} and repo.sources == [db]


def test_an_ordinary_change_makes_no_backup():
    backup = FakeBackup()
    service, _ = _sources([Source("A", "/a", id="a")], backup=backup)

    service.update("a", "/a2", "A2")

    assert backup.created == []


def test_the_same_backend_is_no_switch():
    md = Source("A", "/a", id="a")
    sync = FakeSync(in_sync=False)
    service, _ = _sources([md], sync)

    assert service.update("a", "/a2", "A2", "markdown", None).path == "/a2"
    assert sync.asked == []


def test_lookup_by_id():
    a = Source("A", "/repo/docs")
    lookup = SourceLookup(InMemorySources([a]))

    assert lookup.by_id(a.id) == a
    with pytest.raises(SourceGoneError):
        lookup.by_id("unknown")


def _items(items: list[Item], archive: bool = True) -> tuple[ItemService, FakeBacklogs]:
    backlogs = FakeBacklogs(items, archive=archive)
    service = ItemService(backlogs, EditPlanner(), LifecycleRules(), ItemFactory(), lambda: date(2026, 9, 28))
    return service, backlogs


def test_item_get_by_id():
    item = Item(id="T-1", title="t", project="p", location=Location.ARCHIVE)
    service, _ = _items([item], archive=False)

    result = service.get(Source("p", "/p"), "T-1")

    assert (result.item, result.archive_supported) == (item, False)
    with pytest.raises(ItemNotFoundError):
        service.get(Source("p", "/p"), "T-2")


def test_item_edit_plans_with_archive_rules():
    item = Item(id="T-1", title="t", project="p")
    service, backlogs = _items([item])

    result = service.edit(Source("p", "/p"), "T-1", item.version, {"status": "Completed"}, "done")

    assert result.archive_supported
    assert backlogs.applied == [ChangeSet(set_fields=(("status", "Completed"), ("resolution", "done")),
                                          move_to=Location.ARCHIVE)]


def test_item_edit_rejects_stale_version():
    item = Item(id="T-1", title="t", project="p")
    service, backlogs = _items([item])

    with pytest.raises(VersionConflictError):
        service.edit(Source("p", "/p"), "T-1", "outdated", {"status": "In progress"}, None)
    assert backlogs.applied == []


def test_item_edit_checks_lifecycle_rules_before_writing():
    story = Item(id="S", title="s", project="p", item_type="Story", status="In progress")
    task = Item(id="T", title="t", project="p", parent="S", required_for_parent=True, status="Open")
    service, backlogs = _items([story, task])

    with pytest.raises(LifecycleViolationError) as err:
        service.edit(Source("p", "/p"), "S", story.version, {"status": "Completed"}, "done")

    assert err.value.details["id"] == "S"
    assert backlogs.applied == []


def test_item_create_assigns_id_and_checks_rules():
    story = Item(id="STORY-001", title="s", project="p", item_type="Story", status="Completed")
    service, backlogs = _items([story])
    fields = {"title": "New", "area": "a", "goal": "g", "completion_criteria": "c"}

    created = service.create(Source("p", "/p"), "Task", fields)
    with pytest.raises(LifecycleViolationError) as err:
        service.create(Source("p", "/p"), "Task", {**fields, "parent": "STORY-001", "required_for_parent": "Yes"})

    assert (created.item.id, created.item.created, created.item.status) == ("TASK-001", "2026-09-28", "Open")
    assert (err.value.code, err.value.details) == ("parent_closed", {"id": "TASK-002", "items": "STORY-001"})
    assert [i.id for i in backlogs.items] == ["STORY-001", "TASK-001"]


def test_trash_delete_restore_and_purge_with_children():
    story = Item(id="S", title="s", project="p", item_type="Story")
    task = Item(id="T", title="t", project="p", parent="S", required_for_parent=True)
    backlogs = FakeBacklogs([story, task])
    documents = FakeDocuments()
    trash = TrashService(backlogs, documents, TrashPlanner(LifecycleRules()), lambda: date(2026, 9, 28))
    src = Source("p", "/p")

    with pytest.raises(VersionConflictError):
        trash.delete(src, "S", "outdated", cascade=True)
    with pytest.raises(LifecycleViolationError) as warning:
        trash.delete(src, "S", story.version, cascade=False)
    deleted = trash.delete(src, "S", story.version, cascade=True)
    in_trash = trash.in_trash(src)
    restored = trash.restore(src, "S", in_trash[0].item.version)
    trash.delete(src, "S", restored[0].item.version, cascade=True)
    purged = trash.purge(src, "S", trash.in_trash(src)[0].item.version)

    assert warning.value.code == "has_children"
    assert [(r.item.id, r.item.deleted) for r in deleted] == [("S", "2026-09-28"), ("T", "2026-09-28")]
    assert [r.item.id for r in in_trash] == ["S", "T"]
    assert [(r.item.id, r.item.deleted) for r in restored] == [("S", None), ("T", None)]
    assert [r.item.id for r in purged] == ["S", "T"]
    assert (backlogs.items, documents.deleted) == ([], ["S", "T"])


def test_item_edit_rejects_field_before_touching_storage():
    service, backlogs = _items([])

    with pytest.raises(NotEditableError):
        service.edit(Source("p", "/p"), "x", "v", {"created": "x"}, None)
    assert backlogs.applied == []


# ---------- retype ----------

def _retype_service(items: list[Item], files: dict[str, str] | None = None):
    backlogs, documents = FakeBacklogs(items), FakeDocuments(files)
    return RetypeService(backlogs, documents, RetypePlanner(), LifecycleRules()), backlogs, documents


def _retype_items() -> list[Item]:
    return [
        Item(id="STORY-001", title="Story", project="p", item_type="Story", required_for_parent=None,
             notes=["STORY-001_notes.md"], summary="s"),
        Item(id="TASK-001", title="Child", project="p", parent="STORY-001", required_for_parent=True),
        Item(id="TASK-002", title="Other", project="p", dependencies=["STORY-001"],
             notes=["TASK-002_notes.md"], summary="s"),
    ]


def test_retype_gives_a_new_id_and_follows_references_and_documents():
    files = {"STORY-001/STORY-001_notes.md": "# STORY-001 — Story\n\nSiehe STORY-001.\n",
             "TASK-002/TASK-002_notes.md": "# TASK-002 — Other\n\nWartet auf `STORY-001`.\n"}
    service, backlogs, documents = _retype_service(_retype_items(), files)
    version = backlogs.items[0].version

    result = service.retype(Source("P", "/p"), "STORY-001", version, "Task")

    assert (result.item.id, result.item.item_type) == ("TASK-003", "Task")
    assert result.old_id == "STORY-001"
    assert [(n.code, n.details) for n in result.notices] == [
        ("external_references_may_remain", {"old_id": "STORY-001", "new_id": "TASK-003"})]
    assert result.item.notes == ["TASK-003_notes.md"]
    assert [(i.id, i.parent, i.dependencies) for i in backlogs.items] == [
        ("TASK-003", None, []), ("TASK-001", "TASK-003", []), ("TASK-002", None, ["TASK-003"])]
    assert documents.renamed == [("STORY-001", "TASK-003", {"STORY-001_notes.md": "TASK-003_notes.md"})]
    assert documents.files == {
        "TASK-003/TASK-003_notes.md": "# TASK-003 — Story\n\nSiehe TASK-003.\n",
        "TASK-002/TASK-002_notes.md": "# TASK-002 — Other\n\nWartet auf `TASK-003`.\n"}


def test_retype_without_documents_on_disk_still_works():
    service, backlogs, documents = _retype_service(_retype_items())

    result = service.retype(Source("P", "/p"), "STORY-001", backlogs.items[0].version, "Task")

    assert result.item.id == "TASK-003"
    assert documents.files == {}


def test_retype_checks_lifecycle_rules_before_touching_anything():
    items = _retype_items()
    service, backlogs, documents = _retype_service(items, {"TASK-002/TASK-002_notes.md": "x STORY-001"})
    before = list(backlogs.items)

    with pytest.raises(LifecycleViolationError) as err:
        service.retype(Source("P", "/p"), "TASK-001", backlogs.items[1].version, "Epic")  # an epic has no parent

    assert err.value.code == "epic_with_parent"
    assert backlogs.items == before
    assert documents.renamed == [] and documents.files == {"TASK-002/TASK-002_notes.md": "x STORY-001"}


def test_retype_does_not_count_flaws_the_item_already_had_under_its_old_id():
    items = _retype_items()
    items[2].summary = None  # has notes but no summary: a flaw of the files, not of the retype
    service, backlogs, _ = _retype_service(items)

    result = service.retype(Source("P", "/p"), "TASK-002", backlogs.items[2].version, "Story")

    assert result.item.id == "STORY-002"


def test_retype_rejects_stale_version():
    service, backlogs, documents = _retype_service(_retype_items())

    with pytest.raises(VersionConflictError):
        service.retype(Source("P", "/p"), "STORY-001", "stale", "Task")

    assert documents.renamed == []


def test_retype_restores_the_folder_if_the_backlog_cannot_be_written():
    files = {"STORY-001/STORY-001_notes.md": "# STORY-001\n"}
    service, backlogs, documents = _retype_service(_retype_items(), files)
    backlogs.fail_apply_all = True
    version = backlogs.items[0].version

    with pytest.raises(FileChangedError):
        service.retype(Source("P", "/p"), "STORY-001", version, "Task")

    assert documents.renamed == [
        ("STORY-001", "TASK-003", {"STORY-001_notes.md": "TASK-003_notes.md"}),
        ("TASK-003", "STORY-001", {"TASK-003_notes.md": "STORY-001_notes.md"})]
    assert documents.files == {"STORY-001/STORY-001_notes.md": "# STORY-001\n"}

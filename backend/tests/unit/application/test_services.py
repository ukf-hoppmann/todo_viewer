"""Service tests against in-memory fakes of the ports: no files, no web framework."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

import pytest

from todo_viewer.application.services import ItemService, SourceLookup, SourceService, TrashService
from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.creation import ItemFactory
from todo_viewer.domain.editing import ChangeSet, EditPlanner
from todo_viewer.domain.errors import (
    ConfigMissingError,
    DuplicateSourceError,
    InvalidSourceError,
    ItemNotFoundError,
    LifecycleViolationError,
    NotEditableError,
    SourceGoneError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.source import Source, SourceProblem
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
        self.initialized: list[tuple[str, str]] = []

    def initialize(self, source: Source, language: str) -> None:
        self.initialized.append((source.path, language))

    def check(self, source: Source) -> SourceProblem | None:
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
        changed = [c.applied_to(i) for i, c in plan]
        by_id = {i.id: i for i in changed}
        self.items = [by_id.get(i.id, i) for i in self.items]
        return changed

    def delete(self, source: Source, items: list[Item]) -> None:
        for item in items:
            self.items.remove(item)


class FakeDocuments:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def read(self, source: Source, relative_path: str) -> str:
        return ""

    def write(self, source: Source, relative_path: str, content: str, expected_version: str | None) -> None: ...

    def append(self, source: Source, relative_path: str, text: str, header: str) -> str:
        return text

    def delete_item_folder(self, source: Source, item_id: str) -> None:
        self.deleted.append(item_id)


class Names:
    def suggest(self, path: str) -> str:
        return "suggested"


def _sources(initial: list[Source] | None = None) -> tuple[SourceService, InMemorySources]:
    repo = InMemorySources(initial)
    return SourceService(repo, FakeBacklogs(), Names()), repo


def test_add_source_trims_and_suggests_name():
    service, repo = _sources()

    added = service.add(" /repo/docs/ ", "  ")

    assert added == Source("suggested", "/repo/docs")
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
    repo = InMemorySources([Source("A", "/a")])
    service = SourceService(repo, backlogs, Names())

    created = service.create_backlog(" /new/docs/todo/ ", None, "de")
    with pytest.raises(DuplicateSourceError):
        service.create_backlog("/a", None, "en")
    with pytest.raises(InvalidSourceError) as missing:
        service.create_backlog(" ", None, "en")

    assert created == Source("suggested", "/new/docs/todo")
    assert repo.sources == [Source("A", "/a"), created]
    assert backlogs.initialized == [("/new/docs/todo", "de")]
    assert missing.value.code == "missing_path"


def test_update_keeps_extra_fields_and_remove_by_id():
    a, b = Source("A", "/a", extra={"color": "red"}), Source("B", "/b")
    service, repo = _sources([a, b])

    updated = service.update(a.id, "/a2", "A2")
    with pytest.raises(SourceGoneError):
        service.remove("unknown")
    removed = service.remove(b.id)

    assert updated.extra == {"color": "red"}
    assert removed == b
    assert repo.sources == [Source("A2", "/a2")]


def test_source_id_is_stable_and_path_based():
    assert Source("A", "/a").id == Source("Renamed", "/a").id != Source("A", "/b").id


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

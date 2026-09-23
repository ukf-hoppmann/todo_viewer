"""Service tests against in-memory fakes of the ports: no files, no web framework."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from todo_viewer.application.services import ItemEditService, SourceLookup, SourceService
from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet, EditPlanner
from todo_viewer.domain.errors import (
    ConfigMissingError,
    DuplicateSourceError,
    InvalidSourceError,
    NotEditableError,
    SourceGoneError,
)
from todo_viewer.domain.item import Item, ItemRef, Location
from todo_viewer.domain.source import Source, SourceProblem


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

    def check(self, source: Source) -> SourceProblem | None:
        return SourceProblem("no_todo", "No TODO.md in this folder.") if "plain" in source.path else None

    def load(self, source: Source) -> Backlog:
        return Backlog(items=self.items, archive_available=self.archive)

    def find(self, source: Source, ref: ItemRef) -> Item:
        return next(i for i in self.items if i.ref == ref)

    def archive_available(self, source: Source) -> bool:
        return self.archive

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        self.applied.append(changes)
        return item


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


def test_update_keeps_extra_fields_and_remove_checks_path():
    service, repo = _sources([Source("A", "/a", extra={"color": "red"}), Source("B", "/b")])

    updated = service.update(0, "/a2", "A2")
    with pytest.raises(SourceGoneError):
        service.remove(1, expected_path="/other")
    removed = service.remove(1, expected_path="/b")

    assert updated.extra == {"color": "red"}
    assert removed == Source("B", "/b")
    assert repo.sources == [Source("A2", "/a2")]


def test_lookup_by_index():
    lookup = SourceLookup(InMemorySources([Source("A", "/a")]))

    assert lookup.get(0) == Source("A", "/a")
    with pytest.raises(SourceGoneError):
        lookup.get(1)


def test_item_edit_plans_with_archive_rules():
    item = Item(id="T-1", title="t", source_file="f", project="p", line=3)
    backlogs = FakeBacklogs([item], archive=True)
    service = ItemEditService(backlogs, EditPlanner())

    result = service.edit(Source("p", "/p"), item.ref, "status", "Completed", "done")

    assert result.archive_supported
    assert backlogs.applied == [ChangeSet(set_fields=(("status", "Completed"), ("resolution", "done")),
                                          move_to=Location.ARCHIVE)]


def test_item_edit_rejects_field_before_touching_storage():
    backlogs = FakeBacklogs([])
    service = ItemEditService(backlogs, EditPlanner())

    with pytest.raises(NotEditableError):
        service.edit(Source("p", "/p"), ItemRef("x", Location.ACTIVE, 1), "title", "x", None)
    assert backlogs.applied == []

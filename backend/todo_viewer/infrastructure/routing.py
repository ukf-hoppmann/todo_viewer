"""Routing adapters: send each call to the storage adapter of the source's backend."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeVar

from todo_viewer.application.ports import BacklogRepository, DocumentStore
from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import InvalidSourceError
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source, SourceProblem

Adapter = TypeVar("Adapter")


def _adapter_for(adapters: Mapping[str, Adapter], source: Source) -> Adapter:
    try:
        return adapters[source.backend]
    except KeyError:
        raise InvalidSourceError(f"Unknown storage backend '{source.backend}'.", code="unknown_backend") from None


class RoutingBacklogRepository:
    def __init__(self, backends: Mapping[str, BacklogRepository]):
        self._backends = backends

    def _for(self, source: Source) -> BacklogRepository:
        return _adapter_for(self._backends, source)

    def check(self, source: Source) -> SourceProblem | None:
        return self._for(source).check(source)

    def load(self, source: Source) -> Backlog:
        return self._for(source).load(source)

    def get(self, source: Source, item_id: str) -> Item:
        return self._for(source).get(source, item_id)

    def archive_available(self, source: Source) -> bool:
        return self._for(source).archive_available(source)

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        return self._for(source).apply(source, item, changes)

    def apply_all(self, source: Source, plan: Sequence[tuple[Item, ChangeSet]]) -> list[Item]:
        return self._for(source).apply_all(source, plan)

    def create(self, source: Source, item: Item) -> Item:
        return self._for(source).create(source, item)

    def delete(self, source: Source, items: Sequence[Item]) -> None:
        self._for(source).delete(source, items)

    def initialize(self, source: Source, language: str) -> None:
        self._for(source).initialize(source, language)

    def write_backlog(self, source: Source, items: Sequence[Item], language: str) -> None:
        self._for(source).write_backlog(source, items, language)


class RoutingDocumentStore:
    def __init__(self, backends: Mapping[str, DocumentStore]):
        self._backends = backends

    def _for(self, source: Source) -> DocumentStore:
        return _adapter_for(self._backends, source)

    def read(self, source: Source, item_id: str, name: str) -> str:
        return self._for(source).read(source, item_id, name)

    def write(self, source: Source, item_id: str, name: str, content: str, expected_version: str | None) -> None:
        self._for(source).write(source, item_id, name, content, expected_version)

    def append(self, source: Source, item_id: str, name: str, text: str, header: str) -> str:
        return self._for(source).append(source, item_id, name, text, header)

    def delete_documents(self, source: Source, item_id: str) -> None:
        self._for(source).delete_documents(source, item_id)

    def relabel_documents(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        self._for(source).relabel_documents(source, old_id, new_id, renames)

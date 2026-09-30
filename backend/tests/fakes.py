"""In-memory storage adapters that keep the port contract: the second implementation of the contract suite."""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.documents import content_version
from todo_viewer.domain.editing import ID_RE, ChangeSet
from todo_viewer.domain.errors import (
    BacklogExistsError,
    DocumentForbiddenError,
    DocumentNotFoundError,
    DuplicateItemError,
    ItemFolderExistsError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SourceProblem

DOCUMENT_SUFFIXES = {".md", ".markdown", ".txt"}


class InMemoryBacklogRepository:
    """Items per source, kept in list order like the entries of a file."""

    def __init__(self, items: Sequence[Item] = ()) -> None:
        self._items: dict[str, list[Item]] = {}
        self._seed = [dataclasses.replace(i) for i in items]

    def _stored(self, source: Source) -> list[Item]:
        return self._items.setdefault(source.id, [dataclasses.replace(i, project=source.project) for i in self._seed])

    def check(self, source: Source) -> SourceProblem | None:
        return None

    def load(self, source: Source) -> Backlog:
        return Backlog(items=[dataclasses.replace(i) for i in self._stored(source)], archive_available=True)

    def get(self, source: Source, item_id: str) -> Item:
        return self.load(source).find(item_id)

    def archive_available(self, source: Source) -> bool:
        return True

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        return self.apply_all(source, [(item, changes)])[0]

    def apply_all(self, source: Source, plan: Sequence[tuple[Item, ChangeSet]]) -> list[Item]:
        stored = self._stored(source)
        self._check_versions(stored, [item for item, _ in plan])
        changed = {item.id: changes.applied_to(item) for item, changes in plan}
        moved = [item.id for item, changes in plan if changes.move_to not in (None, item.location)]
        # Items stay in place unless they change list; moved ones go to the end of their new list.
        stored[:] = [changed.get(i.id, i) for i in stored if i.id not in moved] + [changed[m] for m in moved]
        return [dataclasses.replace(changed[item.id]) for item, _ in plan]

    def create(self, source: Source, item: Item) -> Item:
        stored = self._stored(source)
        if any(i.id == item.id for i in stored):
            raise DuplicateItemError(item.id)
        stored.append(dataclasses.replace(item, location=Location.ACTIVE))
        return dataclasses.replace(stored[-1])

    def delete(self, source: Source, items: Sequence[Item]) -> None:
        stored = self._stored(source)
        self._check_versions(stored, items)
        gone = {i.id for i in items}
        stored[:] = [i for i in stored if i.id not in gone]

    def initialize(self, source: Source, language: str) -> None:
        if source.id in self._items:
            raise BacklogExistsError()
        self._items[source.id] = []

    @staticmethod
    def _check_versions(stored: list[Item], items: Sequence[Item]) -> None:
        by_id = {i.id: i for i in stored}
        for item in items:
            current = by_id.get(item.id)
            if current is None or current.version != item.version:
                raise VersionConflictError(item.id)


class InMemoryDocumentStore:
    """Documents per source and item, addressed by item id and plain document name."""

    def __init__(self, documents: Mapping[tuple[str, str], str] | None = None) -> None:
        self._docs: dict[str, dict[tuple[str, str], str]] = {}
        self._seed = dict(documents or {})

    def _stored(self, source: Source) -> dict[tuple[str, str], str]:
        return self._docs.setdefault(source.id, dict(self._seed))

    def read(self, source: Source, item_id: str, name: str) -> str:
        docs = self._stored(source)
        key = self._key(item_id, name)
        if key not in docs:
            raise DocumentNotFoundError(name)
        return docs[key]

    def write(self, source: Source, item_id: str, name: str, content: str, expected_version: str | None) -> None:
        docs = self._stored(source)
        key = self._key(item_id, name)
        if key not in docs:
            if expected_version is not None:
                raise VersionConflictError(name)
        elif expected_version is None or content_version(docs[key]) != expected_version:
            raise VersionConflictError(name)
        docs[key] = content

    def append(self, source: Source, item_id: str, name: str, text: str, header: str) -> str:
        docs = self._stored(source)
        key = self._key(item_id, name)
        docs[key] = f"{header}\n{text}" if key not in docs else f"{docs[key].rstrip()}\n\n{text}"
        return docs[key]

    def delete_documents(self, source: Source, item_id: str) -> None:
        docs = self._stored(source)
        self._check_id(item_id)
        for key in [k for k in docs if k[0] == item_id]:
            del docs[key]

    def relabel_documents(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        docs = self._stored(source)
        self._check_id(old_id)
        self._check_id(new_id)
        for name in (*renames, *renames.values()):
            self._check_name(name)
        old = [k for k in docs if k[0] == old_id]
        if not old:
            return
        if any(k[0] == new_id for k in docs):
            raise ItemFolderExistsError(new_id)
        for key in old:
            docs[(new_id, renames.get(key[1], key[1]))] = docs.pop(key)

    @classmethod
    def _key(cls, item_id: str, name: str) -> tuple[str, str]:
        cls._check_id(item_id)
        cls._check_name(name)
        return item_id, name

    @staticmethod
    def _check_id(item_id: str) -> None:
        if not ID_RE.match(item_id) or item_id in {".", ".."}:
            raise DocumentForbiddenError()

    @staticmethod
    def _check_name(name: str) -> None:
        if not name or "/" in name or "." + name.rsplit(".", 1)[-1].lower() not in DOCUMENT_SUFFIXES:
            raise DocumentForbiddenError()

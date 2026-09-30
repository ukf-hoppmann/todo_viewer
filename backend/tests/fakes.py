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
    """Documents per source, addressed by their path relative to the backlog (`items/<ID>/<name>`)."""

    def __init__(self, files: Mapping[str, str] | None = None) -> None:
        self._files: dict[str, dict[str, str]] = {}
        self._seed = dict(files or {})

    def _stored(self, source: Source) -> dict[str, str]:
        return self._files.setdefault(source.id, dict(self._seed))

    def read(self, source: Source, relative_path: str) -> str:
        files = self._stored(source)
        self._check_path(relative_path)
        if relative_path not in files:
            raise DocumentNotFoundError(relative_path)
        return files[relative_path]

    def write(self, source: Source, relative_path: str, content: str, expected_version: str | None) -> None:
        files = self._stored(source)
        self._check_path(relative_path)
        if relative_path not in files:
            if expected_version is not None:
                raise VersionConflictError(relative_path)
        elif expected_version is None or content_version(files[relative_path]) != expected_version:
            raise VersionConflictError(relative_path)
        files[relative_path] = content

    def append(self, source: Source, relative_path: str, text: str, header: str) -> str:
        files = self._stored(source)
        self._check_path(relative_path)
        files[relative_path] = f"{header}\n{text}" if relative_path not in files \
            else f"{files[relative_path].rstrip()}\n\n{text}"
        return files[relative_path]

    def delete_item_folder(self, source: Source, item_id: str) -> None:
        files = self._stored(source)
        self._check_id(item_id)
        for path in [p for p in files if p.startswith(f"items/{item_id}/")]:
            del files[path]

    def rename_item_folder(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        files = self._stored(source)
        self._check_id(old_id)
        self._check_id(new_id)
        for name in (*renames, *renames.values()):
            if "/" in name or name in {"", ".", ".."}:
                raise DocumentForbiddenError()
        old = [p for p in files if p.startswith(f"items/{old_id}/")]
        if not old:
            return
        if any(p.startswith(f"items/{new_id}/") for p in files):
            raise ItemFolderExistsError(new_id)
        for path in old:
            name = path.rsplit("/", 1)[-1]
            files[f"items/{new_id}/{renames.get(name, name)}"] = files.pop(path)

    @staticmethod
    def _check_id(item_id: str) -> None:
        if not ID_RE.match(item_id) or item_id in {".", ".."}:
            raise DocumentForbiddenError()

    @staticmethod
    def _check_path(relative_path: str) -> None:
        parts = relative_path.split("/")
        if ".." in parts or relative_path.startswith("/") or \
                "." + relative_path.rsplit(".", 1)[-1].lower() not in DOCUMENT_SUFFIXES:
            raise DocumentForbiddenError()

"""Ports: what the application needs from the outside world. Adapters implement them."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any, Protocol

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source, SourceProblem


class BacklogRepository(Protocol):
    def check(self, source: Source) -> SourceProblem | None:
        """Why the source cannot be read, or None if it is usable."""

    def load(self, source: Source) -> Backlog: ...

    def get(self, source: Source, item_id: str) -> Item:
        """The item with this id, active or archived.

        Raises ItemNotFoundError, or DuplicateItemError if the id is not unique.
        """

    def archive_available(self, source: Source) -> bool: ...

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        """Persists the changes and returns the item as stored afterwards.

        Raises VersionConflictError if the stored item no longer matches `item.version`.
        """

    def apply_all(self, source: Source, plan: Sequence[tuple[Item, ChangeSet]]) -> list[Item]:
        """Like `apply` for several items at once, all or nothing."""

    def create(self, source: Source, item: Item) -> Item:
        """Stores a new active item; raises DuplicateItemError if its id is taken."""

    def delete(self, source: Source, items: Sequence[Item]) -> None:
        """Removes the items for good; raises VersionConflictError if one changed since it was read."""

    def initialize(self, source: Source, language: str) -> None:
        """Creates an empty backlog (with its folders) in `language`; raises BacklogExistsError if there is one."""


class SourceRepository(Protocol):
    def all(self) -> list[Source]:
        """Raises ConfigMissingError if no configuration exists yet."""

    def edit(self) -> AbstractContextManager[list[Source]]:
        """Exclusive read-modify-write; the yielded list is saved on normal exit."""


class DocumentStore(Protocol):
    def read(self, source: Source, relative_path: str) -> str:
        """A notes/spec file inside the source; raises DocumentForbidden/NotFound errors."""

    def write(self, source: Source, relative_path: str, content: str, expected_version: str | None) -> None:
        """Replaces a document still at `expected_version` (None: must not exist); else VersionConflictError."""

    def append(self, source: Source, relative_path: str, text: str, header: str) -> str:
        """Appends to a document (a new one starts with `header`) and returns the new content."""

    def delete_item_folder(self, source: Source, item_id: str) -> None:
        """Deletes the item's document folder with all files in it, if there is one."""

    def rename_item_folder(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        """Moves `items/<old_id>/` to `items/<new_id>/` and renames files in it (old name -> new name).

        Does nothing if there is no folder; raises ItemFolderExistsError if the target folder exists.
        """


class ProjectNameSuggester(Protocol):
    def suggest(self, path: str) -> str: ...


@dataclass(frozen=True)
class FolderEntry:
    name: str
    has_todo: bool


@dataclass(frozen=True)
class FolderListing:
    path: str
    parent: str | None
    has_todo: bool
    dirs: list[FolderEntry] = field(default_factory=list)
    error: str | None = None


class FolderBrowser(Protocol):
    def browse(self, path: str | None) -> FolderListing:
        """Subfolders of `path` (default start folder if None; nearest existing ancestor if missing)."""


class UiStateStore(Protocol):
    def load(self) -> dict[str, Any]: ...

    def save(self, state: dict[str, Any]) -> None: ...


__all__ = [
    "BacklogRepository",
    "DocumentStore",
    "FolderBrowser",
    "FolderEntry",
    "FolderListing",
    "ProjectNameSuggester",
    "SourceRepository",
    "UiStateStore",
]

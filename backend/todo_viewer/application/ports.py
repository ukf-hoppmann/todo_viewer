"""Ports: what the application needs from the outside world. Adapters implement them."""
from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any, Protocol

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.item import Item, ItemRef
from todo_viewer.domain.source import Source, SourceProblem


class BacklogRepository(Protocol):
    def check(self, source: Source) -> SourceProblem | None:
        """Why the source cannot be read, or None if it is usable."""

    def load(self, source: Source) -> Backlog: ...

    def find(self, source: Source, ref: ItemRef) -> Item:
        """The item at `ref`; raises EntryMovedError if it is not there anymore."""

    def archive_available(self, source: Source) -> bool: ...

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        """Persists the changes and returns the item as stored afterwards."""


class SourceRepository(Protocol):
    def all(self) -> list[Source]:
        """Raises ConfigMissingError if no configuration exists yet."""

    def edit(self) -> AbstractContextManager[list[Source]]:
        """Exclusive read-modify-write; the yielded list is saved on normal exit."""


class DocumentStore(Protocol):
    def read(self, source: Source, relative_path: str) -> str:
        """A notes/spec file inside the source; raises DocumentForbidden/NotFound errors."""


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

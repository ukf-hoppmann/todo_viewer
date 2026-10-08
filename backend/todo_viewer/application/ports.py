"""Ports: what the application needs from the outside world. Adapters implement them."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.item import Item
from todo_viewer.domain.notes import (
    Link,
    LinkRole,
    LinkTarget,
    NewNote,
    NewTrigger,
    Note,
    NoteChanges,
    Topic,
    Trigger,
)
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

    def write_backlog(self, source: Source, items: Sequence[Item], language: str) -> None:
        """Makes the backlog hold exactly `items` (each in its own location, in the given order).

        Items already stored stay the same items, with their documents; the others go. Missing files of a
        markdown backlog are created in `language`. Raises the source's problem if the backlog is unusable.
        """


class SourceRepository(Protocol):
    def all(self) -> list[Source]:
        """Raises ConfigMissingError if no configuration exists yet."""

    def edit(self) -> AbstractContextManager[list[Source]]:
        """Exclusive read-modify-write; the yielded list is saved on normal exit."""


class DocumentStore(Protocol):
    """Notes and specs of items, addressed by item id and document name; the adapter decides where they live."""

    def read(self, source: Source, item_id: str, name: str) -> str:
        """Raises DocumentForbiddenError for names the store does not accept, DocumentNotFoundError if missing."""

    def write(self, source: Source, item_id: str, name: str, content: str, expected_version: str | None) -> None:
        """Replaces a document still at `expected_version` (None: must not exist); else VersionConflictError."""

    def append(self, source: Source, item_id: str, name: str, text: str, header: str) -> str:
        """Appends to a document (a new one starts with `header`) and returns the new content."""

    def delete_documents(self, source: Source, item_id: str) -> None:
        """Deletes all documents of the item, if it has any."""

    def delete_document(self, source: Source, item_id: str, name: str) -> None:
        """Deletes one document, if it exists; raises DocumentForbiddenError for names the store does not accept."""

    def relabel_documents(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        """Moves the documents of `old_id` to `new_id` and renames some of them (old name -> new name).

        Does nothing if there are none; raises ItemFolderExistsError if `new_id` has documents already.
        """


class NoteRepository(Protocol):
    """Topics, notes, links, and triggers of all projects, addressed by project id plus label.

    Writes are transactional. Triggers are only stored here; whether one has arrived is decided in `domain`.
    """

    def create_topic(self, project: str, name: str, parent: str | None, due_at: datetime | None,
                     max_depth: int) -> Topic:
        """Raises TopicNotFoundError for an unknown `parent`, TopicTooDeepError beyond `max_depth`."""

    def get_topic(self, project: str, label: str) -> Topic: ...

    def list_topics(self, project: str) -> list[Topic]: ...

    def update_topic(self, project: str, label: str, name: str, due_at: datetime | None) -> Topic: ...

    def move_topic(self, project: str, label: str, parent: str | None, max_depth: int) -> Topic:
        """Raises TopicLoopError or TopicTooDeepError (the whole subtree counts)."""

    def create_note(self, project: str, new: NewNote) -> Note:
        """Raises TopicNotFoundError for an unknown topic."""

    def get_note(self, project: str, label: str) -> Note:
        """Active or in the trash; raises NoteNotFoundError."""

    def list_notes(self, project: str, include_deleted: bool = False) -> list[Note]: ...

    def update_note(self, project: str, label: str, expected_version: str, changes: NoteChanges) -> Note:
        """Raises VersionConflictError if the stored note no longer has `expected_version`."""

    def delete_note(self, project: str, label: str, at: datetime) -> Note:
        """Moves the note to the trash."""

    def restore_note(self, project: str, label: str) -> Note: ...

    def move_note(self, project: str, label: str, target_project: str, target_topic: str | None, at: datetime) -> Note:
        """Creates the note in `target_project` with a new label (links, triggers, and documents come along, links
        from other notes follow) and puts the old one in the trash. Returns the new note."""

    def add_link(self, project: str, label: str, target: LinkTarget, role: LinkRole) -> Link: ...

    def remove_link(self, project: str, label: str, link_id: int) -> None: ...

    def links_of(self, project: str, label: str) -> list[Link]: ...

    def links_to(self, target: LinkTarget) -> list[Link]:
        """Links of any project that point at `target`; the note of a link is in `Link.note` with its project in
        `Link.project`."""

    def relink_item(self, project: str, old_label: str, new_label: str) -> None:
        """Points every link and trigger on the item `old_label` of `project` at `new_label`."""

    def add_trigger(self, project: str, label: str, new: NewTrigger) -> Trigger:
        """An event trigger also gets a link with role `trigger` to its item."""

    def triggers_of(self, project: str, label: str) -> list[Trigger]: ...

    def mark_fired(self, project: str, label: str, trigger_id: int, at: datetime) -> Trigger: ...

    def remove_trigger(self, project: str, label: str, trigger_id: int) -> None:
        """Removes the trigger and the link that belongs to it."""


class NoteDocumentStore(Protocol):
    """Notes and specs of notes (`<LABEL>_notes.md`, `<LABEL>_spec.md`), addressed by project id, label, and name."""

    def names(self, project: str, label: str) -> list[str]: ...

    def read(self, project: str, label: str, name: str) -> str:
        """Raises DocumentForbiddenError for names the store does not accept, DocumentNotFoundError if missing."""

    def write(self, project: str, label: str, name: str, content: str, expected_version: str | None) -> None:
        """Replaces a document still at `expected_version` (None: must not exist); else VersionConflictError."""

    def append(self, project: str, label: str, name: str, text: str, header: str) -> str: ...

    def delete_document(self, project: str, label: str, name: str) -> None: ...


@dataclass(frozen=True)
class StorageDescription:
    """What the central database is: its type (e.g. "sqlite"), where it is (no secrets), its schema version."""

    kind: str
    location: str
    schema_version: int


class StorageInfo(Protocol):
    def describe(self) -> StorageDescription:
        """Opens the database (migrating it if needed) and reports what it is."""


class RawBackup(Protocol):
    """A byte-exact copy of a project's files, for the backends that keep the project in files."""

    def copy(self, source: Source, target: str) -> bool:
        """Copies the project into the new folder `target` and returns True; False if the backend has no files to
        copy (the caller then exports the data instead). Raises OSError if a copy cannot be made or differs."""


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
    "NoteDocumentStore",
    "NoteRepository",
    "ProjectNameSuggester",
    "RawBackup",
    "SourceRepository",
    "StorageDescription",
    "StorageInfo",
    "UiStateStore",
]

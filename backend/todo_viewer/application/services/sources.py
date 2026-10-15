from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Callable
from typing import Protocol

from todo_viewer.domain.errors import (
    AutoSyncNeedsMirrorError,
    DuplicateSourceError,
    InvalidSourceError,
    InvalidValueError,
    SourceGoneError,
    SyncPathMissingError,
    SyncRequiredError,
    ValueRequiredError,
)
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import SyncDirection

from ..ports import BacklogRepository, ProjectNameSuggester, SourceRepository


class SyncCheck(Protocol):
    def in_sync(self, source: Source, direction: SyncDirection) -> bool:
        """True if a sync of the project in `direction` would find nothing to do."""


class BackupMaker(Protocol):
    def create(self, source: Source) -> str:
        """Saves the project's current primary source; raises BackupFailedError if that is not possible."""


class SourceLookup:
    """Finds configured sources by their stable id."""

    def __init__(self, sources: SourceRepository):
        self._sources = sources

    def by_id(self, source_id: str) -> Source:
        found = next((s for s in self._sources.all() if s.id == source_id), None)
        if found is None:
            raise SourceGoneError()
        return found


class SourceService:
    """Adds, changes and removes configured backlog folders."""

    def __init__(self, sources: SourceRepository, backlogs: BacklogRepository, names: ProjectNameSuggester,
                 sync: SyncCheck, backup: BackupMaker, new_id: Callable[[], str] = lambda: str(uuid.uuid4())):
        self._sources = sources
        self._backlogs = backlogs
        self._names = names
        self._sync = sync
        self._backup = backup
        self._new_id = new_id

    def all(self) -> list[Source]:
        return self._sources.all()

    def add(self, path: str, project: str | None, backend: str = "markdown", sync_path: str | None = None,
            mirror: str | None = None, auto_sync: bool | None = None) -> Source:
        """A markdown project is registered by its folder; a database project needs a name only.

        `mirror` names the other side to keep: "database" for a markdown project, "markdown" (needs `sync_path`)
        for a database one; "none" keeps none (a given `sync_path` is kept for later), nothing leaves the default.
        """
        source = self._mirrored(dataclasses.replace(self._validated(path, project, backend), id=self._new_id(),
                                                    sync_path=_optional_path(sync_path)), mirror)
        source = self._auto_synced(source, auto_sync)
        with self._sources.edit() as sources:
            if self._taken(sources, source.path):
                raise DuplicateSourceError()
            sources.append(source)
        return source

    def create_backlog(self, path: str, project: str | None, language: str) -> Source:
        """Creates an empty backlog in the folder and adds it as a source."""
        path = self._normalized(path)
        with self._sources.edit() as sources:
            if any(s.path == path for s in sources):
                raise DuplicateSourceError()
            self._backlogs.initialize(Source(project="", path=path), language)
            source = dataclasses.replace(self._validated(path, project), id=self._new_id())
            sources.append(source)
        return source

    def update(self, source_id: str, path: str, project: str | None, backend: str | None = None,
               sync_path: str | None = None, mirror: str | None = None, auto_sync: bool | None = None) -> Source:
        """Changes name, folder, sync folder, and mirror; with another `backend` the project is moved there instead.

        A move needs both sides in sync (SyncRequiredError otherwise): sync first, then switch. The project keeps
        its id, and its folder changes sides: `path` of a markdown project is the `sync_path` of a database one.
        The current primary source is backed up first (BackupFailedError: nothing is changed). The former primary
        side stays as the mirror. `path`, `sync_path` and `mirror` are not read when the backend
        changes; a `project` name is.

        `mirror` switches the other side on or off: "database" / "none" for a markdown project, "markdown" (needs
        `sync_path`) / "none" for a database one; nothing leaves it as it is. Switching a database project's mirror
        off keeps its folder (send it again with `sync_path`), so switching it on needs no new one; the folder goes
        only when `sync_path` is emptied.
        """
        with self._sources.edit() as sources:
            index = self._index_of(sources, source_id)
            current = sources[index]
            if backend is not None and backend != current.backend:
                sources[index] = self._switched(current, [s for i, s in enumerate(sources) if i != index],
                                                project, backend)
                return sources[index]
            candidate = self._validated(path, project, current.backend)
            if self._taken([s for i, s in enumerate(sources) if i != index], candidate.path):
                raise DuplicateSourceError()
            changed = dataclasses.replace(current.updated(candidate.project, candidate.path),
                                          sync_path=_optional_path(sync_path))
            changed = self._auto_synced(self._mirrored(changed, mirror), auto_sync)
            if (changed.markdown_path, changed.mirror) != (current.markdown_path, current.mirror):
                changed = dataclasses.replace(changed, baseline=None)  # a side is another one: no last sync to compare
            sources[index] = changed
            return changed

    def _switched(self, current: Source, others: list[Source], project: str | None, backend: str) -> Source:
        """The project on the other backend; nothing is changed unless both sides are in sync and the current
        primary source is backed up."""
        to_database = backend == "database"
        if not self._sync.in_sync(current, SyncDirection.FROM_MD if to_database else SyncDirection.TO_MD):
            raise SyncRequiredError()
        name = (project or "").strip() or current.project
        moved = (dataclasses.replace(current, project=name, backend=backend, path="", sync_path=current.path,
                                     mirror_database=False, baseline=None)
                 if to_database else
                 dataclasses.replace(current, project=name, backend=backend, path=current.sync_path or "",
                                     sync_path=None, mirror_database=True, baseline=None))
        problem = self._backlogs.check(moved)
        if problem:
            raise InvalidSourceError(problem.message, code=problem.code)
        if self._taken(others, moved.path):
            raise DuplicateSourceError()
        self._backup.create(current)
        return moved

    @staticmethod
    def _auto_synced(source: Source, auto_sync: bool | None) -> Source:
        """`source` with the automatic sync switched on or off; None leaves it as it is. On needs a mirror."""
        if auto_sync is None:
            return source
        if auto_sync and source.mirror == "none":
            raise AutoSyncNeedsMirrorError()
        return dataclasses.replace(source, auto_sync=auto_sync)

    @staticmethod
    def _mirrored(source: Source, mirror: str | None) -> Source:
        """`source` with the mirror asked for; None leaves it as it is."""
        if mirror is None:
            return source
        allowed = ("none", "database") if source.backend == "markdown" else ("none", "markdown")
        if mirror not in allowed:
            raise InvalidValueError("mirror", allowed)
        if source.backend == "markdown":
            return dataclasses.replace(source, mirror_database=mirror == "database")
        if mirror == "none":  # the folder stays (as sent), only the mirror is off
            return dataclasses.replace(source, mirror_disabled=True)
        if not source.sync_path:
            raise SyncPathMissingError()
        return dataclasses.replace(source, mirror_disabled=False)

    def remove(self, source_id: str) -> Source:
        with self._sources.edit() as sources:
            return sources.pop(self._index_of(sources, source_id))

    @staticmethod
    def _index_of(sources: list[Source], source_id: str) -> int:
        index = next((i for i, s in enumerate(sources) if s.id == source_id), None)
        if index is None:
            raise SourceGoneError()
        return index

    @staticmethod
    def _normalized(path: str) -> str:
        path = path.strip().rstrip("/")
        if not path:
            raise InvalidSourceError("Path is missing.", code="missing_path")
        return path

    @staticmethod
    def _taken(sources: list[Source], path: str) -> bool:
        """Only folders identify a project; projects without one (database) never clash."""
        return bool(path) and any(s.path == path for s in sources)

    def _validated(self, path: str, project: str | None, backend: str = "markdown") -> Source:
        """What the storage needs is checked by its adapter (e.g. a folder with TODO.md for markdown)."""
        path = path.strip().rstrip("/")
        problem = self._backlogs.check(Source(project="", path=path, backend=backend))
        if problem:
            raise InvalidSourceError(problem.message, code=problem.code)
        name = (project or "").strip() or (self._names.suggest(path) if path else "")
        if not name:
            raise ValueRequiredError("project")
        return Source(project=name, path=path, backend=backend)


def _optional_path(path: str | None) -> str | None:
    path = (path or "").strip().rstrip("/")
    return path or None

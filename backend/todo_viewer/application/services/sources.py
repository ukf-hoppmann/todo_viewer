from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Callable

from todo_viewer.domain.errors import DuplicateSourceError, InvalidSourceError, SourceGoneError
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, ProjectNameSuggester, SourceRepository


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
                 new_id: Callable[[], str] = lambda: str(uuid.uuid4())):
        self._sources = sources
        self._backlogs = backlogs
        self._names = names
        self._new_id = new_id

    def all(self) -> list[Source]:
        return self._sources.all()

    def add(self, path: str, project: str | None) -> Source:
        source = dataclasses.replace(self._validated(path, project), id=self._new_id())
        with self._sources.edit() as sources:
            if any(s.path == source.path for s in sources):
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

    def update(self, source_id: str, path: str, project: str | None) -> Source:
        candidate = self._validated(path, project)
        with self._sources.edit() as sources:
            index = self._index_of(sources, source_id)
            if any(i != index and s.path == candidate.path for i, s in enumerate(sources)):
                raise DuplicateSourceError()
            sources[index] = sources[index].updated(candidate.project, candidate.path)
            return sources[index]

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

    def _validated(self, path: str, project: str | None) -> Source:
        path = self._normalized(path)
        source = Source(project="", path=path)
        problem = self._backlogs.check(source)
        if problem:
            raise InvalidSourceError(problem.message, code=problem.code)
        return Source(project=(project or "").strip() or self._names.suggest(path), path=path)

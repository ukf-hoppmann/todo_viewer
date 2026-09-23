from __future__ import annotations

from pathlib import PurePath

from todo_viewer.domain.errors import DuplicateSourceError, InvalidSourceError, SourceGoneError
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, ProjectNameSuggester, SourceRepository


class SourceLookup:
    """Finds configured sources by id (API v2), by index or by folder (legacy API)."""

    def __init__(self, sources: SourceRepository):
        self._sources = sources

    def by_id(self, source_id: str) -> Source:
        found = next((s for s in self._sources.all() if s.id == source_id), None)
        if found is None:
            raise SourceGoneError()
        return found

    def by_index(self, index: int, expected_path: str | None = None) -> Source:
        sources = self._sources.all()
        if not 0 <= index < len(sources):
            raise SourceGoneError("Source not found.")
        if expected_path and sources[index].path != expected_path:
            raise SourceGoneError()
        return sources[index]

    def by_folder(self, folder: PurePath) -> Source:
        found = next((s for s in self._sources.all() if PurePath(s.path) == folder), None)
        if found is None:
            raise SourceGoneError()
        return found


class SourceService:
    """Adds, changes and removes configured backlog folders."""

    def __init__(self, sources: SourceRepository, backlogs: BacklogRepository, names: ProjectNameSuggester):
        self._sources = sources
        self._backlogs = backlogs
        self._names = names

    def all(self) -> list[Source]:
        return self._sources.all()

    def add(self, path: str, project: str | None) -> Source:
        source = self._validated(path, project)
        with self._sources.edit() as sources:
            if any(s.path == source.path for s in sources):
                raise DuplicateSourceError()
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

    def _validated(self, path: str, project: str | None) -> Source:
        path = path.strip().rstrip("/")
        if not path:
            raise InvalidSourceError("Path is missing.", code="missing_path")
        source = Source(project="", path=path)
        problem = self._backlogs.check(source)
        if problem:
            raise InvalidSourceError(problem.message, code=problem.code)
        return Source(project=(project or "").strip() or self._names.suggest(path), path=path)

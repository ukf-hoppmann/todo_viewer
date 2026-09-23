from __future__ import annotations

from todo_viewer.domain.errors import DuplicateSourceError, InvalidSourceError, SourceGoneError
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, ProjectNameSuggester, SourceRepository


class SourceLookup:
    """Resolves the index the UI uses to address a configured source."""

    def __init__(self, sources: SourceRepository):
        self._sources = sources

    def get(self, index: int, expected_path: str | None = None) -> Source:
        sources = self._sources.all()
        if not 0 <= index < len(sources):
            raise SourceGoneError("Source not found.")
        if expected_path and sources[index].path != expected_path:
            raise SourceGoneError()
        return sources[index]


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

    def update(self, index: int, path: str, project: str | None) -> Source:
        candidate = self._validated(path, project)
        with self._sources.edit() as sources:
            if not 0 <= index < len(sources):
                raise SourceGoneError()
            if any(i != index and s.path == candidate.path for i, s in enumerate(sources)):
                raise DuplicateSourceError()
            sources[index] = sources[index].updated(candidate.project, candidate.path)
            return sources[index]

    def remove(self, index: int, expected_path: str | None) -> Source:
        with self._sources.edit() as sources:
            if not 0 <= index < len(sources) or (expected_path and sources[index].path != expected_path):
                raise SourceGoneError()
            return sources.pop(index)

    def _validated(self, path: str, project: str | None) -> Source:
        path = path.strip().rstrip("/")
        if not path:
            raise InvalidSourceError("Path is missing.", code="missing_path")
        source = Source(project="", path=path)
        problem = self._backlogs.check(source)
        if problem:
            raise InvalidSourceError(problem.message, code=problem.code)
        return Source(project=(project or "").strip() or self._names.suggest(path), path=path)

from __future__ import annotations

from pathlib import Path

from todo_viewer.domain.item import Location
from todo_viewer.domain.source import Source, SourceProblem

from .syntax import ARCHIVE_FILE, TODO_FILE


class SourcePathResolver:
    """Turns a configured source path into a folder; relative paths are relative to `base_dir`."""

    def __init__(self, base_dir: Path):
        self._base_dir = base_dir

    def resolve(self, path: str) -> Path:
        folder = Path(path).expanduser()
        return folder if folder.is_absolute() else self._base_dir / folder


class BacklogLayout:
    """File layout of a backlog folder: TODO.md (active) and optionally archive.md."""

    FILES = {Location.ACTIVE: TODO_FILE, Location.ARCHIVE: ARCHIVE_FILE}

    def __init__(self, folder: Path):
        self.folder = folder

    def file(self, location: Location) -> Path:
        return self.folder / self.FILES[location]

    def archive_available(self) -> bool:
        return all(self.file(loc).exists() for loc in Location)

    def problem(self) -> SourceProblem | None:
        if not self.folder.exists():
            return SourceProblem("not_found", "Folder not found.")
        if not self.folder.is_dir():
            return SourceProblem("not_a_dir", "Path is not a folder.")
        if not self.file(Location.ACTIVE).is_file():
            return SourceProblem("no_todo", f"No {TODO_FILE} in this folder.")
        return None


class LayoutFactory:
    def __init__(self, resolver: SourcePathResolver):
        self._resolver = resolver

    def for_source(self, source: Source) -> BacklogLayout:
        return BacklogLayout(self._resolver.resolve(source.path))

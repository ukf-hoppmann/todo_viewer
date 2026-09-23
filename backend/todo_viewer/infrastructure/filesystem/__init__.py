"""Local file system adapters: folder browser and project name suggestion."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from todo_viewer.application.ports import FolderEntry, FolderListing

from ..markdown.layout import SourcePathResolver
from ..markdown.syntax import TODO_FILE


class LocalFolderBrowser:
    def __init__(self, start_dir: Callable[[], Path], resolver: SourcePathResolver):
        self._start_dir = start_dir
        self._resolver = resolver

    def browse(self, path: str | None) -> FolderListing:
        target = self._resolver.resolve(path) if path else self._start_dir()
        # Fall back to the nearest existing ancestor (e.g. for a broken source path).
        while not target.is_dir() and target != target.parent:
            target = target.parent
        target = target.resolve()

        dirs: list[FolderEntry] = []
        error = None
        try:
            for entry in sorted(target.iterdir(), key=lambda e: e.name.lower()):
                if entry.name.startswith("."):
                    continue
                try:
                    if entry.is_dir():
                        dirs.append(FolderEntry(entry.name, (entry / TODO_FILE).is_file()))
                except OSError:
                    continue
        except OSError as exc:
            error = str(exc)

        return FolderListing(
            path=str(target),
            parent=str(target.parent) if target != target.parent else None,
            has_todo=(target / TODO_FILE).is_file(),
            dirs=dirs,
            error=error,
        )


def browse_start_from(env_value: str | None) -> Callable[[], Path]:
    """Start folder: $BROWSE_START if it is a folder, else the home folder (checked per call)."""

    def start() -> Path:
        if env_value and Path(env_value).is_dir():
            return Path(env_value)
        return Path.home()

    return start


class GitProjectNameSuggester:
    """Name of the enclosing git repository, falling back to the folder name."""

    def __init__(self, resolver: SourcePathResolver):
        self._resolver = resolver

    def suggest(self, path: str) -> str:
        folder = self._resolver.resolve(path)
        for candidate in [folder, *folder.parents]:
            if (candidate / ".git").exists():
                return candidate.name
        return folder.name

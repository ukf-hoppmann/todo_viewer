"""Plain files for the notes mirror. The adapter knows names and bytes only; formats and rules live in `domain`."""
from __future__ import annotations

import contextlib
import hashlib
import os
import re
import tempfile
from pathlib import Path

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import MirrorConflictError
from todo_viewer.domain.source import Source

FOLDER = "notes"
_STEM = r"(?:NOTE-\d+|new-[A-Za-z0-9.-]+)"
_NAME = re.compile(rf"^(?:{_STEM}(?:_(?:notes|spec(?:_[A-Za-z0-9-]+)?))?\.md|topics\.md|counters\.md)$")
_START = re.compile(r"^<{7}(\s|$)", re.MULTILINE)
_END = re.compile(r"^>{7}(\s|$)", re.MULTILINE)


class FilesNotesMirror:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir

    def read(self, source: Source) -> dict[str, str]:
        folder = self._folder(source)
        if not folder.is_dir():
            return {}
        return {p.name: _text(p) for p in sorted(folder.iterdir()) if p.is_file() and _NAME.match(p.name)}

    def write(self, source: Source, name: str, text: str, expected: str | None) -> None:
        path = self._path(source, name)
        current = _text(path) if path.is_file() else None
        _check(name, current, expected)
        if current is not None and "\r\n" in current and "\r\n" not in text:
            text = text.replace("\n", "\r\n")  # a file keeps its line ending
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="") as stream:
                stream.write(text)
            os.replace(temporary, path)
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(temporary)
            raise

    def delete(self, source: Source, name: str, expected: str) -> None:
        path = self._path(source, name)
        _check(name, _text(path) if path.is_file() else None, expected)
        path.unlink()

    def fingerprint(self, source: Source) -> str:
        digest = hashlib.sha256()
        for name, text in self.read(source).items():
            digest.update(f"\0{name}\0{content_version(text)}".encode())
        return digest.hexdigest()[:16]

    def files_with_markers(self, source: Source) -> list[str]:
        return [f"{FOLDER}/{name}" for name, text in self.read(source).items()
                if _START.search(text) and _END.search(text)]

    def _folder(self, source: Source) -> Path:
        path = Path(source.path).expanduser()
        return (path if path.is_absolute() else self._base_dir / path) / FOLDER

    def _path(self, source: Source, name: str) -> Path:
        if not _NAME.match(name):
            raise ValueError(f"not a notes file: {name!r}")
        return self._folder(source) / name


def _text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def _check(name: str, current: str | None, expected: str | None) -> None:
    """The file must be as it was when it was read: absent for None, otherwise of the expected version."""
    unchanged = current is None if expected is None else current is not None and content_version(current) == expected
    if not unchanged:
        raise MirrorConflictError(name)

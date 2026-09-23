"""Line-based text file access that keeps line endings and never leaves half-written files."""
from __future__ import annotations

import os
import shutil
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from todo_viewer.domain.errors import FileChangedError


@dataclass(frozen=True)
class FileStamp:
    mtime_ns: int
    size: int

    @classmethod
    def of(cls, path: Path) -> FileStamp:
        st = path.stat()
        return cls(st.st_mtime_ns, st.st_size)


@dataclass
class TextDocument:
    path: Path
    lines: list[str]
    newline: str
    stamp: FileStamp

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class TextFileStore:
    """Reads files as lines and writes them back atomically.

    `write` refuses to overwrite a file that changed since it was read, so a
    concurrent edit (e.g. by an agent) is reported instead of silently lost.
    """

    def read(self, path: Path) -> TextDocument:
        raw = path.read_bytes().decode("utf-8", errors="replace")
        newline = "\r\n" if "\r\n" in raw else "\n"
        return TextDocument(path, raw.replace("\r\n", "\n").split("\n"), newline, FileStamp.of(path))

    def ensure_unchanged(self, doc: TextDocument) -> None:
        if FileStamp.of(doc.path) != doc.stamp:
            raise FileChangedError()

    def write(self, doc: TextDocument) -> None:
        self.ensure_unchanged(doc)
        data = doc.newline.join(doc.lines).encode("utf-8")
        fd, tmp_name = tempfile.mkstemp(prefix=f".{doc.path.name}.", suffix=".tmp", dir=doc.path.parent)
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            shutil.copymode(doc.path, tmp)
            os.replace(tmp, doc.path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        doc.stamp = FileStamp.of(doc.path)


class KeyedLocks:
    """One re-entrant lock per key (e.g. per backlog folder) for in-process writers."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, threading.RLock] = {}

    @contextmanager
    def hold(self, key: str) -> Iterator[None]:
        with self._guard:
            lock = self._locks.setdefault(key, threading.RLock())
        with lock:
            yield

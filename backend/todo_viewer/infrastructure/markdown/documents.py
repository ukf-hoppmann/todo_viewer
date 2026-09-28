from __future__ import annotations

from pathlib import Path

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import DocumentForbiddenError, DocumentNotFoundError, VersionConflictError
from todo_viewer.domain.source import Source

from .layout import LayoutFactory
from .text_file import KeyedLocks, TextFileStore

DOCUMENT_SUFFIXES = {".md", ".markdown", ".txt"}


class MarkdownDocumentStore:
    """Notes/spec files; only markdown files inside the backlog folder are read or written."""

    def __init__(self, layouts: LayoutFactory, files: TextFileStore, locks: KeyedLocks):
        self._layouts = layouts
        self._files = files
        self._locks = locks

    def read(self, source: Source, relative_path: str) -> str:
        target = self._target(source, relative_path)
        if not target.is_file():
            raise DocumentNotFoundError(relative_path)
        return target.read_text(encoding="utf-8", errors="replace")

    def write(self, source: Source, relative_path: str, content: str, expected_version: str | None) -> None:
        """Replaces the file if it still has `expected_version`; None means the file must not exist yet."""
        target = self._target(source, relative_path)
        with self._locks.hold(str(self._folder(source))):
            if not target.is_file():
                if expected_version is not None:
                    raise VersionConflictError(relative_path)
                self._files.create(target, content)
                return
            doc = self._files.read(target)
            if expected_version is None or content_version(doc.text) != expected_version:
                raise VersionConflictError(relative_path)
            doc.lines = content.replace("\r\n", "\n").split("\n")
            self._files.write(doc)

    def append(self, source: Source, relative_path: str, text: str, header: str) -> str:
        """Appends `text` after a blank line; a new file starts with `header`. Returns the new content."""
        target = self._target(source, relative_path)
        with self._locks.hold(str(self._folder(source))):
            if not target.is_file():
                content = f"{header}\n{text}"
                self._files.create(target, content)
                return content
            doc = self._files.read(target)
            content = f"{doc.text.rstrip()}\n\n{text}"
            doc.lines = content.split("\n")
            self._files.write(doc)
            return content

    def _folder(self, source: Source) -> Path:
        return self._layouts.for_source(source).folder

    def _target(self, source: Source, relative_path: str) -> Path:
        base = self._folder(source).resolve()
        target = (base / relative_path).resolve()
        if not target.is_relative_to(base) or target.suffix.lower() not in DOCUMENT_SUFFIXES:
            raise DocumentForbiddenError()
        return target

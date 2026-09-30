from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.editing import ID_RE
from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    ItemFolderExistsError,
    VersionConflictError,
)
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

    def delete_item_folder(self, source: Source, item_id: str) -> None:
        """Deletes `items/<ID>/` with everything in it, if it exists."""
        if not ID_RE.match(item_id) or item_id in {".", ".."}:
            raise DocumentForbiddenError()
        items = (self._folder(source) / "items").resolve()
        target = (items / item_id).resolve()
        if target.parent != items:
            raise DocumentForbiddenError()
        with self._locks.hold(str(self._folder(source))):
            if target.is_dir():
                shutil.rmtree(target)

    def rename_item_folder(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        """Moves `items/<old_id>/` to `items/<new_id>/` and renames files in it (old name -> new name)."""
        items = (self._folder(source) / "items").resolve()
        old, new = self._item_folder(items, old_id), self._item_folder(items, new_id)
        for name in (*renames, *renames.values()):
            if "/" in name or name in {"", ".", ".."}:
                raise DocumentForbiddenError()
        with self._locks.hold(str(self._folder(source))):
            if not old.is_dir():
                return
            if new.exists():
                raise ItemFolderExistsError(new_id)
            old.rename(new)
            for before, after in renames.items():
                if (new / before).is_file():
                    (new / before).rename(new / after)

    @staticmethod
    def _item_folder(items: Path, item_id: str) -> Path:
        if not ID_RE.match(item_id) or item_id in {".", ".."}:
            raise DocumentForbiddenError()
        target = (items / item_id).resolve()
        if target.parent != items:
            raise DocumentForbiddenError()
        return target

    def _folder(self, source: Source) -> Path:
        return self._layouts.for_source(source).folder

    def _target(self, source: Source, relative_path: str) -> Path:
        base = self._folder(source).resolve()
        target = (base / relative_path).resolve()
        if not target.is_relative_to(base) or target.suffix.lower() not in DOCUMENT_SUFFIXES:
            raise DocumentForbiddenError()
        return target

from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    ItemFolderExistsError,
    VersionConflictError,
)
from todo_viewer.domain.source import Source

from .document_paths import document_file, item_folder
from .layout import LayoutFactory
from .text_file import KeyedLocks, TextFileStore


class MarkdownDocumentStore:
    """Notes/spec files in `items/<ID>/`; only markdown/text files inside the backlog folder are read or written."""

    def __init__(self, layouts: LayoutFactory, files: TextFileStore, locks: KeyedLocks):
        self._layouts = layouts
        self._files = files
        self._locks = locks

    def read(self, source: Source, item_id: str, name: str) -> str:
        target = document_file(self._folder(source), item_id, name)
        if not target.is_file():
            raise DocumentNotFoundError(name)
        return target.read_text(encoding="utf-8", errors="replace")

    def write(self, source: Source, item_id: str, name: str, content: str, expected_version: str | None) -> None:
        """Replaces the file if it still has `expected_version`; None means the file must not exist yet."""
        target = document_file(self._folder(source), item_id, name)
        with self._locks.hold(str(self._folder(source))):
            if not target.is_file():
                if expected_version is not None:
                    raise VersionConflictError(name)
                self._files.create(target, content)
                return
            doc = self._files.read(target)
            if expected_version is None or content_version(doc.text) != expected_version:
                raise VersionConflictError(name)
            doc.lines = content.replace("\r\n", "\n").split("\n")
            self._files.write(doc)

    def append(self, source: Source, item_id: str, name: str, text: str, header: str) -> str:
        """Appends `text` after a blank line; a new file starts with `header`. Returns the new content."""
        target = document_file(self._folder(source), item_id, name)
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

    def delete_documents(self, source: Source, item_id: str) -> None:
        """Deletes `items/<ID>/` with everything in it, if it exists."""
        target = item_folder(self._folder(source), item_id)
        with self._locks.hold(str(self._folder(source))):
            if target.is_dir():
                shutil.rmtree(target)

    def delete_document(self, source: Source, item_id: str, name: str) -> None:
        """Deletes the file of the document, if it exists."""
        target = document_file(self._folder(source), item_id, name)
        with self._locks.hold(str(self._folder(source))):
            target.unlink(missing_ok=True)

    def relabel_documents(self, source: Source, old_id: str, new_id: str, renames: Mapping[str, str]) -> None:
        """Moves `items/<old_id>/` to `items/<new_id>/` and renames files in it (old name -> new name)."""
        old, new = item_folder(self._folder(source), old_id), item_folder(self._folder(source), new_id)
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

    def _folder(self, source: Source) -> Path:
        return self._layouts.for_source(source).folder

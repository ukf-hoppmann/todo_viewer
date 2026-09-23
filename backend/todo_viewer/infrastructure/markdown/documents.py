from __future__ import annotations

from todo_viewer.domain.errors import DocumentForbiddenError, DocumentNotFoundError
from todo_viewer.domain.source import Source

from .layout import LayoutFactory

DOCUMENT_SUFFIXES = {".md", ".markdown", ".txt"}


class MarkdownDocumentStore:
    """Serves notes/spec files; only markdown files inside the backlog folder are readable."""

    def __init__(self, layouts: LayoutFactory):
        self._layouts = layouts

    def read(self, source: Source, relative_path: str) -> str:
        base = self._layouts.for_source(source).folder.resolve()
        target = (base / relative_path).resolve()
        if not target.is_relative_to(base) or target.suffix.lower() not in DOCUMENT_SUFFIXES:
            raise DocumentForbiddenError()
        if not target.is_file():
            raise DocumentNotFoundError(relative_path)
        return target.read_text(encoding="utf-8", errors="replace")

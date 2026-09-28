"""Markdown backlog adapter (TODO.md / archive.md)."""
from __future__ import annotations

from pathlib import Path

from .detector import FormatDetector
from .editors import BacklogEntryEditor, EntryLocator, EntryMover
from .field_mapper import BacklogFieldMapper, PriorityNormalizer
from .layout import LayoutFactory, SourcePathResolver
from .parsers import BacklogParser
from .repository import MarkdownBacklogRepository
from .text_file import KeyedLocks, TextFileStore


def build_markdown_repository(base_dir: Path) -> MarkdownBacklogRepository:
    return MarkdownBacklogRepository(
        layouts=LayoutFactory(SourcePathResolver(base_dir)),
        files=TextFileStore(),
        detector=FormatDetector(),
        parser=BacklogParser(BacklogFieldMapper(PriorityNormalizer())),
        locator=EntryLocator(),
        entry_editor=BacklogEntryEditor(),
        mover=EntryMover(),
        locks=KeyedLocks(),
    )


__all__ = ["MarkdownBacklogRepository", "build_markdown_repository"]

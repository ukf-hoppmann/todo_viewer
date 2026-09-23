"""Markdown backlog adapter (TODO.md / archive.md)."""
from __future__ import annotations

from pathlib import Path

from todo_viewer.domain.item import ItemFormat

from .detector import FormatDetector
from .editors import BacklogEntryEditor, ChecklistEntryEditor, EntryLocator, EntryMover
from .field_mapper import BacklogFieldMapper, PriorityNormalizer
from .layout import LayoutFactory, SourcePathResolver
from .parsers import BacklogParser, ChecklistParser
from .repository import MarkdownBacklogRepository
from .text_file import KeyedLocks, TextFileStore


def build_markdown_repository(base_dir: Path) -> MarkdownBacklogRepository:
    return MarkdownBacklogRepository(
        layouts=LayoutFactory(SourcePathResolver(base_dir)),
        files=TextFileStore(),
        detector=FormatDetector(),
        parsers={
            ItemFormat.BACKLOG_V2: BacklogParser(BacklogFieldMapper(PriorityNormalizer())),
            ItemFormat.CHECKBOX: ChecklistParser(),
        },
        locator=EntryLocator(),
        entry_editor=BacklogEntryEditor(),
        checklist_editor=ChecklistEntryEditor(),
        mover=EntryMover(),
        locks=KeyedLocks(),
    )


__all__ = ["MarkdownBacklogRepository", "build_markdown_repository"]

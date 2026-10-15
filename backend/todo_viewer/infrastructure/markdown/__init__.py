"""Markdown backlog adapter (TODO.md / archive.md)."""
from __future__ import annotations

from pathlib import Path

from .backup import MarkdownRawBackup
from .detector import FormatDetector
from .documents import MarkdownDocumentStore
from .editors import BacklogEntryEditor, EntryLocator, EntryMover, EntryRenderer
from .field_mapper import BacklogFieldMapper, PriorityNormalizer
from .layout import LayoutFactory, SourcePathResolver
from .merge_markers import MarkdownMergeMarkers
from .parsers import BacklogParser
from .repository import MarkdownBacklogRepository
from .templates import EmptyBacklogTemplates
from .text_file import KeyedLocks, TextFileStore


def build_markdown_repository(base_dir: Path, locks: KeyedLocks | None = None) -> MarkdownBacklogRepository:
    """`locks` should be shared with the document store of the same backlogs."""
    return MarkdownBacklogRepository(
        layouts=LayoutFactory(SourcePathResolver(base_dir)),
        files=TextFileStore(),
        detector=FormatDetector(),
        parser=BacklogParser(BacklogFieldMapper(PriorityNormalizer())),
        locator=EntryLocator(),
        entry_editor=BacklogEntryEditor(),
        mover=EntryMover(),
        renderer=EntryRenderer(),
        templates=EmptyBacklogTemplates(),
        locks=locks or KeyedLocks(),
    )


def build_markdown_documents(base_dir: Path, locks: KeyedLocks) -> MarkdownDocumentStore:
    return MarkdownDocumentStore(LayoutFactory(SourcePathResolver(base_dir)), TextFileStore(), locks)


__all__ = ["KeyedLocks", "MarkdownBacklogRepository", "MarkdownDocumentStore", "MarkdownMergeMarkers",
           "MarkdownRawBackup",
           "build_markdown_documents", "build_markdown_repository"]

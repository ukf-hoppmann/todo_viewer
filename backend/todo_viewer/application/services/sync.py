from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import DocumentForbiddenError, DocumentNotFoundError, SyncSourceInvalidError
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import (
    SyncDirection,
    SyncEntry,
    SyncPreview,
    check_token,
    merged_items,
    plan_sync,
    sync_pair,
)

from ..ports import BacklogRepository, DocumentStore

# A markdown folder that does not exist yet or has no TODO.md is a target that is still empty.
_EMPTY_TARGET = frozenset({"not_found", "no_todo"})


@dataclass(frozen=True)
class SyncResult:
    preview: SyncPreview  # what was found before anything was written
    deleted: tuple[SyncEntry, ...]  # missing entries that were removed from the target
    kept: tuple[SyncEntry, ...]  # missing entries that were left alone


@dataclass(frozen=True)
class _Side:
    source: Source
    items: list[Item]
    documents: dict[tuple[str, str], str]
    skipped: list[SyncEntry]
    exists: bool = True


class SyncService:
    """Copies all data of a database project to its markdown folder or back; nothing happens by itself."""

    def __init__(self, backlogs: BacklogRepository, documents: DocumentStore):
        self._backlogs = backlogs
        self._documents = documents
        self._locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)
        self._guard = threading.Lock()

    def preview(self, source: Source, direction: SyncDirection) -> SyncPreview:
        """What a sync would do; changes nothing."""
        with self._lock(source):
            _, _, preview = self._compare(source, direction)
            return preview

    def run(self, source: Source, direction: SyncDirection, token: str | None, delete_missing: bool,
            language: str) -> SyncResult:
        """Syncs in `direction`. `token` is the one of the preview the caller confirmed (SyncStaleError if either
        side changed since). Missing entries stay on the target unless `delete_missing`."""
        with self._lock(source):
            origin, target, preview = self._compare(source, direction)
            check_token(token, preview.token)
            items = merged_items(origin.items, target.items, delete_missing)
            writes = [(label, name, content) for (label, name), content in origin.documents.items()
                      if target.documents.get((label, name)) != content]

            if not target.exists:
                self._backlogs.initialize(target.source, language)
            if direction is SyncDirection.TO_MD:  # the backlog file goes last: it marks the export as complete
                self._write_documents(target.source, writes)
                self._backlogs.write_backlog(target.source, items, language)
            else:  # documents belong to items, which must exist first
                self._backlogs.write_backlog(target.source, items, language)
                self._write_documents(target.source, writes)
            if delete_missing:
                for entry in preview.missing:
                    self._documents.delete_documents(target.source, entry.label)
                for entry in preview.missing_documents:
                    assert entry.name is not None
                    self._documents.delete_document(target.source, entry.label, entry.name)
            return SyncResult(preview, deleted=self._missing(preview) if delete_missing else (),
                              kept=() if delete_missing else self._missing(preview))

    @staticmethod
    def _missing(preview: SyncPreview) -> tuple[SyncEntry, ...]:
        return (*preview.missing, *preview.missing_documents)

    def _lock(self, source: Source) -> threading.Lock:
        with self._guard:
            return self._locks[source.id]

    def _compare(self, source: Source, direction: SyncDirection) -> tuple[_Side, _Side, SyncPreview]:
        database, markdown = sync_pair(source)
        to_md = direction is SyncDirection.TO_MD
        origin_source, target_source = (database, markdown) if to_md else (markdown, database)
        origin = self._read(origin_source, empty_ok=False)
        target = self._read(target_source, empty_ok=to_md)
        preview = plan_sync(origin.items, target.items, origin.documents, target.documents, origin.skipped)
        return origin, target, preview

    def _read(self, source: Source, empty_ok: bool) -> _Side:
        """The items and documents of one side; an unusable backlog stops the sync before anything is written."""
        backlog = self._backlogs.load(source)
        if backlog.problem:
            if empty_ok and backlog.problem.code in _EMPTY_TARGET:
                return _Side(source, [], {}, [], exists=False)
            raise SyncSourceInvalidError(backlog.problem.code, backlog.problem.message)
        documents: dict[tuple[str, str], str] = {}
        skipped: list[SyncEntry] = []
        for item in backlog.items:
            for name in [*item.notes, *item.spec]:
                content = self._read_document(source, item, name)
                if content is None:
                    skipped.append(SyncEntry("document", item.id, item.title, name))
                else:
                    documents[(item.id, name)] = content
        return _Side(source, backlog.items, documents, skipped)

    def _read_document(self, source: Source, item: Item, name: str) -> str | None:
        """None for documents the sync cannot carry: written as a path, forbidden, or listed but missing."""
        if "/" in name:
            return None
        try:
            return self._documents.read(source, item.id, name)
        except (DocumentNotFoundError, DocumentForbiddenError):
            return None

    def _write_documents(self, target: Source, writes: Sequence[tuple[str, str, str]]) -> None:
        for label, name, content in writes:
            try:  # a file the target's item does not list yet is replaced, not refused
                current: str | None = self._documents.read(target, label, name)
            except DocumentNotFoundError:
                current = None
            self._documents.write(target, label, name, content,
                                  expected_version=None if current is None else content_version(current))


__all__ = ["SyncResult", "SyncService"]

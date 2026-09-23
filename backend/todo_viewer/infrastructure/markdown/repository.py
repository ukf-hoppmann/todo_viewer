"""Backlog repository backed by TODO.md / archive.md files."""
from __future__ import annotations

from collections.abc import Mapping

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet, Field
from todo_viewer.domain.errors import EntryMovedError
from todo_viewer.domain.item import Item, ItemFormat, ItemRef, Location
from todo_viewer.domain.source import Source, SourceProblem

from .detector import FormatDetector
from .editors import BacklogEntryEditor, ChecklistEntryEditor, EntryLocator, EntryMover
from .layout import BacklogLayout, LayoutFactory
from .parsers import ItemParser
from .text_file import KeyedLocks, TextDocument, TextFileStore


class MarkdownBacklogRepository:
    def __init__(
        self,
        layouts: LayoutFactory,
        files: TextFileStore,
        detector: FormatDetector,
        parsers: Mapping[ItemFormat, ItemParser],
        locator: EntryLocator,
        entry_editor: BacklogEntryEditor,
        checklist_editor: ChecklistEntryEditor,
        mover: EntryMover,
        locks: KeyedLocks,
    ):
        self._layouts = layouts
        self._files = files
        self._detector = detector
        self._parsers = parsers
        self._locator = locator
        self._entry_editor = entry_editor
        self._checklist_editor = checklist_editor
        self._mover = mover
        self._locks = locks

    # ---------- reading ----------

    def check(self, source: Source) -> SourceProblem | None:
        return self._layouts.for_source(source).problem()

    def load(self, source: Source) -> Backlog:
        layout = self._layouts.for_source(source)
        problem = layout.problem()
        if problem:
            return Backlog(problem=problem)

        backlog = Backlog(archive_available=layout.archive_available())
        for location in Location:
            path = layout.file(location)
            if not path.is_file():
                continue
            try:
                backlog.items.extend(self._parse(self._files.read(path), source, location))
            except Exception as exc:  # surfaced to the UI instead of crashing
                backlog.problem = SourceProblem("parse_error", f"{path.name}: {exc}")
        return backlog

    def archive_available(self, source: Source) -> bool:
        return self._layouts.for_source(source).archive_available()

    def find(self, source: Source, ref: ItemRef) -> Item:
        path = self._layouts.for_source(source).file(ref.location)
        if not path.is_file():
            raise EntryMovedError()
        items = self._parse(self._files.read(path), source, ref.location)
        found = next((i for i in items if i.id == ref.id and i.line == ref.line), None)
        if found is None:
            raise EntryMovedError()
        return found

    def _parse(self, doc: TextDocument, source: Source, location: Location) -> list[Item]:
        fmt = self._detector.detect(doc.text, location)
        if fmt is None:
            return []
        return self._parsers[fmt].parse(doc.lines, str(doc.path), source.project, location)

    # ---------- writing ----------

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        """Applies a ChangeSet to the stored entry and returns the item as stored afterwards."""
        layout = self._layouts.for_source(source)
        with self._locks.hold(str(layout.folder)):
            doc = self._files.read(layout.file(item.location))
            idx = self._locator.locate(doc.lines, item.ref, item.format, doc.path)

            if item.format is ItemFormat.CHECKBOX:
                for key, value in changes.set_fields:
                    if key == Field.STATUS:
                        self._checklist_editor.set_status(doc.lines, idx, value)
                self._files.write(doc)
                return self._reload(source, layout, item.id, item.location)

            for key, value in changes.set_fields:
                self._entry_editor.set_field(doc.lines, idx, key, value)
            for key in changes.remove_fields:
                self._entry_editor.remove_field(doc.lines, idx, key)

            if changes.move_to is None or changes.move_to is item.location:
                self._files.write(doc)
                return self._reload(source, layout, item.id, item.location)

            target = self._files.read(layout.file(changes.move_to))
            self._mover.append(target.lines, self._mover.cut(doc.lines, idx))
            self._files.ensure_unchanged(doc)
            # Write the destination first so the entry is never lost.
            self._files.write(target)
            self._files.write(doc)
            return self._reload(source, layout, item.id, changes.move_to)

    def _reload(self, source: Source, layout: BacklogLayout, item_id: str, location: Location) -> Item:
        items = self._parse(self._files.read(layout.file(location)), source, location)
        found = next((i for i in items if i.id == item_id), None)
        if found is None:
            raise EntryMovedError("Entry not found after saving.")
        return found

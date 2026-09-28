"""Backlog repository backed by TODO.md / archive.md files."""
from __future__ import annotations

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import DuplicateItemError, InvalidSourceError, ItemNotFoundError, VersionConflictError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SourceProblem

from .detector import FormatDetector
from .editors import BacklogEntryEditor, EntryLocator, EntryMover
from .layout import BacklogLayout, LayoutFactory
from .parsers import BacklogParser
from .syntax import TODO_FILE
from .text_file import KeyedLocks, TextDocument, TextFileStore


class MarkdownBacklogRepository:
    def __init__(
        self,
        layouts: LayoutFactory,
        files: TextFileStore,
        detector: FormatDetector,
        parser: BacklogParser,
        locator: EntryLocator,
        entry_editor: BacklogEntryEditor,
        mover: EntryMover,
        locks: KeyedLocks,
    ):
        self._layouts = layouts
        self._files = files
        self._detector = detector
        self._parser = parser
        self._locator = locator
        self._entry_editor = entry_editor
        self._mover = mover
        self._locks = locks

    # ---------- reading ----------

    def check(self, source: Source) -> SourceProblem | None:
        layout = self._layouts.for_source(source)
        return layout.problem() or self._format_problem(layout)

    def load(self, source: Source) -> Backlog:
        layout = self._layouts.for_source(source)
        problem = layout.problem() or self._format_problem(layout)
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

    def get(self, source: Source, item_id: str) -> Item:
        backlog = self.load(source)
        if backlog.problem:
            raise InvalidSourceError(backlog.problem.message, code=backlog.problem.code)
        found = [i for i in backlog.items if i.id == item_id]
        if not found:
            raise ItemNotFoundError(item_id)
        if len(found) > 1:
            raise DuplicateItemError(item_id)
        return found[0]

    def archive_available(self, source: Source) -> bool:
        return self._layouts.for_source(source).archive_available()

    def _format_problem(self, layout: BacklogLayout) -> SourceProblem | None:
        if self._detector.is_backlog(self._files.read(layout.file(Location.ACTIVE)).text):
            return None
        return SourceProblem("unsupported_format", f"{TODO_FILE} is not in the backlog format.")

    def _parse(self, doc: TextDocument, source: Source, location: Location) -> list[Item]:
        if not self._detector.is_backlog(doc.text):
            return []
        return self._parser.parse(doc.lines, source.project, location)

    # ---------- writing ----------

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        """Applies a ChangeSet to the stored entry and returns the item as stored afterwards."""
        layout = self._layouts.for_source(source)
        with self._locks.hold(str(layout.folder)):
            doc = self._files.read(layout.file(item.location))
            stored = next((i for i in self._parse(doc, source, item.location) if i.id == item.id), None)
            if stored is None or stored.version != item.version:
                raise VersionConflictError(item.id)
            idx = self._locator.locate(doc.lines, item.id)

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
            raise ItemNotFoundError(item_id)
        return found

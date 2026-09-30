"""Backlog repository backed by TODO.md / archive.md files."""
from __future__ import annotations

from collections.abc import Sequence

import structlog

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet, Field, FieldValue
from todo_viewer.domain.errors import (
    BacklogExistsError,
    DuplicateItemError,
    InvalidSourceError,
    ItemNotFoundError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SourceProblem

from .detector import FormatDetector
from .document_paths import path_of
from .editors import BacklogEntryEditor, EntryLocator, EntryMover, EntryRenderer
from .layout import BacklogLayout, LayoutFactory
from .parsers import BacklogParser
from .syntax import TODO_FILE
from .templates import EmptyBacklogTemplates
from .text_file import KeyedLocks, TextDocument, TextFileStore

log = structlog.get_logger(__name__)


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
        renderer: EntryRenderer,
        templates: EmptyBacklogTemplates,
        locks: KeyedLocks,
    ):
        self._layouts = layouts
        self._files = files
        self._detector = detector
        self._parser = parser
        self._locator = locator
        self._entry_editor = entry_editor
        self._mover = mover
        self._renderer = renderer
        self._templates = templates
        self._locks = locks

    # ---------- reading ----------

    def check(self, source: Source) -> SourceProblem | None:
        if not source.path.strip():
            return SourceProblem("missing_path", "Path is missing.")
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
                log.warning("backlog_unparsable", source=source.id, path=str(path),
                            error=f"{type(exc).__name__}: {exc}")
                log.debug("backlog_unparsable_trace", path=str(path), exc_info=exc)
        return backlog

    def get(self, source: Source, item_id: str) -> Item:
        return self.load(source).find(item_id)

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
        return self.apply_all(source, [(item, changes)])[0]

    def apply_all(self, source: Source, plan: Sequence[tuple[Item, ChangeSet]]) -> list[Item]:
        """Applies several ChangeSets in one go under one lock; each item must still be at its version."""
        layout = self._layouts.for_source(source)
        with self._locks.hold(str(layout.folder)):
            docs = {loc: self._files.read(layout.file(loc)) for loc in Location if layout.file(loc).is_file()}
            for item, _ in plan:
                self._check_version(docs[item.location], source, item)
            touched: list[Location] = []
            for item, changes in plan:
                doc = docs[item.location]
                idx = self._locator.locate(doc.lines, item.id)
                for key, value in self._file_fields(item, changes):
                    self._entry_editor.set_field(doc.lines, idx, key, value)
                for key in changes.remove_fields:
                    self._entry_editor.remove_field(doc.lines, idx, key)
                touched.append(item.location)
                if changes.move_to is not None and changes.move_to is not item.location:
                    self._mover.append(docs[changes.move_to].lines, self._mover.cut(doc.lines, idx))
                    touched.append(changes.move_to)
            # Write destinations before sources so a moved entry is never lost.
            order = [loc for loc in (Location.ARCHIVE, Location.ACTIVE) if loc in touched]
            if len(order) > 1:
                for loc in order:
                    self._files.ensure_unchanged(docs[loc])
            moved_to_archive = any(c.move_to is Location.ARCHIVE for _, c in plan)
            for loc in order if moved_to_archive else reversed(order):
                self._files.write(docs[loc])
            return [self._reload(source, layout, str(dict(changes.set_fields).get("id", item.id)),
                                 changes.move_to or item.location)
                    for item, changes in plan]

    @staticmethod
    def _file_fields(item: Item, changes: ChangeSet) -> list[tuple[str, FieldValue]]:
        """The changes as written into the file: documents are listed by path, which contains the item's id."""
        fields = dict(changes.set_fields)
        item_id = str(fields.get(Field.ID, item.id))
        result = list(changes.set_fields)
        if item_id != item.id:  # the paths move with the id even where the names stay
            for key, names in ((Field.NOTES, item.notes), (Field.SPEC, item.spec)):
                if key not in fields and names:
                    result.append((key, tuple(names)))
        return [(key, tuple(path_of(item_id, str(n)) for n in value or ()) if key in (Field.NOTES, Field.SPEC)
                 else value) for key, value in result]

    def delete(self, source: Source, items: Sequence[Item]) -> None:
        """Removes the entries (each still at its version) in one go."""
        layout = self._layouts.for_source(source)
        with self._locks.hold(str(layout.folder)):
            docs = {loc: self._files.read(layout.file(loc)) for loc in {i.location for i in items}}
            for item in items:
                self._check_version(docs[item.location], source, item)
            for item in items:
                doc = docs[item.location]
                self._mover.cut(doc.lines, self._locator.locate(doc.lines, item.id))
            for doc in docs.values():
                self._files.write(doc)

    def create(self, source: Source, item: Item) -> Item:
        """Adds a new active entry; raises DuplicateItemError if its id was taken in the meantime."""
        layout = self._layouts.for_source(source)
        with self._locks.hold(str(layout.folder)):
            if any(i.id == item.id for i in self.load(source).items):
                raise DuplicateItemError(item.id)
            doc = self._files.read(layout.file(Location.ACTIVE))
            self._mover.insert(doc.lines, self._renderer.render(item))
            self._files.write(doc)
            return self._reload(source, layout, item.id, Location.ACTIVE)

    def initialize(self, source: Source, language: str) -> None:
        """Creates TODO.md, archive.md (unless present) and items/ in a new or existing folder."""
        layout = self._layouts.for_source(source)
        texts = self._templates.for_language(language)
        if layout.folder.exists() and not layout.folder.is_dir():
            raise InvalidSourceError("Path is not a folder.", code="not_a_dir")
        with self._locks.hold(str(layout.folder)):
            if layout.file(Location.ACTIVE).exists():
                raise BacklogExistsError()
            for location in (Location.ARCHIVE, Location.ACTIVE):  # TODO.md last: it marks the backlog as complete
                if not layout.file(location).exists():
                    self._files.create(layout.file(location), texts[location])
            layout.items_folder().mkdir(exist_ok=True)

    def _check_version(self, doc: TextDocument, source: Source, item: Item) -> None:
        stored = next((i for i in self._parse(doc, source, item.location) if i.id == item.id), None)
        if stored is None or stored.version != item.version:
            raise VersionConflictError(item.id)

    def _reload(self, source: Source, layout: BacklogLayout, item_id: str, location: Location) -> Item:
        items = self._parse(self._files.read(layout.file(location)), source, location)
        found = next((i for i in items if i.id == item_id), None)
        if found is None:
            raise ItemNotFoundError(item_id)
        return found

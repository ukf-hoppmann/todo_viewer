from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.creation import ItemFactory
from todo_viewer.domain.editing import EditPlanner, Field
from todo_viewer.domain.errors import NotEditableError, VersionConflictError
from todo_viewer.domain.item import Item
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, DocumentStore, SourceRepository


@dataclass(frozen=True)
class SourceBacklog:
    index: int
    source: Source
    backlog: Backlog


class BacklogOverviewService:
    """All configured backlogs with their items; broken sources are reported, not raised."""

    def __init__(self, sources: SourceRepository, backlogs: BacklogRepository):
        self._sources = sources
        self._backlogs = backlogs

    def overview(self, only: Source | None = None) -> list[SourceBacklog]:
        """All sources, or just `only`."""
        return [SourceBacklog(index, source, self._backlogs.load(source))
                for index, source in enumerate(self._sources.all()) if only is None or source == only]


@dataclass(frozen=True)
class ItemResult:
    item: Item
    archive_supported: bool


class ItemService:
    """Reads and edits single items addressed by id, following the domain's archive and lifecycle rules."""

    def __init__(self, backlogs: BacklogRepository, documents: DocumentStore, planner: EditPlanner,
                 rules: LifecycleRules, factory: ItemFactory, today: Callable[[], date] = date.today):
        self._backlogs = backlogs
        self._documents = documents
        self._planner = planner
        self._rules = rules
        self._factory = factory
        self._today = today

    def get(self, source: Source, item_id: str) -> ItemResult:
        item = self._backlogs.get(source, item_id)
        return ItemResult(item, self._backlogs.archive_available(source))

    def create(self, source: Source, item_type: str, fields: Mapping[str, object]) -> ItemResult:
        """A new Open item with the next free id of its type, checked against the lifecycle rules."""
        backlog = self._backlogs.load(source)
        backlog.require_usable()
        item = self._factory.create(item_type, fields, backlog.items, source.project, self._today().isoformat())
        self._rules.check_change(backlog.items, [*backlog.items, item])
        return ItemResult(self._backlogs.create(source, item), backlog.archive_available)

    def delete(self, source: Source, item_id: str, version: str) -> ItemResult:
        """Deletes the item and its `items/<ID>/` folder; refused while other items refer to it."""
        backlog = self._backlogs.load(source)
        item = backlog.find(item_id)
        if item.version != version:
            raise VersionConflictError(item_id)
        self._rules.check_delete(backlog.items, item_id)
        self._backlogs.delete(source, item)
        self._documents.delete_item_folder(source, item_id)
        return ItemResult(item, backlog.archive_available)

    def edit(self, source: Source, item_id: str, version: str, changes: Mapping[str, object],
             resolution: str | None) -> ItemResult:
        """Applies all field changes at once, so e.g. parent and required_for_parent can change together."""
        for field in changes:
            if field not in Field.EDITABLE:
                raise NotEditableError(field)
        backlog = self._backlogs.load(source)
        item = backlog.find(item_id)
        if item.version != version:
            raise VersionConflictError(item_id)
        change_set = self._planner.plan(item, changes, resolution, backlog.archive_available)
        after = change_set.applied_to(item)
        self._rules.check_change(backlog.items, [after if i is item else i for i in backlog.items])
        return ItemResult(self._backlogs.apply(source, item, change_set), backlog.archive_available)

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.creation import ItemFactory
from todo_viewer.domain.editing import EditPlanner, Field
from todo_viewer.domain.errors import LifecycleViolationError, NotEditableError, VersionConflictError
from todo_viewer.domain.item import Item
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.source import Source
from todo_viewer.domain.trash import live

from ..ports import BacklogRepository, ItemStatusListener, SourceRepository


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

    def __init__(self, backlogs: BacklogRepository, planner: EditPlanner, rules: LifecycleRules,
                 factory: ItemFactory, today: Callable[[], date] = date.today,
                 listener: ItemStatusListener | None = None):
        self._listener = listener
        self._backlogs = backlogs
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
        self._rules.check_change(live(backlog.items), [*live(backlog.items), item])
        return ItemResult(self._backlogs.create(source, item), backlog.archive_available)

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
        if item.deleted:
            raise LifecycleViolationError("item_deleted", item_id)
        change_set = self._planner.plan(item, changes, resolution, backlog.archive_available)
        after = change_set.applied_to(item)
        in_use = live(backlog.items)
        self._rules.check_change(in_use, [after if i is item else i for i in in_use])
        stored = self._backlogs.apply(source, item, change_set)
        if self._listener is not None and after.status != item.status:
            self._listener.item_status_changed(source.project, after.id, after.status)
        return ItemResult(stored, backlog.archive_available)

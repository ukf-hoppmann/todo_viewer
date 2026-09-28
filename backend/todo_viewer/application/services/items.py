from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import EditPlanner, Field
from todo_viewer.domain.errors import NotEditableError, VersionConflictError
from todo_viewer.domain.item import Item
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.source import Source

from ..ports import BacklogRepository, SourceRepository


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

    def __init__(self, backlogs: BacklogRepository, planner: EditPlanner, rules: LifecycleRules):
        self._backlogs = backlogs
        self._planner = planner
        self._rules = rules

    def get(self, source: Source, item_id: str) -> ItemResult:
        item = self._backlogs.get(source, item_id)
        return ItemResult(item, self._backlogs.archive_available(source))

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

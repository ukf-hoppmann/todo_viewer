from __future__ import annotations

from dataclasses import dataclass

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import EditPlanner, Field
from todo_viewer.domain.errors import NotEditableError, VersionConflictError
from todo_viewer.domain.item import Item
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

    def overview(self) -> list[SourceBacklog]:
        return [SourceBacklog(index, source, self._backlogs.load(source))
                for index, source in enumerate(self._sources.all())]


@dataclass(frozen=True)
class ItemResult:
    item: Item
    archive_supported: bool


class ItemService:
    """Reads and edits single items addressed by id, following the domain's archive rules."""

    def __init__(self, backlogs: BacklogRepository, planner: EditPlanner):
        self._backlogs = backlogs
        self._planner = planner

    def get(self, source: Source, item_id: str) -> ItemResult:
        item = self._backlogs.get(source, item_id)
        return ItemResult(item, self._backlogs.archive_available(source))

    def edit(self, source: Source, item_id: str, version: str, field: str, value: str,
             resolution: str | None) -> ItemResult:
        if field not in Field.EDITABLE:
            raise NotEditableError(field)
        item = self._backlogs.get(source, item_id)
        if item.version != version:
            raise VersionConflictError(item_id)
        archive = self._backlogs.archive_available(source)
        changes = self._planner.plan(item, field, value, resolution, archive)
        return ItemResult(self._backlogs.apply(source, item, changes), archive)

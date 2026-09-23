from __future__ import annotations

from dataclasses import dataclass

from todo_viewer.domain.backlog import Backlog, supports_archive
from todo_viewer.domain.editing import EditPlanner, Field
from todo_viewer.domain.errors import NotEditableError
from todo_viewer.domain.item import Item, ItemRef
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
class EditResult:
    item: Item
    archive_supported: bool


class ItemEditService:
    """Edits one field of an item, following the domain's archive rules."""

    def __init__(self, backlogs: BacklogRepository, planner: EditPlanner):
        self._backlogs = backlogs
        self._planner = planner

    def edit(self, source: Source, ref: ItemRef, field: str, value: str, resolution: str | None) -> EditResult:
        if field not in Field.EDITABLE:
            raise NotEditableError(field)
        item = self._backlogs.find(source, ref)
        archive = self._backlogs.archive_available(source)
        changes = self._planner.plan(item, field, value, resolution, supports_archive(item, archive))
        updated = self._backlogs.apply(source, item, changes)
        return EditResult(updated, supports_archive(updated, archive))

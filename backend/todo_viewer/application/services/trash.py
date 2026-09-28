from __future__ import annotations

from collections.abc import Callable
from datetime import date

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.errors import VersionConflictError
from todo_viewer.domain.item import Item
from todo_viewer.domain.source import Source
from todo_viewer.domain.trash import TrashPlanner

from ..ports import BacklogRepository, DocumentStore
from .items import ItemResult


class TrashService:
    """Deleting moves items to the trash; from there they are restored or purged, with their descendants."""

    def __init__(self, backlogs: BacklogRepository, documents: DocumentStore, planner: TrashPlanner,
                 today: Callable[[], date] = date.today):
        self._backlogs = backlogs
        self._documents = documents
        self._planner = planner
        self._today = today

    def in_trash(self, source: Source) -> list[ItemResult]:
        backlog = self._backlogs.load(source)
        backlog.require_usable()
        return [ItemResult(i, backlog.archive_available) for i in backlog.items if i.deleted]

    def delete(self, source: Source, item_id: str, version: str, cascade: bool) -> list[ItemResult]:
        backlog = self._backlog(source, item_id, version)
        plan = self._planner.delete(backlog.items, item_id, cascade, self._today().isoformat(),
                                    backlog.archive_available)
        return self._results(self._backlogs.apply_all(source, plan), backlog)

    def restore(self, source: Source, item_id: str, version: str) -> list[ItemResult]:
        backlog = self._backlog(source, item_id, version)
        plan = self._planner.restore(backlog.items, item_id)
        return self._results(self._backlogs.apply_all(source, plan), backlog)

    def purge(self, source: Source, item_id: str, version: str) -> list[ItemResult]:
        """Removes the items and their `items/<ID>/` folders for good."""
        backlog = self._backlog(source, item_id, version)
        targets = self._planner.purge(backlog.items, item_id)
        self._backlogs.delete(source, targets)
        for target in targets:
            self._documents.delete_item_folder(source, target.id)
        return self._results(targets, backlog)

    def _backlog(self, source: Source, item_id: str, version: str) -> Backlog:
        backlog = self._backlogs.load(source)
        if backlog.find(item_id).version != version:
            raise VersionConflictError(item_id)
        return backlog

    @staticmethod
    def _results(items: list[Item], backlog: Backlog) -> list[ItemResult]:
        return [ItemResult(i, backlog.archive_available) for i in items]

"""The trash: deleting marks items (and, on confirmation, their descendants) instead of removing them.

Items in the trash do not take part in the lifecycle rules; they can be restored or purged, both
together with their descendants.
"""
from __future__ import annotations

from collections.abc import Sequence

from .backlog import Backlog
from .editing import ChangeSet, Field
from .errors import LifecycleViolationError
from .item import Item, Location, Status
from .lifecycle import LifecycleRules


def live(items: Sequence[Item]) -> list[Item]:
    """The items in use, i.e. not in the trash."""
    return [i for i in items if not i.deleted]


def descendants(items: Sequence[Item], item_id: str) -> list[Item]:
    """Children, grandchildren, ... of an item in backlog order."""
    found: list[Item] = []
    parents = {item_id}
    while True:
        new = [i for i in items if i.parent in parents and i not in found]
        if not new:
            return [i for i in items if i in found]
        found += new
        parents = {i.id for i in new}


class TrashPlanner:
    def __init__(self, rules: LifecycleRules):
        self._rules = rules

    def delete(self, items: Sequence[Item], item_id: str, cascade: bool, today: str,
               archive_available: bool = True) -> list[tuple[Item, ChangeSet]]:
        """Moves the item to the trash; its descendants only with `cascade` (a warning otherwise).

        Trashed entries go to the archive; without one they stay in place, marked as deleted.
        """
        in_use = live(items)
        item = self._get(items, item_id)
        if item.deleted:
            raise LifecycleViolationError("item_deleted", item_id)
        children = descendants(in_use, item_id)
        if children and not cascade:
            raise LifecycleViolationError("has_children", item_id, _ids(children))
        targets = [item, *children]
        self._refuse_referrers(in_use, targets, item_id)
        gone = {t.id for t in targets}
        self._rules.check_change(in_use, [i for i in in_use if i.id not in gone])
        return [(t, ChangeSet(set_fields=((Field.DELETED, today),),
                              move_to=Location.ARCHIVE if archive_available and t.location is Location.ACTIVE
                              else None))
                for t in targets]

    def restore(self, items: Sequence[Item], item_id: str) -> list[tuple[Item, ChangeSet]]:
        """Takes the item and its descendants out of the trash; open items go back to the active list."""
        item = self._in_trash(items, item_id)
        parent = next((i for i in items if i.id == item.parent), None)
        if parent is not None and parent.deleted:
            raise LifecycleViolationError("parent_deleted", item_id, (parent.id,))
        targets = [item, *(d for d in descendants(items, item_id) if d.deleted)]
        plan = [(t, ChangeSet(remove_fields=(Field.DELETED,),
                              move_to=Location.ACTIVE
                              if t.location is Location.ARCHIVE and not Status.is_terminal(t.status) else None))
                for t in targets]
        restored = [c.applied_to(t) for t, c in plan]
        self._rules.check_change(live(items), [*live(items), *restored], returning=restored)
        return plan

    def purge(self, items: Sequence[Item], item_id: str) -> list[Item]:
        """The items to remove for good: the item and its descendants, if nothing else refers to them."""
        item = self._in_trash(items, item_id)
        targets = [item, *descendants(items, item_id)]
        self._refuse_referrers(items, targets, item_id)
        return targets

    @staticmethod
    def _get(items: Sequence[Item], item_id: str) -> Item:
        return Backlog(items=list(items)).find(item_id)  # same lookup rules as everywhere else

    def _in_trash(self, items: Sequence[Item], item_id: str) -> Item:
        item = self._get(items, item_id)
        if not item.deleted:
            raise LifecycleViolationError("item_not_deleted", item_id)
        return item

    @staticmethod
    def _refuse_referrers(items: Sequence[Item], targets: Sequence[Item], item_id: str) -> None:
        gone = {t.id for t in targets}
        referrers = [i for i in items if i.id not in gone
                     and ((i.parent in gone) or gone.intersection(i.dependencies))]
        if referrers:
            raise LifecycleViolationError("item_referenced", item_id, _ids(referrers))


def _ids(items: Sequence[Item]) -> tuple[str, ...]:
    return tuple(i.id for i in items)

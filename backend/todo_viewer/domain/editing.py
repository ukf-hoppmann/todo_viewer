"""Editing rules: turns an edit request into a storage-independent ChangeSet."""
from __future__ import annotations

from dataclasses import dataclass

from .errors import CheckboxStatusOnlyError, NotEditableError, ResolutionRequiredError
from .item import Item, ItemFormat, Location, Status


class Field:
    STATUS = "status"
    PRIORITY = "priority"
    RESOLUTION = "resolution"

    EDITABLE = frozenset({STATUS, PRIORITY})


@dataclass(frozen=True)
class ChangeSet:
    """What has to happen to one item. Field changes are applied in order."""

    set_fields: tuple[tuple[str, str], ...] = ()
    remove_fields: tuple[str, ...] = ()
    move_to: Location | None = None


class EditPlanner:
    """Applies the backlog rules (e.g. Completed/Rejected → resolution + archive)."""

    def plan(self, item: Item, field: str, value: str, resolution: str | None, archive_supported: bool) -> ChangeSet:
        if field not in Field.EDITABLE:
            raise NotEditableError(field)
        if item.format is ItemFormat.CHECKBOX:
            if field != Field.STATUS:
                raise CheckboxStatusOnlyError()
            return ChangeSet(set_fields=((field, value),))

        if field != Field.STATUS or not archive_supported:
            return ChangeSet(set_fields=((field, value),))

        if Status.is_terminal(value):
            if not (resolution or "").strip():
                raise ResolutionRequiredError()
            move = Location.ARCHIVE if item.location is Location.ACTIVE else None
            return ChangeSet(set_fields=((field, value), (Field.RESOLUTION, resolution or "")), move_to=move)

        move = Location.ACTIVE if item.location is Location.ARCHIVE else None
        return ChangeSet(set_fields=((field, value),), remove_fields=(Field.RESOLUTION,), move_to=move)

"""Editing rules: turns an edit request into a storage-independent ChangeSet."""
from __future__ import annotations

from dataclasses import dataclass

from .errors import InvalidValueError, NotEditableError, ResolutionRequiredError
from .item import Item, Location, Status


class Field:
    STATUS = "status"
    PRIORITY = "priority"
    REQUIRED_FOR_PARENT = "required_for_parent"
    RESOLUTION = "resolution"

    EDITABLE = frozenset({STATUS, PRIORITY, REQUIRED_FOR_PARENT})
    # Fields with a fixed set of values, spelled as in the file.
    ALLOWED_VALUES = {REQUIRED_FOR_PARENT: ("Yes", "No")}


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
        allowed = Field.ALLOWED_VALUES.get(field)
        if allowed is not None and value not in allowed:
            raise InvalidValueError(field, allowed)

        if field != Field.STATUS or not archive_supported:
            return ChangeSet(set_fields=((field, value),))

        if Status.is_terminal(value):
            if not (resolution or "").strip():
                raise ResolutionRequiredError()
            move = Location.ARCHIVE if item.location is Location.ACTIVE else None
            return ChangeSet(set_fields=((field, value), (Field.RESOLUTION, resolution or "")), move_to=move)

        move = Location.ACTIVE if item.location is Location.ARCHIVE else None
        return ChangeSet(set_fields=((field, value),), remove_fields=(Field.RESOLUTION,), move_to=move)

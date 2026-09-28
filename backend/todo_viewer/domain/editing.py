"""Editing rules: turns an edit request into a storage-independent ChangeSet."""
from __future__ import annotations

import dataclasses
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

    def applied_to(self, item: Item) -> Item:
        """The item as it will be stored afterwards, for rule checks before anything is written."""
        values: dict[str, object] = {}
        for key, value in self.set_fields:
            values[key] = (value == "Yes") if key == Field.REQUIRED_FOR_PARENT else value
        for key in self.remove_fields:
            values[key] = None
        if self.move_to is not None:
            values["location"] = self.move_to
        return dataclasses.replace(item, **values)  # type: ignore[arg-type]


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

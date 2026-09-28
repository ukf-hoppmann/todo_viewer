"""Editing rules: turns an edit request into a storage-independent ChangeSet."""
from __future__ import annotations

import dataclasses
import re
from collections.abc import Mapping
from dataclasses import dataclass

from .errors import InvalidValueError, NotEditableError, ResolutionRequiredError, ValueRequiredError
from .item import Item, Location, Status

# A value in a ChangeSet: text, a list of ids (dependencies), or None (e.g. no parent).
FieldValue = str | tuple[str, ...] | None

ID_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


class Field:
    TITLE = "title"
    STATUS = "status"
    PRIORITY = "priority"
    REQUIRED_FOR_PARENT = "required_for_parent"
    RESOLUTION = "resolution"
    GOAL = "goal"
    COMPLETION_CRITERIA = "completion_criteria"
    SUMMARY = "summary"
    AREA = "area"
    PARENT = "parent"
    DEPENDENCIES = "dependencies"
    # Maintained by the server when documents are written, not editable directly.
    NOTES = "notes"
    SPEC = "spec"

    EDITABLE = frozenset({TITLE, STATUS, PRIORITY, REQUIRED_FOR_PARENT, GOAL, COMPLETION_CRITERIA, SUMMARY, AREA,
                          PARENT, DEPENDENCIES})
    # Free text stored on one logical line; these must not become empty.
    REQUIRED_TEXT = frozenset({TITLE, PRIORITY, GOAL, COMPLETION_CRITERIA, AREA})
    OPTIONAL_TEXT = frozenset({SUMMARY})
    # Fields with a fixed set of values, spelled as in the file.
    ALLOWED_VALUES = {REQUIRED_FOR_PARENT: ("Yes", "No")}


@dataclass(frozen=True)
class ChangeSet:
    """What has to happen to one item. Field changes are applied in order."""

    set_fields: tuple[tuple[str, FieldValue], ...] = ()
    remove_fields: tuple[str, ...] = ()
    move_to: Location | None = None

    def applied_to(self, item: Item) -> Item:
        """The item as it will be stored afterwards, for rule checks before anything is written."""
        values: dict[str, object] = {}
        for key, value in self.set_fields:
            if key == Field.REQUIRED_FOR_PARENT:
                values[key] = value == "Yes"
            elif key in (Field.DEPENDENCIES, Field.NOTES, Field.SPEC):
                values[key] = list(value or ())
            else:
                values[key] = value
        for key in self.remove_fields:
            values[key] = None
        if self.move_to is not None:
            values["location"] = self.move_to
        return dataclasses.replace(item, **values)  # type: ignore[arg-type]


class EditPlanner:
    """Applies the backlog rules (e.g. Completed/Rejected → resolution + archive) to a set of field changes."""

    def plan(self, item: Item, changes: Mapping[str, object], resolution: str | None,
             archive_supported: bool) -> ChangeSet:
        if not changes:
            raise NotEditableError("(none)")
        for field in changes:
            if field not in Field.EDITABLE:
                raise NotEditableError(field)

        set_fields: list[tuple[str, FieldValue]] = []
        remove_fields: list[str] = []
        move_to: Location | None = None
        for field, raw in changes.items():
            if field == Field.STATUS:
                continue  # handled last: it may add a resolution and move the entry
            value = self.normalize(field, raw)
            if value is None and field in Field.OPTIONAL_TEXT:
                remove_fields.append(field)
                continue
            set_fields.append((field, value))
            if field == Field.PARENT and value is None:
                remove_fields.append(Field.REQUIRED_FOR_PARENT)

        if Field.STATUS in changes:
            status = self._text(Field.STATUS, changes[Field.STATUS], required=True)
            set_fields.append((Field.STATUS, status))
            if archive_supported:
                if Status.is_terminal(status or ""):
                    if not (resolution or "").strip():
                        raise ResolutionRequiredError()
                    set_fields.append((Field.RESOLUTION, resolution or ""))
                    move_to = Location.ARCHIVE if item.location is Location.ACTIVE else None
                else:
                    remove_fields.append(Field.RESOLUTION)
                    move_to = Location.ACTIVE if item.location is Location.ARCHIVE else None

        return ChangeSet(set_fields=tuple(set_fields), remove_fields=tuple(remove_fields), move_to=move_to)

    def normalize(self, field: str, raw: object) -> FieldValue:
        """Validates one field value and brings it into its stored form (None = no value)."""
        if field == Field.PARENT:
            return None if raw is None else self._id(field, raw)
        if field == Field.DEPENDENCIES:
            if not isinstance(raw, list | tuple):
                raise InvalidValueError(field, ("list of ids",))
            return tuple(dict.fromkeys(self._id(field, v) for v in raw))
        allowed = Field.ALLOWED_VALUES.get(field)
        if allowed is not None and raw not in allowed:
            raise InvalidValueError(field, allowed)
        value = self._text(field, raw, required=field in Field.REQUIRED_TEXT)
        if field == Field.TITLE and value is not None and "**" in value:
            raise InvalidValueError(field, ("text without '**'",))
        return value

    @staticmethod
    def _text(field: str, raw: object, required: bool) -> str | None:
        """Trims and joins whitespace (the format stores text as one logical line); '' means no value."""
        value = " ".join(str(raw).split()) if raw is not None else ""
        if value:
            return value
        if required:
            raise ValueRequiredError(field)
        return None

    @staticmethod
    def _id(field: str, raw: object) -> str:
        value = str(raw).strip()
        if not ID_RE.match(value):
            raise InvalidValueError(field, ("item ids",))
        return value

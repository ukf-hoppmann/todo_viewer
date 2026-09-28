"""Creating items: next free id per type and the defaults of a new entry."""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .editing import EditPlanner, Field
from .errors import InvalidValueError, NotEditableError
from .item import Item, Status

TYPES = ("Epic", "Story", "Task")
DEFAULT_PRIORITY = "Normal"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Fields a new item may set; status is always Open and the id is assigned.
CREATABLE = frozenset({Field.TITLE, Field.PRIORITY, Field.REQUIRED_FOR_PARENT, Field.GOAL,
                       Field.COMPLETION_CRITERIA, Field.SUMMARY, Field.AREA, Field.PARENT, Field.DEPENDENCIES,
                       "created"})
REQUIRED = (Field.TITLE, Field.AREA, Field.GOAL, Field.COMPLETION_CRITERIA)


class ItemFactory:
    def __init__(self, planner: EditPlanner | None = None):
        self._planner = planner or EditPlanner()

    def create(self, item_type: str, fields: Mapping[str, object], existing: Sequence[Item], project: str,
               today: str) -> Item:
        if item_type not in TYPES:
            raise InvalidValueError("type", TYPES)
        for name in fields:
            if name not in CREATABLE:
                raise NotEditableError(name)

        values = {name: self._planner.normalize(name, fields[name]) for name in fields if name != "created"}
        for name in REQUIRED:
            values[name] = self._planner.normalize(name, fields.get(name))
        created = str(fields.get("created") or today).strip()
        if not DATE_RE.match(created):
            raise InvalidValueError("created", ("YYYY-MM-DD",))

        required = values.get(Field.REQUIRED_FOR_PARENT)
        return Item(
            id=self.next_id(item_type, existing),
            title=str(values[Field.TITLE]),
            project=project,
            item_type=item_type,
            status=Status.OPEN,
            parent=_text(values.get(Field.PARENT)),
            required_for_parent=None if required is None else required == "Yes",
            dependencies=list(values.get(Field.DEPENDENCIES) or ()),
            created=created,
            area=_text(values[Field.AREA]),
            priority=_text(values.get(Field.PRIORITY)) or DEFAULT_PRIORITY,
            goal=_text(values[Field.GOAL]),
            completion_criteria=_text(values[Field.COMPLETION_CRITERIA]),
            summary=_text(values.get(Field.SUMMARY)),
        )

    @staticmethod
    def next_id(item_type: str, existing: Sequence[Item]) -> str:
        """`PREFIX-NNN` with the next number of the type; ids are counted over active and archived items."""
        prefix = item_type.upper()
        pattern = re.compile(rf"^{prefix}-(\d+)$")
        numbers = [int(m.group(1)) for i in existing if (m := pattern.match(i.id))]
        return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None

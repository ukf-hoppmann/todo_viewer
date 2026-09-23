"""Maps raw `  - Key: value` fields of a backlog entry onto an Item."""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping

from todo_viewer.domain.item import Item

from .syntax import field_key

BACKTICK_ID_RE = re.compile(r"`([A-Za-z0-9_.\-]+)`")
BACKTICK_ANY_RE = re.compile(r"`([^`]+)`")

# Older backlogs used German priority names; the keys are English now.
LEGACY_PRIORITIES = {"dringend": "Urgent", "wichtig": "Important", "perspektivisch": "Prospective"}


def clean(value: str) -> str:
    """Strips the trailing period every field value carries in the format."""
    value = value.strip()
    return value[:-1].rstrip() if value.endswith(".") else value


def extract_ids(value: str) -> list[str]:
    return BACKTICK_ID_RE.findall(value)


def extract_paths(value: str) -> list[str]:
    paths = BACKTICK_ANY_RE.findall(value)
    if paths:
        return paths
    return [p.strip() for p in clean(value).split(",") if p.strip() and p.strip() != "None"]


def yes_no(value: str) -> bool | None:
    v = clean(value).lower()
    if v == "yes":
        return True
    if v == "no":
        return False
    return None


class PriorityNormalizer:
    def __init__(self, legacy: Mapping[str, str] = LEGACY_PRIORITIES):
        self._legacy = {k.lower(): v for k, v in legacy.items()}

    def normalize(self, value: str | None) -> str | None:
        if not value:
            return value
        return self._legacy.get(value.lower(), value)


class BacklogFieldMapper:
    """Known fields become typed attributes, everything else lands in extra_fields."""

    def __init__(self, priorities: PriorityNormalizer):
        self._priorities = priorities
        self._setters: dict[str, Callable[[Item, str], None]] = {
            "type": lambda item, v: setattr(item, "item_type", clean(v)),
            "status": lambda item, v: setattr(item, "status", clean(v)),
            "parent": lambda item, v: setattr(item, "parent", next(iter(extract_ids(v)), None)),
            "required_for_parent": lambda item, v: setattr(item, "required_for_parent", yes_no(v)),
            "dependencies": lambda item, v: setattr(item, "dependencies", extract_ids(v)),
            "created": lambda item, v: setattr(item, "created", clean(v)),
            "area": lambda item, v: setattr(item, "area", clean(v)),
            "priority": lambda item, v: setattr(item, "priority", self._priorities.normalize(clean(v))),
            "goal": lambda item, v: setattr(item, "goal", v.strip()),
            "completion_criteria": lambda item, v: setattr(item, "completion_criteria", v.strip()),
            "summary": lambda item, v: setattr(item, "summary", v.strip()),
            "resolution": lambda item, v: setattr(item, "resolution", v.strip()),
            "notes": lambda item, v: setattr(item, "notes", extract_paths(v)),
            "spec": lambda item, v: setattr(item, "spec", extract_paths(v)),
        }

    def apply(self, item: Item, fields: list[tuple[str, str]]) -> None:
        for label, value in fields:
            setter = self._setters.get(field_key(label))
            if setter is None:
                item.extra_fields[label.strip()] = value.strip()
            else:
                setter(item, value)

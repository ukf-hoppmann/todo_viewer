"""Work items as the domain sees them, independent of how they are stored."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ItemFormat(StrEnum):
    BACKLOG_V2 = "backlog_v2"
    CHECKBOX = "checkbox"


class Location(StrEnum):
    """Where an item lives inside its backlog."""

    ACTIVE = "active"
    ARCHIVE = "archive"


class Status:
    """Status values as written in the files. Unknown values are kept as-is."""

    OPEN = "Open"
    IN_PROGRESS = "In progress"
    AWAITING_CONFIRMATION = "Awaiting confirmation"
    COMPLETED = "Completed"
    REJECTED = "Rejected"

    TERMINAL = frozenset({COMPLETED, REJECTED})

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        return status in cls.TERMINAL


@dataclass
class Item:
    id: str
    title: str
    source_file: str
    project: str
    line: int
    format: ItemFormat = ItemFormat.BACKLOG_V2
    item_type: str = "Task"
    status: str = Status.OPEN
    parent: str | None = None
    required_for_parent: bool | None = None
    dependencies: list[str] = field(default_factory=list)
    created: str | None = None
    area: str | None = None
    priority: str | None = None
    goal: str | None = None
    completion_criteria: str | None = None
    summary: str | None = None
    resolution: str | None = None
    notes: list[str] = field(default_factory=list)
    spec: list[str] = field(default_factory=list)
    extra_fields: dict[str, str] = field(default_factory=dict)
    location: Location = Location.ACTIVE

"""Work items as the domain sees them, independent of how they are stored."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum


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
    """One work item. Within a backlog it is identified by its id alone."""

    id: str
    title: str
    project: str
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

    @property
    def version(self) -> str:
        """Changes whenever the stored item changes; guards edits against lost updates.

        `project` is left out: it is the source's display name, not part of the item.
        """
        stored = {k: v for k, v in asdict(self).items() if k != "project"}
        data = json.dumps(stored, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

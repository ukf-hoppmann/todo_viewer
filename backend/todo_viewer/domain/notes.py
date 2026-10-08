"""Topics, notes, links, and triggers: things worth remembering that are not work items (yet).

Everything here is addressed by project plus label (`NOTE-001`, `TOPIC-001`); labels count per project and type,
are never reused, and never change inside a project. Points in time are timezone-aware.
"""
from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from .errors import DocumentForbiddenError, TopicLoopError, TopicNotFoundError, TopicTooDeepError
from .item import Status

DEFAULT_MAX_TOPIC_DEPTH = 3
DEFAULT_REVIEW_DAYS = 30


@dataclass(frozen=True)
class NotesSettings:
    """The global options `notes.max_topic_depth` and `notes.review_days`."""

    max_topic_depth: int = DEFAULT_MAX_TOPIC_DEPTH
    review_days: int = DEFAULT_REVIEW_DAYS


class NoteStatus(StrEnum):
    WAITING = "waiting"
    DUE = "due"
    SNOOZED = "snoozed"
    DONE = "done"
    DROPPED = "dropped"
    PROMOTED = "promoted"


class TriggerMode(StrEnum):
    """Whether one arrived trigger is enough to make the note due, or all of them are needed."""

    ANY = "any"
    ALL = "all"


class TargetKind(StrEnum):
    ITEM = "item"
    TOPIC = "topic"
    NOTE = "note"


class LinkRole(StrEnum):
    REFERENCE = "reference"
    TRIGGER = "trigger"
    ORIGIN = "origin"


class TriggerKind(StrEnum):
    TIME = "time"
    EVENT = "event"
    TOPIC_DUE = "topic_due"


# The statuses an item can reach that make an event trigger arrive.
EVENT_STATUSES = (Status.IN_PROGRESS, Status.AWAITING_CONFIRMATION, Status.COMPLETED, Status.REJECTED)

_LABEL_PREFIX = {"note": "NOTE", "topic": "TOPIC"}


def format_label(kind: str, number: int) -> str:
    return f"{_LABEL_PREFIX[kind]}-{number:03d}"


def utc(moment: datetime) -> datetime:
    """The same moment in UTC; a moment without a time zone is taken as local time of this machine."""
    return moment.astimezone(UTC)


@dataclass(frozen=True)
class Topic:
    project: str
    label: str
    name: str
    parent: str | None = None  # label of the parent topic in the same project
    due_at: datetime | None = None
    created: datetime | None = None
    deleted: datetime | None = None


@dataclass(frozen=True)
class Note:
    project: str
    label: str
    summary: str
    body: str | None = None
    status: NoteStatus = NoteStatus.WAITING
    topic: str | None = None  # label of a topic in the same project
    review_at: datetime | None = None
    trigger_mode: TriggerMode = TriggerMode.ANY
    created: datetime | None = None
    updated: datetime | None = None
    archived: bool = False
    deleted: datetime | None = None

    @property
    def version(self) -> str:
        """Changes whenever a stored field changes; a write based on an older version is refused."""
        parts = (self.summary, self.body, self.status, self.topic, self.review_at, self.trigger_mode, self.archived,
                 self.deleted)
        return hashlib.sha256(repr(parts).encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class NewNote:
    summary: str
    body: str | None = None
    topic: str | None = None
    review_at: datetime | None = None
    trigger_mode: TriggerMode = TriggerMode.ANY


@dataclass(frozen=True)
class NoteChanges:
    """Fields to replace; None keeps the stored value. `clear_*` empties an optional field."""

    summary: str | None = None
    body: str | None = None
    clear_body: bool = False
    status: NoteStatus | None = None
    topic: str | None = None
    clear_topic: bool = False
    review_at: datetime | None = None
    clear_review_at: bool = False
    trigger_mode: TriggerMode | None = None
    archived: bool | None = None


@dataclass(frozen=True)
class LinkTarget:
    kind: TargetKind
    project: str
    label: str


@dataclass(frozen=True)
class Link:
    """From a note to an item, a topic, or another note. Item links hold project plus item label."""

    note: str  # label of the source note
    project: str  # project of the source note
    target: LinkTarget
    role: LinkRole
    id: int = 0  # assigned by the store


@dataclass(frozen=True)
class NewTrigger:
    kind: TriggerKind
    at: datetime | None = None  # time
    target: LinkTarget | None = None  # event: the item to watch
    target_status: str | None = None  # event: the status that makes it arrive
    fired_at: datetime | None = None
    already_met: bool = False  # event: the target had the status when the trigger was created


@dataclass(frozen=True)
class Trigger:
    id: int
    note: str
    kind: TriggerKind
    at: datetime | None = None
    target: LinkTarget | None = None
    target_status: str | None = None
    fired_at: datetime | None = None
    already_met: bool = False
    link_id: int | None = None  # event: the link with role `trigger` that belongs to it


# --- topic tree ---

def topic_depth(parents: Mapping[str, str | None], label: str) -> int:
    """Levels from the root down to `label` (a root topic has depth 1). `parents` maps label -> parent label."""
    depth, seen = 0, set()
    current: str | None = label
    while current is not None:
        if current in seen:
            raise TopicLoopError(label)
        if current not in parents:
            raise TopicNotFoundError(current)
        seen.add(current)
        depth += 1
        current = parents[current]
    return depth


def subtree_height(parents: Mapping[str, str | None], label: str) -> int:
    """Levels of the subtree below `label`, `label` included (a topic without children has height 1)."""
    children: dict[str | None, list[str]] = {}
    for child, parent in parents.items():
        children.setdefault(parent, []).append(child)

    def height(node: str, seen: frozenset[str]) -> int:
        if node in seen:
            raise TopicLoopError(label)
        return 1 + max((height(c, seen | {node}) for c in children.get(node, ())), default=0)

    return height(label, frozenset())


def check_new_topic(parents: Mapping[str, str | None], parent: str | None, max_depth: int, label: str) -> None:
    """A topic below `parent` must not exceed `max_depth`. `label` is only used in the error."""
    if parent is not None and topic_depth(parents, parent) + 1 > max_depth:
        raise TopicTooDeepError(label, max_depth)


def check_topic_move(parents: Mapping[str, str | None], label: str, parent: str | None, max_depth: int) -> None:
    """Moving `label` below `parent` must not make a loop and must keep the whole subtree within `max_depth`."""
    if parent is None:
        return
    node: str | None = parent
    while node is not None:
        if node == label:
            raise TopicLoopError(label)
        node = parents.get(node)
    if topic_depth(parents, parent) + subtree_height(parents, label) > max_depth:
        raise TopicTooDeepError(label, max_depth)


# --- documents of a note ---

def check_note_document_name(label: str, name: str) -> None:
    """Notes: `<LABEL>_notes.md`; specs: `<LABEL>_spec.md` or `<LABEL>_spec_<topic>.md`."""
    if not re.fullmatch(rf"{re.escape(label)}_(notes|spec(_[A-Za-z0-9-]+)?)\.md", name):
        raise DocumentForbiddenError()

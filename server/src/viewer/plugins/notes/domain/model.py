"""Notes und Topics: feste Wertelisten, Datentypen und die reinen Regeln (Fälligkeit, Prüfdatum, Einstellungen)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from viewer.core.domain.errors import DomainError, InvalidInput

#: Alle Status; `due` wird nie gespeichert, sondern aus dem Prüfdatum abgeleitet.
STATUSES = ("waiting", "due", "snoozed", "done", "dropped", "promoted")
STORED_STATUSES = frozenset({"waiting", "snoozed", "done", "dropped", "promoted"})
#: Abgeschlossene Notes liegen im Archiv.
FINISHED_STATUSES = frozenset({"done", "dropped", "promoted"})
TRIGGER_MODES = ("any", "all")

DEFAULT_REVIEW_DAYS = 30
DEFAULT_MAX_TOPIC_DEPTH = 3
MAX_TOPIC_DEPTH_LIMIT = 10
REVIEW_DAYS_LIMIT = 3650

#: Name des neutralen Topics, in das „archivierte Notes behalten“ sie hängt.
ARCHIVE_TOPIC_NAME = "Archiviert"


class NotesViolation(DomainError):
    """Eine Änderung verletzt eine Regel von `notes`; `code` nennt sie, `details` die Beteiligten."""

    def __init__(self, code: str, message: str, **details: object) -> None:
        super().__init__(message, code=code, details=dict(details))


@dataclass(frozen=True)
class Note:
    """Eine Note. `uid`, `label`, `revision` und `deleted_at` gehören dem Register von `workspace`."""

    uid: str
    project_uid: str
    label: str
    summary: str
    body: str | None
    status: str
    topic_uid: str | None
    review_at: datetime | None
    trigger_mode: str
    #: Im Archiv: abgeschlossen oder wegen ihres archivierten Topics.
    archived: bool
    revision: int
    deleted_at: datetime | None = None
    #: Namen der Dokumente (Notizen zuerst).
    documents: tuple[str, ...] = ()

    @property
    def finished(self) -> bool:
        return self.status in FINISHED_STATUSES


@dataclass(frozen=True)
class Topic:
    uid: str
    project_uid: str
    label: str
    name: str
    parent_uid: str | None
    due_at: datetime | None
    archived_at: datetime | None
    #: Das neutrale Topic „Archiviert“ des Projekts: nicht löschbar, nicht umbenennbar.
    system: bool
    revision: int
    deleted_at: datetime | None = None


@dataclass(frozen=True)
class NotesSettings:
    max_topic_depth: int = DEFAULT_MAX_TOPIC_DEPTH
    review_days: int = DEFAULT_REVIEW_DAYS


def utc(moment: datetime) -> datetime:
    """Ein Zeitpunkt ohne Zeitzone gilt als UTC."""
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def default_review_at(now: datetime, review_days: int) -> datetime:
    return utc(now) + timedelta(days=review_days)


def changed_settings(
    current: NotesSettings, max_topic_depth: int | None = None, review_days: int | None = None
) -> NotesSettings:
    """Die Einstellungen mit den genannten Werten; jeder Wert ist eine ganze Zahl von 1 bis zu seiner Grenze."""
    depth = current.max_topic_depth if max_topic_depth is None else max_topic_depth
    days = current.review_days if review_days is None else review_days
    if not 1 <= depth <= MAX_TOPIC_DEPTH_LIMIT:
        raise InvalidInput(
            f"max_topic_depth muss zwischen 1 und {MAX_TOPIC_DEPTH_LIMIT} liegen",
            details={"field": "max_topic_depth", "max": MAX_TOPIC_DEPTH_LIMIT},
        )
    if not 1 <= days <= REVIEW_DAYS_LIMIT:
        raise InvalidInput(
            f"review_days muss zwischen 1 und {REVIEW_DAYS_LIMIT} liegen",
            details={"field": "review_days", "max": REVIEW_DAYS_LIMIT},
        )
    return NotesSettings(depth, days)

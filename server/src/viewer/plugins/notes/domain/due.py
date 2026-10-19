"""Wann eine Note fällig ist: die Entscheidung als reine Funktion, mit der Uhr als Parameter."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime

from viewer.core.domain.errors import InvalidInput
from viewer.plugins.notes.domain.model import Note, NotesViolation, Topic, utc
from viewer.plugins.notes.domain.notices import Notice

#: Die Status eines Items, bei denen ein Ereignis-Auslöser feuert.
EVENT_STATUSES = ("In progress", "Awaiting confirmation", "Completed", "Rejected")
TRIGGER_KINDS = ("event", "topic_date")

#: Gründe, warum eine Note fällig ist, in der Reihenfolge, in der der erste zutreffende gilt.
REASONS = ("trigger", "notice", "topic_due", "review_expired")


@dataclass(frozen=True)
class Trigger:
    """Ein Auslöser einer Note. `event`: das Item `target_uid` erreicht `status`; `topic_date`: der Termin des Topics
    der Note ist erreicht. `fired_at` ist gesetzt, wenn das Ereignis eingetreten ist (es bleibt, bis die Note
    zurückgestellt wird); `already_met` heißt, das Item hatte den Status schon, als der Auslöser angelegt wurde."""

    uid: str
    note_uid: str
    kind: str
    target_uid: str | None = None
    status: str | None = None
    fired_at: datetime | None = None
    already_met: bool = False
    #: Die Verknüpfung (Rolle `trigger`) von der Note zum Item eines Ereignisses.
    link_uid: str | None = None


@dataclass(frozen=True)
class DueState:
    """`status` ist der abgeleitete Status (`due`, oder der gespeicherte), `reason` der Grund, `fired` die `uid`s der
    Auslöser, die eingetreten sind, `all_fired` ob es alle sind."""

    status: str
    reason: str | None
    fired: tuple[str, ...]
    all_fired: bool


def trigger_arrived(trigger: Trigger, topic: Topic | None, now: datetime) -> bool:
    """Ob der Auslöser eingetreten ist; hängt nur von den gespeicherten Daten und `now` ab."""
    if trigger.fired_at is not None:
        return True
    if trigger.kind == "topic_date":
        return (
            topic is not None
            and topic.deleted_at is None
            and topic.due_at is not None
            and utc(topic.due_at) <= utc(now)
        )
    return False  # ein Ereignis tritt nur ein, wenn die Änderung des Items es meldet


def due_state(
    note: Note, triggers: Sequence[Trigger], topic: Topic | None, open_notices: int, now: datetime
) -> DueState:
    """Eine Note in Gebrauch (nicht im Archiv, nicht im Papierkorb) mit `waiting`/`snoozed` ist fällig, wenn ihre
    Auslöser eingetreten sind (im Modus `any` einer, in `all` alle), ein Hinweis offen ist oder ihr Prüfdatum erreicht
    ist. Der Grund ist der erste, der zutrifft: Auslöser, Hinweis, Topic-Termin, Prüfdatum."""
    if note.archived or note.deleted_at is not None or note.status not in ("waiting", "snoozed"):
        return DueState(note.status, None, (), False)
    arrived = [t for t in triggers if trigger_arrived(t, topic, now)]
    fired = tuple(t.uid for t in arrived)
    all_fired = bool(triggers) and len(arrived) == len(triggers)
    triggered = all_fired if note.trigger_mode == "all" else bool(arrived)
    if triggered:
        if all(t.kind == "topic_date" for t in arrived):
            return DueState("due", "notice" if open_notices else "topic_due", fired, all_fired)
        return DueState("due", "trigger", fired, all_fired)
    if open_notices:
        return DueState("due", "notice", fired, all_fired)
    if note.review_at is not None and utc(note.review_at) <= utc(now):
        return DueState("due", "review_expired", fired, all_fired)
    return DueState(note.status, None, fired, all_fired)


def due_since(
    state: DueState, note: Note, triggers: Sequence[Trigger], topic: Topic | None, notices: Sequence[Notice]
) -> datetime | None:
    """Seit wann eine fällige Note fällig ist, nach ihrem Grund: das späteste Eintreten ihrer Auslöser (ein Topic-Termin
    mit seinem Termin), der jüngste offene Hinweis, der Topic-Termin oder das Prüfdatum; nichts, wenn sie nicht fällig
    ist."""
    if state.status != "due":
        return None
    if state.reason == "trigger":
        moments = [_arrived_at(t, topic) for t in triggers if t.uid in state.fired]
        return max((utc(m) for m in moments if m is not None), default=None)
    if state.reason == "notice":
        return max((utc(n.created_at) for n in notices if n.is_open), default=None)
    if state.reason == "topic_due":
        return utc(topic.due_at) if topic is not None and topic.due_at is not None else None
    return utc(note.review_at) if note.review_at is not None else None


def next_clock_due(notes: Sequence[Note], topics: Sequence[Topic], now: datetime) -> datetime | None:
    """Der nächste Zeitpunkt nach `now`, zu dem eine Note durch die Uhr fällig werden kann: das früheste künftige
    Prüfdatum einer Note in Gebrauch oder der früheste künftige Termin eines Topics (weder archiviert noch im
    Papierkorb); `None`, wenn keiner kommt. Alle anderen Gründe kommen mit einem Ereignis."""
    moments = [
        utc(n.review_at)
        for n in notes
        if n.review_at is not None and not n.archived and n.deleted_at is None and n.status in ("waiting", "snoozed")
    ]
    moments += [
        utc(t.due_at) for t in topics if t.due_at is not None and t.archived_at is None and t.deleted_at is None
    ]
    return min((m for m in moments if m > utc(now)), default=None)


def _arrived_at(trigger: Trigger, topic: Topic | None) -> datetime | None:
    if trigger.fired_at is not None:
        return trigger.fired_at
    return topic.due_at if trigger.kind == "topic_date" and topic is not None else None


def is_due(
    note: Note,
    now: datetime,
    triggers: Sequence[Trigger] = (),
    topic: Topic | None = None,
    open_notices: int = 0,
) -> bool:
    return due_state(note, triggers, topic, open_notices, now).status == "due"


def effective_status(
    note: Note,
    now: datetime,
    triggers: Sequence[Trigger] = (),
    topic: Topic | None = None,
    open_notices: int = 0,
) -> str:
    return due_state(note, triggers, topic, open_notices, now).status


def hit(trigger: Trigger, status: str) -> bool:
    """Ob ein Item, das jetzt `status` hat, diesen Ereignis-Auslöser eintreten lässt."""
    return (
        trigger.kind == "event" and trigger.fired_at is None and status in EVENT_STATUSES and trigger.status == status
    )


def check_new_trigger(note: Note, kind: str, status: str | None, topic: Topic | None) -> None:
    """Die Regeln für einen neuen Auslöser, ohne das Item zu kennen (das prüft der Dienst)."""
    if kind not in TRIGGER_KINDS:
        raise InvalidInput(f"Unbekannte Art '{kind}'", details={"field": "kind", "allowed": list(TRIGGER_KINDS)})
    if kind == "event" and status not in EVENT_STATUSES:
        raise InvalidInput(
            "Der Status ist keiner, bei dem ein Item einen Auslöser feuert",
            details={"field": "status", "allowed": list(EVENT_STATUSES)},
        )
    if kind == "topic_date" and (topic is None or topic.due_at is None):
        raise NotesViolation(
            "trigger_needs_topic_date",
            "Ein Topic-Termin-Auslöser braucht ein Topic mit Termin",
            note=note.label,
        )


def reset(triggers: Sequence[Trigger], topic: Topic | None, now: datetime) -> tuple[list[Trigger], list[str]]:
    """Beim Zurückstellen: gefeuerte Ereignisse feuern wieder neu (`fired_at` leer), ein Topic-Termin, der vorbei
    ist, kann nicht noch einmal eintreten und fällt weg. Gibt die bleibenden Auslöser und die `uid`s der entfernten
    zurück."""
    kept: list[Trigger] = []
    removed: list[str] = []
    for trigger in triggers:
        if trigger.kind == "topic_date":
            if trigger_arrived(trigger, topic, now):
                removed.append(trigger.uid)
            else:
                kept.append(trigger)
        else:
            kept.append(replace(trigger, fired_at=None, already_met=False))
    return kept, removed

"""Statusübergänge einer Note. Reine Funktionen: sie geben die geänderte Note zurück oder werfen `NotesViolation`."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from viewer.plugins.notes.domain.model import (
    FINISHED_STATUSES,
    Note,
    NotesViolation,
    Topic,
    default_review_at,
)


def check_open(note: Note) -> None:
    """Nur eine Note in Gebrauch lässt sich ändern: nicht im Papierkorb, nicht im Archiv."""
    if note.deleted_at is not None:
        raise NotesViolation(
            "note_deleted", f"{note.label} liegt im Papierkorb; erst wiederherstellen", note=note.label
        )
    if note.archived:
        raise NotesViolation("note_archived", f"{note.label} liegt im Archiv; erst zurückholen", note=note.label)


def keep(note: Note, now: datetime, review_days: int) -> Note:
    """„Behalten“: die Note bleibt, wie sie ist; nur das Prüfdatum rückt vor."""
    check_open(note)
    return replace(note, review_at=default_review_at(now, review_days))


def snooze(note: Note, now: datetime, review_days: int, review_at: datetime | None = None) -> Note:
    """Zurückgestellt mit neuem Prüfdatum (gegeben oder heute + Intervall)."""
    check_open(note)
    return replace(note, status="snoozed", review_at=review_at or default_review_at(now, review_days))


def finish(note: Note, target: str) -> Note:
    """Erledigt, verworfen oder befördert: die Note wandert ins Archiv."""
    if target not in FINISHED_STATUSES:
        raise NotesViolation("note_target_invalid", f"'{target}' schließt keine Note ab", target=target)
    check_open(note)
    return replace(note, status=target, archived=True)


def restore(note: Note, topic: Topic | None, now: datetime, review_days: int) -> Note:
    """Aus dem Archiv zurück auf „wartet“ mit neuem Prüfdatum; nicht in ein archiviertes oder gelöschtes Topic."""
    if note.deleted_at is not None:
        raise NotesViolation(
            "note_deleted", f"{note.label} liegt im Papierkorb; erst wiederherstellen", note=note.label
        )
    if not note.archived:
        raise NotesViolation("note_not_archived", f"{note.label} liegt nicht im Archiv", note=note.label)
    if topic is not None and (topic.archived_at is not None or topic.deleted_at is not None):
        raise NotesViolation(
            "topic_archived", f"Das Topic {topic.name} ist archiviert oder gelöscht", note=note.label, topic=topic.label
        )
    return replace(note, status="waiting", archived=False, review_at=default_review_at(now, review_days))

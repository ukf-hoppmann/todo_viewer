"""Statusübergänge eines Memos. Reine Funktionen: sie geben das geänderte Memo zurück oder werfen `MemosViolation`."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from viewer.plugins.memos.domain.model import (
    FINISHED_STATUSES,
    Memo,
    MemosViolation,
    Topic,
    default_review_at,
)


def check_open(memo: Memo) -> None:
    """Nur ein Memo in Gebrauch lässt sich ändern: nicht im Papierkorb, nicht im Archiv."""
    if memo.deleted_at is not None:
        raise MemosViolation(
            "memo_deleted", f"{memo.label} liegt im Papierkorb; erst wiederherstellen", memo=memo.label
        )
    if memo.archived:
        raise MemosViolation("memo_archived", f"{memo.label} liegt im Archiv; erst zurückholen", memo=memo.label)


def keep(memo: Memo, now: datetime, review_days: int) -> Memo:
    """„Behalten“: das Memo bleibt, wie sie ist; nur das Prüfdatum rückt vor."""
    check_open(memo)
    return replace(memo, review_at=default_review_at(now, review_days))


def snooze(memo: Memo, now: datetime, review_days: int, review_at: datetime | None = None) -> Memo:
    """Zurückgestellt mit neuem Prüfdatum (gegeben oder heute + Intervall)."""
    check_open(memo)
    return replace(memo, status="snoozed", review_at=review_at or default_review_at(now, review_days))


def finish(memo: Memo, target: str) -> Memo:
    """Erledigt, verworfen oder befördert: das Memo wandert ins Archiv."""
    if target not in FINISHED_STATUSES:
        raise MemosViolation("memo_target_invalid", f"'{target}' schließt kein Memo ab", target=target)
    check_open(memo)
    return replace(memo, status=target, archived=True)


def restore(memo: Memo, topic: Topic | None, now: datetime, review_days: int) -> Memo:
    """Aus dem Archiv zurück auf „wartet“ mit neuem Prüfdatum; nicht in ein archiviertes oder gelöschtes Topic."""
    if memo.deleted_at is not None:
        raise MemosViolation(
            "memo_deleted", f"{memo.label} liegt im Papierkorb; erst wiederherstellen", memo=memo.label
        )
    if not memo.archived:
        raise MemosViolation("memo_not_archived", f"{memo.label} liegt nicht im Archiv", memo=memo.label)
    if topic is not None and (topic.archived_at is not None or topic.deleted_at is not None):
        raise MemosViolation(
            "topic_archived", f"Das Topic {topic.name} ist archiviert oder gelöscht", memo=memo.label, topic=topic.label
        )
    return replace(memo, status="waiting", archived=False, review_at=default_review_at(now, review_days))

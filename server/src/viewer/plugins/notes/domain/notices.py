"""Hinweise zwischen Notes und Items: Ursachen, Entscheidungen und die Regeln dazu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from viewer.core.domain.errors import InvalidInput
from viewer.plugins.notes.domain.model import NotesViolation

SIDES = ("note", "item")
#: Ursachen eines Hinweises an die Note (ein verknüpftes Item hat sich geändert) …
NOTE_CAUSES = ("item_completed", "item_rejected", "item_deleted", "item_retyped")
#: … und an ein Item (eine Note, die es verweist, wurde abgeschlossen).
ITEM_CAUSES = ("note_dropped", "note_promoted")

NOTE_DECISIONS = ("keep", "detach", "drop", "promote")
ITEM_DECISIONS = ("acknowledge",)


@dataclass(frozen=True)
class Notice:
    """Ein Hinweis. `subject_uid` ist, wer informiert wird (Note oder Item, nach `side`), `source_uid` das andere Ende
    der Verknüpfung."""

    uid: str
    side: str
    subject_uid: str
    source_uid: str
    kind: str
    created_at: datetime
    decided_at: datetime | None = None
    decision: str | None = None

    @property
    def is_open(self) -> bool:
        return self.decided_at is None


def decision_options(side: str) -> tuple[str, ...]:
    return NOTE_DECISIONS if side == "note" else ITEM_DECISIONS


def cause_of_status(status: str) -> str | None:
    """Der Hinweis, den eine Note bekommt, wenn ein verwiesenes Item `status` erreicht; nur die abschließenden."""
    return {"Completed": "item_completed", "Rejected": "item_rejected"}.get(status)


def check_decision(notice: Notice, decision: str) -> None:
    """Der Hinweis muss offen sein und die Entscheidung zu seiner Seite gehören."""
    if not notice.is_open:
        raise NotesViolation("notice_decided", "Der Hinweis ist schon entschieden", notice=notice.uid)
    allowed = decision_options(notice.side)
    if decision not in allowed:
        raise InvalidInput(
            f"Entscheidung '{decision}' passt nicht zum Hinweis",
            details={"field": "decision", "allowed": list(allowed)},
        )

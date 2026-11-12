"""Hinweise zwischen Memos und Items: Ursachen, Entscheidungen und die Regeln dazu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from viewer.core.domain.errors import InvalidInput
from viewer.plugins.memos.domain.model import MemosViolation

SIDES = ("memo", "item")
#: Ursachen eines Hinweises an das Memo (ein verknüpftes Item hat sich geändert) …
MEMO_CAUSES = ("item_completed", "item_rejected", "item_deleted", "item_retyped")
#: … und an ein Item (ein Memo, die es verweist, wurde abgeschlossen).
ITEM_CAUSES = ("memo_dropped", "memo_promoted")

MEMO_DECISIONS = ("keep", "detach", "drop", "promote")
ITEM_DECISIONS = ("acknowledge",)


@dataclass(frozen=True)
class Hint:
    """Ein Hinweis. `subject_uid` ist, wer informiert wird (Memo oder Item, nach `side`), `source_uid` das andere Ende
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
    return MEMO_DECISIONS if side == "memo" else ITEM_DECISIONS


def cause_of_status(status: str) -> str | None:
    """Der Hinweis, den ein Memo bekommt, wenn ein verwiesenes Item `status` erreicht; nur die abschließenden."""
    return {"Completed": "item_completed", "Rejected": "item_rejected"}.get(status)


def check_decision(hint: Hint, decision: str) -> None:
    """Der Hinweis muss offen sein und die Entscheidung zu seiner Seite gehören."""
    if not hint.is_open:
        raise MemosViolation("hint_decided", "Der Hinweis ist schon entschieden", hint=hint.uid)
    allowed = decision_options(hint.side)
    if decision not in allowed:
        raise InvalidInput(
            f"Entscheidung '{decision}' passt nicht zum Hinweis",
            details={"field": "decision", "allowed": list(allowed)},
        )

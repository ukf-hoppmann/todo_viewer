"""Hinweise anlegen und die Memos und Items finden, die sie bekommen. Alles in der Transaktion des Aufrufers."""

from __future__ import annotations

from viewer.core.application.ports import Transaction
from viewer.plugins.memos.application.deps import ITEM_KINDS, Deps
from viewer.plugins.memos.domain.hints import Hint
from viewer.plugins.memos.domain.model import Memo


def tell(deps: Deps, tx: Transaction, side: str, subject_uid: str, source_uid: str, kind: str) -> bool:
    """Legt den Hinweis an, wenn für Empfänger, Gegenseite und Ursache nicht schon einer offen ist."""
    if deps.hints.find_open(tx, subject_uid, source_uid, kind) is not None:
        return False
    deps.hints.insert(tx, Hint(deps.new_uid(), side, subject_uid, source_uid, kind, deps.clock.now()))
    return True


def referencing_memos(deps: Deps, tx: Transaction, element_uid: str) -> list[Memo]:
    """Die Memos in Gebrauch, die per Verknüpfung der Rolle `reference` auf das Element verweisen."""
    found: list[Memo] = []
    for view in deps.links.incoming(tx, element_uid):
        if view.link.role != "reference" or view.element.kind != "memo" or view.element.deleted_at is not None:
            continue
        memo = deps.memos.get(tx, view.element.uid)
        if memo is not None and memo.deleted_at is None and not memo.archived and not memo.finished:
            found.append(memo)
    return found


def tell_memos(deps: Deps, tx: Transaction, item_uid: str, cause: str) -> list[str]:
    """Hinweis an jedes Memo in Gebrauch, die auf das Item verweist. Gibt die `uid`s der informierten Memos zurück."""
    told = []
    for memo in referencing_memos(deps, tx, item_uid):
        if tell(deps, tx, "memo", memo.uid, item_uid, cause):
            told.append(memo.uid)
    return told


def tell_items(deps: Deps, tx: Transaction, memo: Memo, cause: str) -> list[str]:
    """Hinweis an jedes Item (nicht im Papierkorb), auf das die abgeschlossene Memo per `reference` verweist."""
    items = [
        view.element.uid
        for view in deps.links.outgoing(tx, memo.uid)
        if view.link.role == "reference" and view.element.kind in ITEM_KINDS and view.element.deleted_at is None
    ]
    return [uid for uid in items if tell(deps, tx, "item", uid, memo.uid, cause)]

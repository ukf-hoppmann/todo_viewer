"""Hinweise anlegen und die Notes und Items finden, die sie bekommen. Alles in der Transaktion des Aufrufers."""

from __future__ import annotations

from viewer.core.application.ports import Transaction
from viewer.plugins.notes.application.deps import ITEM_KINDS, Deps
from viewer.plugins.notes.domain.model import Note
from viewer.plugins.notes.domain.notices import Notice


def tell(deps: Deps, tx: Transaction, side: str, subject_uid: str, source_uid: str, kind: str) -> bool:
    """Legt den Hinweis an, wenn für Empfänger, Gegenseite und Ursache nicht schon einer offen ist."""
    if deps.notices.find_open(tx, subject_uid, source_uid, kind) is not None:
        return False
    deps.notices.insert(tx, Notice(deps.new_uid(), side, subject_uid, source_uid, kind, deps.clock.now()))
    return True


def referencing_notes(deps: Deps, tx: Transaction, element_uid: str) -> list[Note]:
    """Die Notes in Gebrauch, die per Verknüpfung der Rolle `reference` auf das Element verweisen."""
    found: list[Note] = []
    for view in deps.links.incoming(tx, element_uid):
        if view.link.role != "reference" or view.element.kind != "note" or view.element.deleted_at is not None:
            continue
        note = deps.notes.get(tx, view.element.uid)
        if note is not None and note.deleted_at is None and not note.archived and not note.finished:
            found.append(note)
    return found


def tell_notes(deps: Deps, tx: Transaction, item_uid: str, cause: str) -> list[str]:
    """Hinweis an jede Note in Gebrauch, die auf das Item verweist. Gibt die `uid`s der informierten Notes zurück."""
    told = []
    for note in referencing_notes(deps, tx, item_uid):
        if tell(deps, tx, "note", note.uid, item_uid, cause):
            told.append(note.uid)
    return told


def tell_items(deps: Deps, tx: Transaction, note: Note, cause: str) -> list[str]:
    """Hinweis an jedes Item (nicht im Papierkorb), auf das die abgeschlossene Note per `reference` verweist."""
    items = [
        view.element.uid
        for view in deps.links.outgoing(tx, note.uid)
        if view.link.role == "reference" and view.element.kind in ITEM_KINDS and view.element.deleted_at is None
    ]
    return [uid for uid in items if tell(deps, tx, "item", uid, note.uid, cause)]

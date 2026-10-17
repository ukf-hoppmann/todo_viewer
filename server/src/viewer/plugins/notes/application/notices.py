"""Hinweise lesen und entscheiden."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from viewer.core.domain.errors import NotFound
from viewer.core.domain.events import Event
from viewer.plugins.notes.application.common import NOTE_TOPIC
from viewer.plugins.notes.application.conversion import ConversionService
from viewer.plugins.notes.application.deps import ITEM_KINDS, Deps
from viewer.plugins.notes.application.notes import NoteService
from viewer.plugins.notes.application.telling import tell_notes
from viewer.plugins.notes.application.triggers import Announce
from viewer.plugins.notes.domain import lifecycle
from viewer.plugins.notes.domain.notices import Notice, check_decision


@dataclass(frozen=True)
class DecisionResult:
    notice: Notice
    note_uid: str | None


@dataclass(frozen=True)
class ItemNotice:
    notice: Notice
    #: Die Note, die den Hinweis ausgelöst hat (uid, label, title).
    source: Any | None


class NoticeService:
    def __init__(self, deps: Deps, notes: NoteService, conversion: ConversionService) -> None:
        self._d = deps
        self._notes = notes
        self._conversion = conversion

    def list_for_item(self, ref: str, project_uid: str | None) -> list[ItemNotice]:
        """Die offenen Hinweise an ein Item (eine Note, die auf es verweist, wurde verworfen oder befördert)."""
        d = self._d
        with d.database.transaction() as tx:
            element = d.registry.get(tx, ref) or (
                d.registry.find_by_label(tx, project_uid, ref) if project_uid else None
            )
            if element is None:
                raise NotFound(f"Item {ref} gibt es nicht", details={"ref": ref})
            notices = d.notices.open_for(tx, [element.uid]).get(element.uid, [])
            return [ItemNotice(notice, d.registry.get(tx, notice.source_uid)) for notice in notices]

    def decide(
        self, notice_uid: str, decision: str, version: int | None, item_type: str | None, fields: Mapping[str, Any]
    ) -> DecisionResult:
        """Entscheidet einen offenen Hinweis. Zuerst wirkt die Entscheidung, dann wird der Hinweis entschieden: ein
        Fehler lässt ihn offen. `keep` rückt das Prüfdatum, `detach` entfernt die Verknüpfung zum Item, `drop`
        verwirft die Note, `promote` befördert sie (`item_type` und `fields` wie bei `promote_note`); am Item
        quittiert `acknowledge`."""
        d = self._d
        with d.database.transaction() as tx:
            notice = d.notices.get(tx, notice_uid)
            if notice is None:
                raise NotFound(f"Hinweis {notice_uid} gibt es nicht", details={"uid": notice_uid})
            check_decision(notice, decision)
            note = d.notes.get(tx, notice.subject_uid) if notice.side == "note" else None
        if note is not None:
            expected = note.revision if version is None else version
            if decision == "keep":
                self._notes.keep(note.uid, None, expected)
            elif decision == "detach":
                self._detach(note.uid, notice.source_uid)
            elif decision == "drop":
                self._notes.finish(note.uid, None, expected, "dropped")
            else:
                self._conversion.promote(note.uid, None, expected, item_type or "Task", fields)
        with d.database.transaction() as tx:
            d.notices.decide(tx, notice_uid, decision, d.clock.now())
            decided = d.notices.get(tx, notice_uid)
        assert decided is not None
        if note is not None:
            d.events.publish(Event(NOTE_TOPIC, {"uid": note.uid, "change": "updated"}, public=True))
        return DecisionResult(decided, None if note is None else note.uid)

    def _detach(self, note_uid: str, source_uid: str) -> None:
        d = self._d
        announce = Announce()
        with d.database.transaction() as tx:
            note = d.notes.get(tx, note_uid)
            assert note is not None
            lifecycle.check_open(note)
            for view in d.links.outgoing(tx, note_uid):
                if view.link.to_uid == source_uid and view.link.role == "reference":
                    d.links.remove(tx, view.link.uid)
                    announce.links.append(("removed", view.link))
        announce.publish(d)

    # --- Ereignisse -----------------------------------------------------------------------------------------------

    def on_elements_changed(self, event: Event) -> None:
        """`workspace.element.changed`: ein Item im Papierkorb ist ein Hinweis für die Notes, die auf es verweisen."""
        d = self._d
        if event.payload.get("change") != "deleted":
            return
        told: list[str] = []
        with d.database.transaction() as tx:
            for uid in event.payload.get("uids", []):
                element = d.registry.get(tx, uid)
                if element is not None and element.kind in ITEM_KINDS:
                    told.extend(tell_notes(d, tx, uid, "item_deleted"))
        self._publish(told)

    def on_item_changed(self, event: Event) -> None:
        """`backlog.item.changed` mit `retyped`: das Item hat ein neues Label, die Notes sollen es wissen."""
        d = self._d
        if event.payload.get("change") != "retyped":
            return
        with d.database.transaction() as tx:
            told = tell_notes(d, tx, str(event.payload.get("uid", "")), "item_retyped")
        self._publish(told)

    def _publish(self, uids: list[str]) -> None:
        for uid in dict.fromkeys(uids):
            self._d.events.publish(Event(NOTE_TOPIC, {"uid": uid, "change": "updated"}, public=True))

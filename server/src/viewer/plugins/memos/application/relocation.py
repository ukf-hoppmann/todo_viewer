"""Eine Memo in ein anderes Projekt verschieben: dort entsteht eine neue Memo, die alte kommt in den Papierkorb."""

from __future__ import annotations

from dataclasses import replace

from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import ELEMENT_TOPIC, MEMO_TOPIC, usable_topic
from viewer.plugins.memos.application.conversion import renamed_document
from viewer.plugins.memos.application.deps import Deps
from viewer.plugins.memos.application.ports import Document
from viewer.plugins.memos.application.triggers import Announce, TriggerService
from viewer.plugins.memos.domain import lifecycle
from viewer.plugins.memos.domain.model import Memo, MemosViolation


class RelocationService:
    def __init__(self, deps: Deps, triggers: TriggerService) -> None:
        self._d = deps
        self._triggers = triggers

    def move_to_project(
        self, ref: str, project_uid: str | None, version: int, target_project: str, topic: str | None
    ) -> str:
        """Gibt die `uid` der neuen Memo zurück. Übernommen werden Texte, Status, Prüfdatum, Dokumente (mit dem neuen
        Label im Namen), Verweise und Ereignis-Auslöser; ein Topic-Termin-Auslöser entfällt, weil das Topic wechselt."""
        d = self._d
        announce = Announce()
        now = d.clock.now()
        with d.database.transaction() as tx:
            old = d.resolver.memo(tx, ref, project_uid)
            lifecycle.check_open(old)
            if old.project_uid == target_project:
                raise MemosViolation("same_project", "Das Memo liegt schon in diesem Projekt", memo=old.label)
            usable_topic(d.topics, tx, topic, target_project)
            element = d.registry.register(tx, target_project, "memo", old.summary)
            new = Memo(
                element.uid,
                target_project,
                element.label,
                old.summary,
                old.body,
                old.status,
                topic,
                old.review_at,
                old.trigger_mode,
                False,
                element.revision,
            )
            d.memos.insert(tx, new)
            for document in d.documents.list_for(tx, old.uid):
                name = renamed_document(document.name, old.label, new.label) or document.name
                d.documents.insert(tx, Document(new.uid, name, document.kind, document.content, 1, now))
            for view in d.links.outgoing(tx, old.uid):
                if view.link.role != "trigger":
                    announce.links.append(("added", d.links.add(tx, new.uid, view.link.to_uid, view.link.role)))
            for trigger in d.triggers.for_memos(tx, [old.uid]).get(old.uid, []):
                if trigger.kind != "event":
                    continue
                created = self._triggers.create_in_tx(tx, new, "event", trigger.target_uid, trigger.status, announce)
                if trigger.fired_at is not None:
                    d.triggers.update(tx, replace(created, fired_at=trigger.fired_at, already_met=trigger.already_met))
            d.registry.bump_revision(tx, old.uid, version)
            d.registry.mark_deleted(tx, old.uid, now)
        announce.publish(d)
        d.events.publish(Event(MEMO_TOPIC, {"uid": new.uid, "change": "created"}, public=True))
        d.events.publish(Event(MEMO_TOPIC, {"uid": old.uid, "change": "deleted"}, public=True))
        d.events.publish(Event(ELEMENT_TOPIC, {"change": "deleted", "uids": [old.uid]}, public=True))
        return new.uid

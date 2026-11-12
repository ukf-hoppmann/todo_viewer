"""Hinweise lesen und entscheiden."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from viewer.core.domain.errors import NotFound
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import MEMO_TOPIC
from viewer.plugins.memos.application.conversion import ConversionService
from viewer.plugins.memos.application.deps import ITEM_KINDS, Deps
from viewer.plugins.memos.application.memos import MemoService
from viewer.plugins.memos.application.telling import tell_memos
from viewer.plugins.memos.application.triggers import Announce
from viewer.plugins.memos.domain import lifecycle
from viewer.plugins.memos.domain.hints import Hint, check_decision


@dataclass(frozen=True)
class DecisionResult:
    hint: Hint
    memo_uid: str | None


@dataclass(frozen=True)
class ItemHint:
    hint: Hint
    #: Das Memo, die den Hinweis ausgelöst hat (uid, label, title).
    source: Any | None


class HintService:
    def __init__(self, deps: Deps, memos: MemoService, conversion: ConversionService) -> None:
        self._d = deps
        self._memos = memos
        self._conversion = conversion

    def list_for_item(self, ref: str, project_uid: str | None) -> list[ItemHint]:
        """Die offenen Hinweise an ein Item (ein Memo, die auf es verweist, wurde verworfen oder befördert)."""
        d = self._d
        with d.database.transaction() as tx:
            element = d.registry.get(tx, ref) or (
                d.registry.find_by_label(tx, project_uid, ref) if project_uid else None
            )
            if element is None:
                raise NotFound(f"Item {ref} gibt es nicht", details={"ref": ref})
            hints = d.hints.open_for(tx, [element.uid]).get(element.uid, [])
            return [ItemHint(hint, d.registry.get(tx, hint.source_uid)) for hint in hints]

    def decide(
        self, hint_uid: str, decision: str, version: int | None, item_type: str | None, fields: Mapping[str, Any]
    ) -> DecisionResult:
        """Entscheidet einen offenen Hinweis. Zuerst wirkt die Entscheidung, dann wird der Hinweis entschieden: ein
        Fehler lässt ihn offen. `keep` rückt das Prüfdatum, `detach` entfernt die Verknüpfung zum Item, `drop`
        verwirft das Memo, `promote` befördert es (`item_type` und `fields` wie bei `promote_memo`); am Item
        quittiert `acknowledge`."""
        d = self._d
        with d.database.transaction() as tx:
            hint = d.hints.get(tx, hint_uid)
            if hint is None:
                raise NotFound(f"Hinweis {hint_uid} gibt es nicht", details={"uid": hint_uid})
            check_decision(hint, decision)
            memo = d.memos.get(tx, hint.subject_uid) if hint.side == "memo" else None
        if memo is not None:
            expected = memo.revision if version is None else version
            if decision == "keep":
                self._memos.keep(memo.uid, None, expected)
            elif decision == "detach":
                self._detach(memo.uid, hint.source_uid)
            elif decision == "drop":
                self._memos.finish(memo.uid, None, expected, "dropped")
            else:
                self._conversion.promote(memo.uid, None, expected, item_type or "Task", fields)
        with d.database.transaction() as tx:
            d.hints.decide(tx, hint_uid, decision, d.clock.now())
            decided = d.hints.get(tx, hint_uid)
        assert decided is not None
        if memo is not None:
            d.events.publish(Event(MEMO_TOPIC, {"uid": memo.uid, "change": "updated"}, public=True))
        return DecisionResult(decided, None if memo is None else memo.uid)

    def _detach(self, memo_uid: str, source_uid: str) -> None:
        d = self._d
        announce = Announce()
        with d.database.transaction() as tx:
            memo = d.memos.get(tx, memo_uid)
            assert memo is not None
            lifecycle.check_open(memo)
            for view in d.links.outgoing(tx, memo_uid):
                if view.link.to_uid == source_uid and view.link.role == "reference":
                    d.links.remove(tx, view.link.uid)
                    announce.links.append(("removed", view.link))
        announce.publish(d)

    # --- Ereignisse -----------------------------------------------------------------------------------------------

    def on_elements_changed(self, event: Event) -> None:
        """`workspace.element.changed`: ein Item im Papierkorb ist ein Hinweis für die Memos, die auf es verweisen."""
        d = self._d
        if event.payload.get("change") != "deleted":
            return
        told: list[str] = []
        with d.database.transaction() as tx:
            for uid in event.payload.get("uids", []):
                element = d.registry.get(tx, uid)
                if element is not None and element.kind in ITEM_KINDS:
                    told.extend(tell_memos(d, tx, uid, "item_deleted"))
        self._publish(told)

    def on_item_changed(self, event: Event) -> None:
        """`backlog.item.changed` mit `retyped`: das Item hat ein neues Label, die Memos sollen es wissen."""
        d = self._d
        if event.payload.get("change") != "retyped":
            return
        with d.database.transaction() as tx:
            told = tell_memos(d, tx, str(event.payload.get("uid", "")), "item_retyped")
        self._publish(told)

    def _publish(self, uids: list[str]) -> None:
        for uid in dict.fromkeys(uids):
            self._d.events.publish(Event(MEMO_TOPIC, {"uid": uid, "change": "updated"}, public=True))

"""Auslöser eines Memos: anlegen, entfernen und auf Änderungen von Items reagieren."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import InvalidInput, NotFound
from viewer.core.domain.events import Event
from viewer.plugins.memos.application.common import MEMO_TOPIC
from viewer.plugins.memos.application.deps import ITEM_KINDS, Deps
from viewer.plugins.memos.application.telling import tell_memos
from viewer.plugins.memos.domain import lifecycle
from viewer.plugins.memos.domain.due import Trigger, check_new_trigger
from viewer.plugins.memos.domain.hints import cause_of_status
from viewer.plugins.memos.domain.model import Memo


@dataclass
class Announce:
    """Verknüpfungen, die in der Transaktion entstanden oder verschwunden sind: nach dem Commit zu melden."""

    links: list[tuple[str, Any]]

    def __init__(self) -> None:
        self.links = []

    def publish(self, deps: Deps) -> None:
        for change, link in self.links:
            deps.links.announce(change, link)


class TriggerService:
    def __init__(self, deps: Deps) -> None:
        self._deps = deps

    # --- für die Operationen -------------------------------------------------------------------------------------

    def add(self, ref: str, project_uid: str | None, kind: str, target: str | None, status: str | None) -> str:
        """Legt den Auslöser an und gibt die `uid` des Memos zurück."""
        deps = self._deps
        announce = Announce()
        with deps.database.transaction() as tx:
            memo = deps.resolver.memo(tx, ref, project_uid)
            lifecycle.check_open(memo)
            self.create_in_tx(tx, memo, kind, target, status, announce)
        announce.publish(deps)
        self._changed(memo.uid)
        return memo.uid

    def remove(self, trigger_uid: str) -> str:
        """Entfernt den Auslöser und gibt die `uid` des Memos zurück."""
        deps = self._deps
        announce = Announce()
        with deps.database.transaction() as tx:
            trigger = deps.triggers.get(tx, trigger_uid)
            if trigger is None:
                raise NotFound(f"Auslöser {trigger_uid} gibt es nicht", details={"uid": trigger_uid})
            memo = deps.memos.get(tx, trigger.memo_uid)
            assert memo is not None
            lifecycle.check_open(memo)
            self.remove_in_tx(tx, trigger, announce)
        announce.publish(deps)
        self._changed(memo.uid)
        return memo.uid

    # --- in der Transaktion des Aufrufers -------------------------------------------------------------------------

    def create_in_tx(
        self, tx: Transaction, memo: Memo, kind: str, target: str | None, status: str | None, announce: Announce
    ) -> Trigger:
        """Legt einen Auslöser an: ein Ereignis auf ein Item (mit Verknüpfung der Rolle `trigger`) oder den Termin des
        Topics des Memos. Hat das Item den Status schon, feuert er sofort (`already_met`)."""
        deps = self._deps
        topic = deps.topics.get(tx, memo.topic_uid) if memo.topic_uid else None
        check_new_trigger(memo, kind, status, topic)
        trigger = Trigger(deps.new_uid(), memo.uid, kind, None, status if kind == "event" else None)
        if kind == "event":
            target_uid = self._item_uid(tx, target, memo.project_uid)
            info = deps.gateway.get_item(target_uid)
            if info is None or info.deleted:
                raise NotFound(f"Item {target} gibt es nicht", details={"ref": target})
            trigger = replace(trigger, target_uid=target_uid)
            if info.status == status:
                trigger = replace(trigger, fired_at=deps.clock.now(), already_met=True)
            link = self._link(tx, memo.uid, target_uid, announce)
            trigger = replace(trigger, link_uid=link)
        deps.triggers.insert(tx, trigger)
        return trigger

    def remove_in_tx(self, tx: Transaction, trigger: Trigger, announce: Announce) -> None:
        """Entfernt den Auslöser und seine Verknüpfung, wenn kein anderer Auslöser sie braucht."""
        deps = self._deps
        deps.triggers.delete(tx, trigger.uid)
        if trigger.link_uid is None:
            return
        others = deps.triggers.for_memos(tx, [trigger.memo_uid]).get(trigger.memo_uid, [])
        if any(other.link_uid == trigger.link_uid for other in others):
            return
        link = next((v.link for v in deps.links.outgoing(tx, trigger.memo_uid) if v.link.uid == trigger.link_uid), None)
        if link is not None:
            deps.links.remove(tx, link.uid)
            announce.links.append(("removed", link))

    # --- Ereignisse -----------------------------------------------------------------------------------------------

    def on_status_changed(self, event: Event) -> None:
        """`backlog.item.status_changed`: Auslöser auf das Item feuern, Hinweise für abschließende Status."""
        deps = self._deps
        item_uid, status = str(event.payload.get("uid", "")), str(event.payload.get("to", ""))
        touched: list[str] = []
        with deps.database.transaction() as tx:
            for trigger in deps.triggers.waiting_on(tx, item_uid, status):
                memo = deps.memos.get(tx, trigger.memo_uid)
                if memo is None or memo.deleted_at is not None or memo.archived or memo.finished:
                    continue
                deps.triggers.update(tx, replace(trigger, fired_at=deps.clock.now()))
                touched.append(memo.uid)
            cause = cause_of_status(status)
            if cause is not None:
                touched.extend(tell_memos(deps, tx, item_uid, cause))
        for uid in dict.fromkeys(touched):
            self._changed(uid)

    # --- Hilfen ---------------------------------------------------------------------------------------------------

    def _item_uid(self, tx: Transaction, target: str | None, project_uid: str) -> str:
        if not target:
            raise InvalidInput("Das Ziel des Auslösers fehlt", details={"field": "target"})
        element = self._deps.registry.get(tx, target) or self._deps.registry.find_by_label(tx, project_uid, target)
        if element is None:
            raise NotFound(f"Item {target} gibt es nicht", details={"ref": target})
        if element.kind not in ITEM_KINDS:
            raise InvalidInput("Ein Ereignis-Auslöser braucht ein Item", details={"field": "target"})
        return str(element.uid)

    def _link(self, tx: Transaction, memo_uid: str, target_uid: str, announce: Announce) -> str:
        """Die Verknüpfung `trigger` vom Memo zum Item; eine vorhandene wird mitbenutzt."""
        deps = self._deps
        existing = next(
            (
                v.link
                for v in deps.links.outgoing(tx, memo_uid)
                if v.link.to_uid == target_uid and v.link.role == "trigger"
            ),
            None,
        )
        if existing is not None:
            return str(existing.uid)
        link = deps.links.add(tx, memo_uid, target_uid, "trigger")
        announce.links.append(("added", link))
        return str(link.uid)

    def _changed(self, uid: str) -> None:
        self._deps.events.publish(Event(MEMO_TOPIC, {"uid": uid, "change": "updated"}, public=True))

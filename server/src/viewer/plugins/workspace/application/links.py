from __future__ import annotations

from collections.abc import Callable

from viewer.core.application.ports import Clock, Database, EventBus, Transaction
from viewer.core.domain.errors import NotFound
from viewer.core.domain.events import Event
from viewer.plugins.workspace.application.ports import ElementStore, LinkStore
from viewer.plugins.workspace.domain.model import (
    Element,
    Link,
    LinkExists,
    LinkView,
    TriggerLinkReserved,
    validate_link,
)

CHANGED_TOPIC = "workspace.links.changed"


class LinkService:
    """Verknüpfungen zwischen Elementen. Die Methoden mit `tx` (Port `Links`) nutzen die Transaktion des Aufrufers und
    melden nichts selbst: das Plugin des Aufrufers veröffentlicht nach dem Commit mit `announce`. Die `*_link`-Fälle
    für die Operationen sind je eine Transaktion mit Ereignis und lehnen die Rolle `trigger` ab."""

    def __init__(
        self,
        links: LinkStore,
        elements: ElementStore,
        database: Database,
        clock: Clock,
        events: EventBus,
        new_uid: Callable[[], str],
    ) -> None:
        self._links = links
        self._elements = elements
        self._database = database
        self._clock = clock
        self._events = events
        self._new_uid = new_uid

    # --- Port `Links` -------------------------------------------------------------------------------------------

    def add(self, tx: Transaction, from_uid: str, to_uid: str, role: str) -> Link:
        checked = validate_link(from_uid, to_uid, role)
        self._require(tx, from_uid)
        self._require(tx, to_uid)
        if self._links.find(tx, from_uid, to_uid, checked) is not None:
            raise LinkExists(
                "Diese Verknüpfung gibt es schon", details={"from_uid": from_uid, "to_uid": to_uid, "role": checked}
            )
        link = Link(self._new_uid(), from_uid, to_uid, checked, self._clock.now())
        self._links.insert(tx, link)
        return link

    def remove(self, tx: Transaction, uid: str) -> Link:
        link = self._links.get(tx, uid)
        if link is None:
            raise NotFound(f"Verknüpfung {uid} gibt es nicht", details={"uid": uid})
        self._links.delete(tx, uid)
        return link

    def outgoing(self, tx: Transaction, uid: str) -> list[LinkView]:
        return [LinkView(link, self._require(tx, link.to_uid)) for link in self._links.outgoing(tx, uid)]

    def incoming(self, tx: Transaction, uid: str) -> list[LinkView]:
        return [LinkView(link, self._require(tx, link.from_uid)) for link in self._links.incoming(tx, uid)]

    def announce(self, change: str, link: Link) -> None:
        payload = {
            "change": change,
            "uid": link.uid,
            "from_uid": link.from_uid,
            "to_uid": link.to_uid,
            "role": link.role,
        }
        self._events.publish(Event(CHANGED_TOPIC, payload, public=True))

    # --- Fälle der Operationen ----------------------------------------------------------------------------------

    def add_link(self, from_uid: str, to_uid: str, role: str) -> LinkView:
        if role == "trigger":
            raise TriggerLinkReserved("Verknüpfungen der Rolle 'trigger' legt nur ein Auslöser der Notes an")
        with self._database.transaction() as tx:
            link = self.add(tx, from_uid, to_uid, role)
            view = LinkView(link, self._require(tx, to_uid))
        self.announce("added", link)
        return view

    def remove_link(self, uid: str) -> None:
        with self._database.transaction() as tx:
            existing = self._links.get(tx, uid)
            if existing is not None and existing.role == "trigger":
                raise TriggerLinkReserved("Verknüpfungen der Rolle 'trigger' entfernt nur ihr Auslöser")
            link = self.remove(tx, uid)
        self.announce("removed", link)

    def list_links(self, uid: str) -> tuple[list[LinkView], list[LinkView]]:
        with self._database.transaction() as tx:
            self._require(tx, uid)
            return self.outgoing(tx, uid), self.incoming(tx, uid)

    def search_elements(self, query: str, limit: int = 50) -> list[Element]:
        with self._database.transaction() as tx:
            return self._elements.search(tx, query, limit) if query.strip() else []

    def _require(self, tx: Transaction, uid: str) -> Element:
        element = self._elements.get(tx, uid)
        if element is None:
            raise NotFound(f"Element {uid} gibt es nicht", details={"uid": uid})
        return element

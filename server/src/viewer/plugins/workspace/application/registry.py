from __future__ import annotations

from collections.abc import Callable

from viewer.core.application.ports import Clock, Transaction
from viewer.core.domain.errors import NotFound
from viewer.core.domain.plugin import ElementKind
from viewer.plugins.workspace.application.ports import ElementStore, ProjectStore
from viewer.plugins.workspace.domain.model import Element, UnknownElementKind, format_label

#: Erzeugt eine neue `uid`; die Composition Root gibt `uuid4`, Tests eine feste Folge.
NewUid = Callable[[], str]


class RegistryService:
    """Das Element-Register: gemeinsame Identität (`uid`), Label und Revision für alle Elementtypen.

    Ein Label wird je Projekt und Präfix durchnummeriert und nie wieder vergeben (der Zähler läuft nur vorwärts,
    auch nach dem Löschen und nach einem Typwechsel). Jedes Label, das ein Element je hatte, bleibt in der
    Historie und löst weiter auf.
    """

    def __init__(self, elements: ElementStore, projects: ProjectStore, clock: Clock, new_uid: NewUid) -> None:
        self._elements = elements
        self._projects = projects
        self._clock = clock
        self._new_uid = new_uid

    def register_kinds(self, tx: Transaction, owner: str, kinds: list[ElementKind]) -> None:
        self._elements.upsert_kinds(tx, owner, kinds)

    def register(self, tx: Transaction, project_uid: str, kind: str, title: str = "") -> Element:
        if self._projects.get(tx, project_uid) is None:
            raise NotFound(f"Projekt {project_uid} gibt es nicht", details={"project": project_uid})
        label = self._next_label(tx, project_uid, kind)
        now = self._clock.now()
        element = Element(self._new_uid(), project_uid, kind, label, 1, now, now, title=title.strip())
        self._elements.insert(tx, element)
        self._elements.add_history(tx, project_uid, label, element.uid)
        return element

    def relabel(self, tx: Transaction, uid: str, new_kind: str) -> Element:
        element = self._require(tx, uid)
        if element.kind == new_kind:
            return element
        label = self._next_label(tx, element.project_uid, new_kind)
        self._elements.set_kind_and_label(tx, uid, new_kind, label, self._clock.now())
        self._elements.add_history(tx, element.project_uid, label, uid)
        return self._require(tx, uid)

    def get(self, tx: Transaction, uid: str) -> Element | None:
        return self._elements.get(tx, uid)

    def find_by_label(self, tx: Transaction, project_uid: str, label: str) -> Element | None:
        uid = self._elements.find_uid_by_label(tx, project_uid, label.strip())
        return self._elements.get(tx, uid) if uid else None

    def bump_revision(self, tx: Transaction, uid: str, expected: int) -> int:
        return self._elements.bump_revision(tx, uid, expected, self._clock.now())

    def mark_deleted(self, tx: Transaction, uid: str) -> Element:
        now = self._clock.now()
        self._require(tx, uid)
        self._elements.set_deleted(tx, uid, now, now)
        return self._require(tx, uid)

    def restore(self, tx: Transaction, uid: str) -> Element:
        self._require(tx, uid)
        self._elements.set_deleted(tx, uid, None, self._clock.now())
        return self._require(tx, uid)

    def set_title(self, tx: Transaction, uid: str, title: str) -> None:
        self._require(tx, uid)
        self._elements.set_title(tx, uid, title.strip(), self._clock.now())

    def search(self, tx: Transaction, query: str, limit: int = 50) -> list[Element]:
        return self._elements.search(tx, query, limit) if query.strip() else []

    def purge(self, tx: Transaction, uid: str) -> None:
        self._require(tx, uid)
        self._elements.delete(tx, uid)

    def _next_label(self, tx: Transaction, project_uid: str, kind: str) -> str:
        prefix = self._elements.kind_prefix(tx, kind)
        if prefix is None:
            raise UnknownElementKind(f"Der Elementtyp '{kind}' ist nicht angemeldet", details={"kind": kind})
        return format_label(prefix, self._elements.next_number(tx, project_uid, prefix))

    def _require(self, tx: Transaction, uid: str) -> Element:
        element = self._elements.get(tx, uid)
        if element is None:
            raise NotFound(f"Element {uid} gibt es nicht", details={"uid": uid})
        return element

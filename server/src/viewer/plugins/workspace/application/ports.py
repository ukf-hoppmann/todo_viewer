"""Ports des Plugins `workspace`.

`ElementRegistry` und `Projects` sind die öffentliche Schnittstelle für andere Plugins (`viewer.plugins.workspace`);
`ProjectStore` und `ElementStore` braucht nur das Plugin selbst. Alle Methoden, die schreiben, nehmen die Transaktion
des Aufrufers, damit ein Plugin sein Element und seine eigenen Zeilen atomar anlegt.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Protocol

from viewer.core.application.ports import Transaction
from viewer.core.domain.plugin import ElementKind
from viewer.plugins.workspace.domain.model import Element, Link, LinkView, Project


class ElementRegistry(Protocol):
    def register(self, tx: Transaction, project_uid: str, kind: str, title: str = "") -> Element:
        """Legt ein Element an: vergibt `uid` und das nächste freie Label des Typs im Projekt."""
        ...

    def relabel(self, tx: Transaction, uid: str, new_kind: str) -> Element:
        """Typwechsel: neues Label des neuen Typs, die `uid` bleibt, das alte Label löst weiter auf."""
        ...

    def get(self, tx: Transaction, uid: str) -> Element | None: ...

    def find_by_label(self, tx: Transaction, project_uid: str, label: str) -> Element | None:
        """Findet auch ein früheres Label und liefert das Element mit seinem aktuellen Label."""
        ...

    def bump_revision(self, tx: Transaction, uid: str, expected: int) -> int:
        """Erhöht die `revision`, wenn sie `expected` ist; sonst `version_conflict`. Gibt die neue zurück."""
        ...

    def mark_deleted(self, tx: Transaction, uid: str, at: datetime | None = None) -> Element:
        """Legt das Element in den Papierkorb (`at`: Löschzeitpunkt, sonst jetzt)."""
        ...

    def restore(self, tx: Transaction, uid: str) -> Element: ...

    def purge(self, tx: Transaction, uid: str) -> None:
        """Löscht das Element endgültig (mit seiner Label-Historie; das Label wird trotzdem nie wieder vergeben)."""
        ...

    def set_title(self, tx: Transaction, uid: str, title: str) -> None:
        """Setzt den Anzeigetitel (für Suche und Verknüpfungen); das Fach-Plugin ruft das bei jeder Titeländerung."""
        ...

    def reserve_label(self, tx: Transaction, project_uid: str, kind: str) -> str:
        """Vergibt das nächste freie Label des Typs, ohne ein Element anzulegen (für den Sync: das Element folgt
        mit `register_as`). Das Label wird nie wieder vergeben."""
        ...

    def note_labels(self, tx: Transaction, project_uid: str, labels: Sequence[str]) -> None:
        """Zieht die Zähler nach, ohne etwas anzulegen: Labels, die gleich mit `register_as` entstehen."""
        ...

    def register_as(
        self, tx: Transaction, project_uid: str, kind: str, uid: str, label: str, title: str = ""
    ) -> Element:
        """Legt ein Element mit vorgegebener `uid` und vorgegebenem Label an (Sync, Datenübernahme); der Zähler des
        Typs zieht nach, wenn das Label eine höhere Nummer hat."""
        ...

    def search(self, tx: Transaction, query: str, limit: int = 50) -> list[Element]:
        """Nicht gelöschte Elemente aller Projekte, deren Label oder Titel `query` enthält."""
        ...


#: `ChildrenProvider`: die `uid`s aller direkten Kinder eines Elements, gelöschte eingeschlossen.
ChildrenProvider = Callable[[Transaction, str], list[str]]
#: `RestoreGuard`: wirft einen `DomainError`, wenn das Wiederherstellen gegen eine Regel des Plugins verstößt.
RestoreGuard = Callable[[Transaction, Element], None]
#: `Purger`: entfernt die Plugin-Daten (und Dokumente) eines Elements vor dem endgültigen Löschen.
Purger = Callable[[Transaction, str], None]


class TrashRegistry(Protocol):
    """Hier melden die Plugins beim Bau an, wie der Papierkorb mit ihren Elementtypen umgehen soll."""

    def register(
        self,
        kind: str,
        *,
        children: ChildrenProvider | None = None,
        restore_guard: RestoreGuard | None = None,
        purger: Purger | None = None,
    ) -> None: ...


class Links(Protocol):
    """Verknüpfungen zwischen Elementen für andere Plugins (`notes` legt `trigger`-Verknüpfungen an)."""

    def add(self, tx: Transaction, from_uid: str, to_uid: str, role: str) -> Link: ...

    def remove(self, tx: Transaction, uid: str) -> Link: ...

    def outgoing(self, tx: Transaction, uid: str) -> list[LinkView]: ...

    def incoming(self, tx: Transaction, uid: str) -> list[LinkView]: ...


class Projects(Protocol):
    """Lesender Zugriff auf die Projekte für andere Plugins."""

    def get(self, tx: Transaction, uid: str) -> Project | None: ...

    def list(self, tx: Transaction) -> list[Project]: ...


class ProjectStore(Protocol):
    def list(self, tx: Transaction, *, include_deleted: bool = False) -> list[Project]: ...

    def get(self, tx: Transaction, uid: str) -> Project | None: ...

    def name_taken(self, tx: Transaction, name: str, except_uid: str | None = None) -> bool: ...

    def insert(self, tx: Transaction, project: Project) -> None: ...

    def update(self, tx: Transaction, project: Project, expected_revision: int) -> Project:
        """Schreibt die Felder und erhöht die `revision`; `version_conflict`, wenn sie nicht `expected_revision` ist."""
        ...

    def set_positions(self, tx: Transaction, uids: Sequence[str]) -> None: ...

    def delete(self, tx: Transaction, uid: str) -> None: ...

    def count_elements(self, tx: Transaction, project_uid: str, *, include_deleted: bool) -> int: ...

    def mark_elements_deleted(self, tx: Transaction, project_uid: str, at: datetime) -> int: ...


class ElementStore(Protocol):
    def kind_prefix(self, tx: Transaction, kind: str) -> str | None: ...

    def upsert_kinds(self, tx: Transaction, owner: str, kinds: Sequence[ElementKind]) -> None: ...

    def next_number(self, tx: Transaction, project_uid: str, prefix: str) -> int:
        """Zählt den Zähler des Projekts und Präfixes hoch und gibt den neuen Wert zurück (nie rückwärts)."""
        ...

    def insert(self, tx: Transaction, element: Element) -> None: ...

    def add_history(self, tx: Transaction, project_uid: str, label: str, element_uid: str) -> None: ...

    def get(self, tx: Transaction, uid: str) -> Element | None: ...

    def find_uid_by_label(self, tx: Transaction, project_uid: str, label: str) -> str | None: ...

    def set_kind_and_label(self, tx: Transaction, uid: str, kind: str, label: str, now: datetime) -> None:
        """Ändert Typ und Label und erhöht die `revision`."""
        ...

    def bump_revision(self, tx: Transaction, uid: str, expected: int, now: datetime) -> int: ...

    def set_deleted(self, tx: Transaction, uid: str, at: datetime | None, now: datetime) -> None: ...

    def set_title(self, tx: Transaction, uid: str, title: str, now: datetime) -> None: ...

    def search(self, tx: Transaction, query: str, limit: int) -> list[Element]: ...

    def list_deleted(self, tx: Transaction, project_uids: Sequence[str] | None, query: str) -> list[Element]: ...

    def raise_counter(self, tx: Transaction, project_uid: str, prefix: str, number: int) -> None: ...

    def delete(self, tx: Transaction, uid: str) -> None: ...


class LinkStore(Protocol):
    def insert(self, tx: Transaction, link: Link) -> None: ...

    def get(self, tx: Transaction, uid: str) -> Link | None: ...

    def find(self, tx: Transaction, from_uid: str, to_uid: str, role: str) -> Link | None: ...

    def delete(self, tx: Transaction, uid: str) -> None: ...

    def outgoing(self, tx: Transaction, uid: str) -> list[Link]: ...

    def incoming(self, tx: Transaction, uid: str) -> list[Link]: ...

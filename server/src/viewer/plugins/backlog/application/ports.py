"""Ports des Plugins `backlog`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from viewer.core.application.ports import Transaction
from viewer.plugins.backlog.domain.model import Item


class ItemRepository(Protocol):
    def insert(self, tx: Transaction, item: Item) -> None:
        """Legt die Zeilen von Item, Bereich (falls neu) und Abhängigkeiten an; das Register-Element gibt es schon."""
        ...

    def get(self, tx: Transaction, uid: str) -> Item | None: ...

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Item]:
        """Items der Projekte (alle, wenn `None`) in der Reihenfolge Projekt, Label."""
        ...

    def children(self, tx: Transaction, uid: str) -> list[Item]:
        """Direkte Kinder, gelöschte eingeschlossen, nach Position und Label."""
        ...

    def delete(self, tx: Transaction, uid: str) -> None:
        """Entfernt die Zeilen des Items und seine Abhängigkeiten (in beide Richtungen)."""
        ...

    def update(self, tx: Transaction, item: Item) -> None:
        """Schreibt alle änderbaren Felder (Typ, Bereich, Parent, Abhängigkeiten …); die Revision hat das Register."""
        ...

    def area_names(self, tx: Transaction, project_uid: str) -> list[str]: ...

    def siblings(self, tx: Transaction, project_uid: str, parent_uid: str | None) -> list[Item]:
        """Nicht gelöschte Items unter einem Parent (oder die Wurzeln), nach Position und Label."""
        ...

    def set_positions(self, tx: Transaction, uids: Sequence[str]) -> None: ...


@dataclass(frozen=True)
class Document:
    """Ein Dokument eines Items; `revision` ist seine Version."""

    item_uid: str
    name: str
    kind: str
    content: str
    revision: int
    updated_at: datetime


class DocumentRepository(Protocol):
    def list_for(self, tx: Transaction, item_uid: str) -> list[Document]:
        """Die Dokumente des Items nach Art (Notizen zuerst) und Name, ohne Inhalt zu laden ist nicht nötig."""
        ...

    def get(self, tx: Transaction, item_uid: str, name: str) -> Document | None: ...

    def insert(self, tx: Transaction, document: Document) -> None: ...

    def update(self, tx: Transaction, item_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        """Ersetzt den Inhalt, wenn die Revision `expected` ist (sonst `version_conflict`); gibt die neue zurück."""
        ...

    def rename(self, tx: Transaction, item_uid: str, old: str, new: str) -> None: ...

    def delete(self, tx: Transaction, item_uid: str, name: str) -> None: ...

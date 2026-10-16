"""Ports des Plugins `backlog`."""

from __future__ import annotations

from collections.abc import Sequence
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

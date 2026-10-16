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

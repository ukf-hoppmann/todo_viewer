"""Ports des Plugins `mindmap`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from viewer.core.application.ports import Transaction
from viewer.plugins.mindmap.domain.model import Node, Placement, Tree


class MindmapRepository(Protocol):
    def tree_of_project(self, tx: Transaction, project_uid: str) -> Tree | None:
        """Der Projektbaum des Projekts, falls es ihn schon gibt."""
        ...

    def get_tree(self, tx: Transaction, uid: str) -> Tree | None: ...

    def insert_tree(self, tx: Transaction, tree: Tree) -> None: ...

    def insert_node(self, tx: Transaction, node: Node) -> None: ...

    def update_node(self, tx: Transaction, node: Node) -> None:
        """Schreibt Titel, Text und Markierung; die Revision hat das Register."""
        ...

    def get_node(self, tx: Transaction, uid: str) -> Node | None: ...

    def nodes_in_tree(self, tx: Transaction, tree_uid: str, *, include_deleted: bool = False) -> list[Node]: ...

    def placements(self, tx: Transaction, tree_uid: str) -> list[Placement]:
        """Alle Platzierungen des Baums, auch die gelöschter Knoten (sie behalten ihre Lage bis zum Löschen)."""
        ...

    def placements_of(self, tx: Transaction, node_uid: str) -> list[Placement]: ...

    def upsert_placements(self, tx: Transaction, placements: Sequence[Placement]) -> None: ...

    def child_uids(self, tx: Transaction, node_uid: str) -> list[str]:
        """Die Knoten direkt unter dem Knoten in allen Bäumen, gelöschte eingeschlossen."""
        ...

    def delete_node(self, tx: Transaction, uid: str) -> None:
        """Entfernt den Knoten und seine Platzierungen (Papierkorb: endgültiges Löschen)."""
        ...


@dataclass(frozen=True)
class Document:
    """Ein Dokument eines Knotens; `revision` ist seine Version."""

    node_uid: str
    name: str
    kind: str
    content: str
    revision: int
    updated_at: datetime


class DocumentRepository(Protocol):
    def list_for(self, tx: Transaction, node_uid: str) -> list[Document]:
        """Die Dokumente des Knotens, die Notiz zuerst."""
        ...

    def names_of(self, tx: Transaction, node_uids: Sequence[str]) -> dict[str, list[str]]:
        """Die Namen der Dokumente je Knoten (nur Knoten mit Dokumenten), die Notiz zuerst."""
        ...

    def get(self, tx: Transaction, node_uid: str, name: str) -> Document | None: ...

    def insert(self, tx: Transaction, document: Document) -> None: ...

    def update(self, tx: Transaction, node_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        """Ersetzt den Inhalt, wenn die Revision `expected` ist (sonst `version_conflict`); gibt die neue zurück."""
        ...


@dataclass(frozen=True)
class BacklogItem:
    """Ein Item des Backlogs, so viel die Mindmap davon braucht."""

    uid: str
    project_uid: str
    label: str
    type: str
    title: str
    status: str
    parent_uid: str | None
    deleted: bool


class BacklogItems(Protocol):
    """Lesender Zugriff auf die Items des Plugins `backlog` (Adapter in `infrastructure/backlog_gateway.py`)."""

    def list_items(self, tx: Transaction, project_uid: str) -> list[BacklogItem]:
        """Alle Items des Projekts, auch die im Papierkorb."""
        ...

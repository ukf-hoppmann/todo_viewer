"""Ports des Plugins `mindmap`."""

from __future__ import annotations

from collections.abc import Sequence
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
        """Schreibt Titel und Text; die Revision hat das Register."""
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

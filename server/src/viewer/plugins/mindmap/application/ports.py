"""Ports des Plugins `mindmap`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from viewer.core.application.ports import Transaction
from viewer.plugins.mindmap.domain.model import Node, Placement, RemovedPlacement, Tree


class MindmapRepository(Protocol):
    def tree_of_project(self, tx: Transaction, project_uid: str) -> Tree | None:
        """Der Projektbaum des Projekts, falls es ihn schon gibt."""
        ...

    def get_tree(self, tx: Transaction, uid: str) -> Tree | None:
        """Der Baum, auch wenn er im Papierkorb liegt."""
        ...

    def insert_tree(self, tx: Transaction, tree: Tree) -> None: ...

    def free_maps(self, tx: Transaction, project_uid: str) -> list[Tree]:
        """Die freien Maps des Projekts außerhalb des Papierkorbs, in der Reihenfolge des Anlegens."""
        ...

    def deleted_maps(self, tx: Transaction, project_uids: Sequence[str] | None) -> list[Tree]:
        """Die freien Maps im Papierkorb (aller oder der genannten Projekte)."""
        ...

    def rename_tree(self, tx: Transaction, uid: str, name: str, expected: int) -> int:
        """Setzt den Namen, wenn die Revision `expected` ist (sonst `version_conflict`); gibt die neue zurück."""
        ...

    def set_tree_deleted(self, tx: Transaction, uid: str, at: datetime | None, expected: int | None = None) -> int:
        """Legt die Map in den Papierkorb (`at`) oder holt sie zurück (`None`) und erhöht die Revision; mit
        `expected` wird sie geprüft (sonst `version_conflict`). Gibt die neue Revision zurück."""
        ...

    def delete_tree(self, tx: Transaction, uid: str) -> None:
        """Entfernt den Baum und seine Platzierungen (die Knoten räumt der Aufrufer ab)."""
        ...

    def node_count(self, tx: Transaction, tree_uid: str) -> int:
        """Die Knoten des Baums außerhalb des Papierkorbs."""
        ...

    def shared_count(self, tx: Transaction, tree_uid: str) -> int:
        """Die Knoten des Baums außerhalb des Papierkorbs, die auch in einem anderen Baum stehen."""
        ...

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
        """Die Knoten direkt unter dem Knoten, die ausschließlich unter ihm stehen (in allen Bäumen), gelöschte
        eingeschlossen. Ein Knoten mit einer Platzierung unter einem anderen Parent oder unter der Wurzel gehört dem
        Papierkorb des Parents nicht mit."""
        ...

    def delete_placements(self, tx: Transaction, placements: Sequence[Placement]) -> None:
        """Entfernt genau diese Platzierungen (Kinder vor ihren Eltern übergeben)."""
        ...

    def mark_removed(self, tx: Transaction, placements: Sequence[Placement], root_uid: str) -> None:
        """Merkt die Platzierungen als entfernt (`TASK-066`): Baum, Parent und Stelle bleiben gespeichert, alle Abfragen
        übergehen sie. `root_uid` nennt den Knoten, dessen Ast mit ihnen entfernt wurde (die Gruppe)."""
        ...

    def removed_placements(self, tx: Transaction, tree_uid: str) -> list[RemovedPlacement]:
        """Die gemerkten, entfernten Platzierungen des Baums."""
        ...

    def removed_placements_of(self, tx: Transaction, node_uid: str) -> list[RemovedPlacement]:
        """Die gemerkten, entfernten Platzierungen des Knotens, eine je Baum."""
        ...

    def live_trees_of(self, tx: Transaction, node_uids: Sequence[str]) -> dict[str, set[str]]:
        """Je Knoten die Bäume außerhalb des Papierkorbs, in denen er steht."""
        ...

    def live_tree_counts(self, tx: Transaction, tree_uid: str) -> dict[str, int]:
        """Je Knoten des Baums die Zahl der Bäume außerhalb des Papierkorbs, in denen er steht (mindestens 1, wenn der
        Baum selbst lebt)."""
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

    def delete(self, tx: Transaction, node_uid: str, name: str) -> None:
        """Entfernt das Dokument endgültig (nur der Sync tut das, nach einer Entscheidung des Owners)."""
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
    #: Die `uid`s der Items, die dieses Item braucht.
    dependencies: tuple[str, ...] = ()


class BacklogItems(Protocol):
    """Lesender Zugriff auf die Items des Plugins `backlog` (Adapter in `infrastructure/backlog_gateway.py`)."""

    def list_items(self, tx: Transaction, project_uid: str) -> list[BacklogItem]:
        """Alle Items des Projekts, auch die im Papierkorb."""
        ...


@dataclass(frozen=True)
class CreatedElement:
    """Ein neu angelegtes Item oder Memo (`title` ist bei Memos die Zusammenfassung)."""

    uid: str
    label: str
    title: str
    type: str | None = None


class BacklogWriter(Protocol):
    """Anlegen eines Items im Plugin `backlog` (Adapter in `infrastructure/backlog_gateway.py`)."""

    def create_item(self, project_uid: str, type_: str, fields: dict[str, Any]) -> CreatedElement: ...


class MemoWriter(Protocol):
    """Anlegen eines Memos im Plugin `memos` (Adapter in `infrastructure/memo_gateway.py`)."""

    def create_memo(self, project_uid: str, fields: dict[str, Any]) -> CreatedElement: ...


class NodeSource(Protocol):
    """Der Knoten, aus dem etwas entsteht: lebend und, falls ein Projekt genannt ist, aus diesem."""

    def node_for_creation(self, ref: str, project_uid: str | None) -> Node: ...


class NodeAssigner(Protocol):
    """Anhängen des Angelegten an den Knoten (`AssignmentService`)."""

    def assign_item(self, item_ref: str, node_ref: str, project_uid: str | None, replace: bool) -> Node: ...

    def link_memo(self, memo_ref: str, node_ref: str, project_uid: str | None) -> Node: ...


@dataclass(frozen=True)
class BacklogProblem:
    """Ein Problem des Backlogs an einem geplanten Item; `key` ist die uid des Knotens (`None`: ganzer Plan)."""

    key: str | None
    code: str
    message: str
    details: dict[str, Any]


class BacklogChecker(Protocol):
    """Nicht schreibende Prüfung geplanter Items mit den Regeln des Backlogs (Adapter in
    `infrastructure/backlog_gateway.py`). `planned` sind `domain.transfer.PlannedItem`."""

    def check_new_items(self, project_uid: str, planned: Sequence[Any]) -> list[BacklogProblem]: ...


class BranchSource(Protocol):
    """Der Ast, der überführt wird: der Knoten zuerst, dann seine lebenden Nachkommen."""

    def branch_of(self, ref: str, project_uid: str | None, tree_uid: str | None) -> list[Node]: ...

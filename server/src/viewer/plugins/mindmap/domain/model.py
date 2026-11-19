"""Mindmap: Knoten, Bäume und Platzierungen.

Ein Knoten ist ein Thema mit Titel und optionalem Text. Wo er steht, sagt allein seine Platzierung in einem Baum
(Knoten, Parent, Stelle); das Knoten selbst hat kein Parent-Feld. So kann ein Knoten später in mehreren Bäumen stehen,
ohne dass der Knoten umgebaut wird. In einem Baum steht ein Knoten höchstens einmal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from viewer.core.domain.errors import DomainError

#: Der Baum eines Projekts; das Projekt ist seine Wurzel. Einmalig je Projekt und nicht löschbar.
TREE_PROJECT = "project"
#: Eine freie Map zum Brainstormen (`TASK-062`): beliebig viele je Projekt, mit Namen, in den Papierkorb legbar.
TREE_FREE = "free"
TREE_KINDS = (TREE_PROJECT, TREE_FREE)
#: Längster Name einer freien Map.
MAP_NAME_MAX = 100

#: Die Markierungen eines Knotens (`TASK-065`): feste Werte, keine Freitexte. Ein Knoten trägt höchstens eine; ohne
#: Markierung steht `None`. Sie ändert weder Summen noch Zustand und gilt nur für den Knoten selbst.
MARK_DISCARDED = "discarded"
MARK_LATER = "later"
NODE_MARKS = (MARK_DISCARDED, MARK_LATER)


class MindmapViolation(DomainError):
    """Eine Regel der Mindmap ist verletzt; `code` nennt sie."""

    def __init__(self, code: str, message: str, **details: object) -> None:
        super().__init__(message, code=code, details=dict(details))


@dataclass(frozen=True)
class Node:
    """Ein Knoten. `uid`, `label`, `revision` und `deleted_at` gehören dem Register von `workspace`."""

    uid: str
    project_uid: str
    label: str
    title: str
    text: str | None
    revision: int
    deleted_at: datetime | None = None
    #: Eine der `NODE_MARKS` oder `None`.
    mark: str | None = None


@dataclass(frozen=True)
class Tree:
    """Ein Baum gehört zu genau einem Projekt. Der Projektbaum hat keinen Namen (er heißt wie das Projekt); eine freie
    Map hat einen. `revision` ist das Versionstoken für Umbenennen und Löschen; `deleted_at` gesetzt heißt: die Map
    liegt im Papierkorb."""

    uid: str
    project_uid: str
    kind: str = TREE_PROJECT
    name: str | None = None
    revision: int = 1
    deleted_at: datetime | None = None


@dataclass(frozen=True)
class Placement:
    """Die Lage eines Knotens in einem Baum. `parent_uid` ist ein Knoten desselben Baums, `None` steht unter der
    Wurzel (dem Projekt). `position` ordnet die Geschwister."""

    tree_uid: str
    node_uid: str
    parent_uid: str | None
    position: int

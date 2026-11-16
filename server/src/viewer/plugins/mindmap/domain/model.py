"""Mindmap: Knoten, Bäume und Platzierungen.

Ein Knoten ist ein Thema mit Titel und optionalem Text. Wo er steht, sagt allein seine Platzierung in einem Baum
(Knoten, Parent, Stelle); das Knoten selbst hat kein Parent-Feld. So kann ein Knoten später in mehreren Bäumen stehen,
ohne dass der Knoten umgebaut wird. In einem Baum steht ein Knoten höchstens einmal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from viewer.core.domain.errors import DomainError

#: Der Baum eines Projekts; das Projekt ist seine Wurzel. Weitere Arten (freie Maps) kommen mit `STORY-102`.
TREE_PROJECT = "project"
TREE_KINDS = (TREE_PROJECT,)


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


@dataclass(frozen=True)
class Tree:
    """Ein Baum gehört zu genau einem Projekt."""

    uid: str
    project_uid: str
    kind: str = TREE_PROJECT


@dataclass(frozen=True)
class Placement:
    """Die Lage eines Knotens in einem Baum. `parent_uid` ist ein Knoten desselben Baums, `None` steht unter der
    Wurzel (dem Projekt). `position` ordnet die Geschwister."""

    tree_uid: str
    node_uid: str
    parent_uid: str | None
    position: int

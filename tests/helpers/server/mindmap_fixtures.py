"""Synthetische Bäume für Tests der Domäne des Plugins `mindmap`."""

from __future__ import annotations

from viewer.plugins.mindmap.domain.model import Placement

TREE = "tree-1"


def placed(*rows: tuple[str, str | None, int]) -> list[Placement]:
    """Platzierungen in `TREE` aus `(Knoten, Parent, Stelle)`."""
    return [Placement(TREE, node, parent, position) for node, parent, position in rows]


def sample() -> list[Placement]:
    """a (b (d), c), e"""
    return placed(("a", None, 0), ("e", None, 1), ("b", "a", 0), ("c", "a", 1), ("d", "b", 0))

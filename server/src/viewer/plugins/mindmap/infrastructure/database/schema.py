"""Migrationen von `mindmap`: Tabellen mit Präfix `mindmap_`, nur vorwärts."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.mindmap.domain.model import TREE_KINDS


def _v1(connection: Any) -> None:
    """Bäume, Knoten und Platzierungen. Die Lage eines Knotens steht nur in `mindmap_placements`: ein Knoten kann
    später in mehreren Bäumen stehen, ein Baum hat Platz für weitere Arten (freie Maps), ohne dass Tabellen umgebaut
    werden."""
    for statement in (
        "CREATE TABLE mindmap_tree_kinds (code TEXT PRIMARY KEY)",
        """CREATE TABLE mindmap_trees (
            uid TEXT PRIMARY KEY,
            project_uid TEXT NOT NULL REFERENCES workspace_projects(uid) ON DELETE CASCADE,
            kind TEXT NOT NULL REFERENCES mindmap_tree_kinds(code)
        )""",
        # Der Projektbaum ist einmalig je Projekt; freie Maps dürfen später mehrfach vorkommen.
        "CREATE UNIQUE INDEX mindmap_trees_project ON mindmap_trees(project_uid) WHERE kind = 'project'",
        """CREATE TABLE mindmap_nodes (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            title TEXT NOT NULL,
            text TEXT
        )""",
        # Höchstens eine Platzierung je Knoten und Baum; der Parent steht im selben Baum.
        """CREATE TABLE mindmap_placements (
            tree_uid TEXT NOT NULL REFERENCES mindmap_trees(uid) ON DELETE CASCADE,
            node_uid TEXT NOT NULL REFERENCES mindmap_nodes(uid),
            parent_uid TEXT,
            position INTEGER NOT NULL CHECK (position >= 0),
            PRIMARY KEY (tree_uid, node_uid),
            CHECK (parent_uid IS NULL OR parent_uid <> node_uid),
            FOREIGN KEY (tree_uid, parent_uid) REFERENCES mindmap_placements(tree_uid, node_uid)
        )""",
        "CREATE INDEX mindmap_placements_parent ON mindmap_placements(tree_uid, parent_uid, position)",
        "CREATE INDEX mindmap_placements_node ON mindmap_placements(node_uid)",
    ):
        connection.exec_driver_sql(statement)
    for code in TREE_KINDS:
        connection.execute(text("INSERT INTO mindmap_tree_kinds(code) VALUES (:c)"), {"c": code})


def _v2(connection: Any) -> None:
    """Dokumente eines Knotens (Notizen und Specs); die Art folgt aus dem Namen und dem Label des Knotens."""
    connection.exec_driver_sql(
        """CREATE TABLE mindmap_documents (
            node_uid TEXT NOT NULL REFERENCES mindmap_nodes(uid) ON DELETE CASCADE,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (node_uid, name)
        )"""
    )


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1), Migration(2, _v2))

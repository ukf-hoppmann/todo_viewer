"""Migrationen von `mindmap`: Tabellen mit Präfix `mindmap_`, nur vorwärts."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.mindmap.domain.model import NODE_MARKS


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
    for code in ("project",):  # fest: spätere Arten kommen mit eigener Migration
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


def _v3(connection: Any) -> None:
    """Markierungen „verworfen“ und „später“ (`TASK-065`): eine feste Liste und eine Spalte am Knoten; leer heißt
    „keine“. Bestehende Knoten behalten alles und tragen keine Markierung."""
    connection.exec_driver_sql("CREATE TABLE mindmap_marks (code TEXT PRIMARY KEY)")
    for code in NODE_MARKS:
        connection.execute(text("INSERT INTO mindmap_marks(code) VALUES (:c)"), {"c": code})
    connection.exec_driver_sql("ALTER TABLE mindmap_nodes ADD COLUMN mark TEXT REFERENCES mindmap_marks(code)")


def _v4(connection: Any) -> None:
    """Freie Maps (`TASK-062`): eine zweite Art Baum, mit Namen, Versionstoken und Papierkorb-Zeitpunkt. Der Projektbaum
    bleibt unbenannt und einmalig je Projekt (der Index aus Version 1 gilt nur für ihn)."""
    connection.execute(text("INSERT INTO mindmap_tree_kinds(code) VALUES ('free')"))
    for statement in (
        "ALTER TABLE mindmap_trees ADD COLUMN name TEXT",
        "ALTER TABLE mindmap_trees ADD COLUMN revision INTEGER NOT NULL DEFAULT 1",
        "ALTER TABLE mindmap_trees ADD COLUMN deleted_at TEXT",
        "CREATE INDEX mindmap_trees_by_project ON mindmap_trees(project_uid, kind)",
    ):
        connection.exec_driver_sql(statement)


def _v5(connection: Any) -> None:
    """Entfernte Platzierungen merken (`TASK-066`): `removed_root` nennt bei einer entfernten Platzierung den Knoten,
    dessen Ast mit ihr entfernt wurde (die Gruppe); leer heißt: die Platzierung gilt. Eine entfernte Platzierung
    behält Baum, Parent und Stelle. Der Parent darf später fehlen; deshalb entfällt der Fremdschlüssel auf die eigene
    Tabelle (die Regeln für gültige Platzierungen stehen in der Domäne). Die Tabelle wird dazu neu aufgebaut."""
    for statement in (
        """CREATE TABLE mindmap_placements_new (
            tree_uid TEXT NOT NULL REFERENCES mindmap_trees(uid) ON DELETE CASCADE,
            node_uid TEXT NOT NULL REFERENCES mindmap_nodes(uid),
            parent_uid TEXT,
            position INTEGER NOT NULL CHECK (position >= 0),
            removed_root TEXT,
            PRIMARY KEY (tree_uid, node_uid),
            CHECK (parent_uid IS NULL OR parent_uid <> node_uid)
        )""",
        "INSERT INTO mindmap_placements_new(tree_uid, node_uid, parent_uid, position) "
        "SELECT tree_uid, node_uid, parent_uid, position FROM mindmap_placements",
        "DROP TABLE mindmap_placements",
        "ALTER TABLE mindmap_placements_new RENAME TO mindmap_placements",
        "CREATE INDEX mindmap_placements_parent ON mindmap_placements(tree_uid, parent_uid, position)",
        "CREATE INDEX mindmap_placements_node ON mindmap_placements(node_uid)",
    ):
        connection.exec_driver_sql(statement)


MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, _v1),
    Migration(2, _v2),
    Migration(3, _v3),
    Migration(4, _v4),
    Migration(5, _v5),
)

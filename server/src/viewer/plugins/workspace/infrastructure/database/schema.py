"""Migrationen von `workspace`: Tabellen mit Präfix `workspace_`, nur vorwärts."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.workspace.domain.model import BUILTIN_PROJECT


def _v1(connection: Any) -> None:
    statements = (
        """CREATE TABLE workspace_projects (
            uid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mirror_folder TEXT,
            mirror_enabled INTEGER NOT NULL DEFAULT 0 CHECK (mirror_enabled IN (0, 1)),
            auto_sync INTEGER NOT NULL DEFAULT 0 CHECK (auto_sync IN (0, 1)),
            sync_direction TEXT NOT NULL DEFAULT 'both' CHECK (sync_direction IN ('both', 'to_files', 'to_database')),
            position INTEGER NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            deleted_at TEXT
        )""",
        # Ein entferntes Projekt gibt seinen Namen wieder frei.
        "CREATE UNIQUE INDEX workspace_projects_name ON workspace_projects(name) WHERE deleted_at IS NULL",
        """CREATE TABLE workspace_element_kinds (
            kind TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            label_prefix TEXT NOT NULL
        )""",
        """CREATE TABLE workspace_elements (
            uid TEXT PRIMARY KEY,
            project_uid TEXT NOT NULL REFERENCES workspace_projects(uid),
            kind TEXT NOT NULL REFERENCES workspace_element_kinds(kind),
            label TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT,
            UNIQUE (project_uid, label)
        )""",
        "CREATE INDEX workspace_elements_project ON workspace_elements(project_uid, kind)",
        """CREATE TABLE workspace_label_counters (
            project_uid TEXT NOT NULL REFERENCES workspace_projects(uid),
            prefix TEXT NOT NULL,
            last INTEGER NOT NULL,
            PRIMARY KEY (project_uid, prefix)
        )""",
        """CREATE TABLE workspace_label_history (
            project_uid TEXT NOT NULL REFERENCES workspace_projects(uid),
            label TEXT NOT NULL,
            element_uid TEXT NOT NULL REFERENCES workspace_elements(uid) ON DELETE CASCADE,
            PRIMARY KEY (project_uid, label)
        )""",
    )
    for statement in statements:
        connection.exec_driver_sql(statement)
    # Das eingebaute Projekt für alles ohne eigenes Projekt (`STORY-060`, Frage 2).
    connection.execute(
        text("INSERT INTO workspace_projects(uid, name, position, created_at) VALUES (:uid, :name, 0, :created_at)"),
        {"uid": str(uuid.uuid4()), "name": BUILTIN_PROJECT, "created_at": datetime.now(UTC).isoformat()},
    )


def _v2(connection: Any) -> None:
    """Anzeigetitel im Register (Suche, Verknüpfungen) und die Verknüpfungen."""
    statements = (
        "ALTER TABLE workspace_elements ADD COLUMN title TEXT NOT NULL DEFAULT ''",
        """CREATE TABLE workspace_links (
            uid TEXT PRIMARY KEY,
            from_uid TEXT NOT NULL REFERENCES workspace_elements(uid) ON DELETE CASCADE,
            to_uid TEXT NOT NULL REFERENCES workspace_elements(uid) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('reference', 'origin', 'trigger')),
            created_at TEXT NOT NULL,
            UNIQUE (from_uid, to_uid, role)
        )""",
        "CREATE INDEX workspace_links_to ON workspace_links(to_uid)",
    )
    for statement in statements:
        connection.exec_driver_sql(statement)


def _v3(connection: Any) -> None:
    """Die Rolle `node` (Mindmap: ein Knoten verknüpft ein Item oder Memo). SQLite ändert eine CHECK-Regel nur über
    eine neue Tabelle; die vorhandenen Verknüpfungen werden übernommen."""
    for statement in (
        "DROP INDEX workspace_links_to",
        "ALTER TABLE workspace_links RENAME TO workspace_links_v2",
        """CREATE TABLE workspace_links (
            uid TEXT PRIMARY KEY,
            from_uid TEXT NOT NULL REFERENCES workspace_elements(uid) ON DELETE CASCADE,
            to_uid TEXT NOT NULL REFERENCES workspace_elements(uid) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK (role IN ('reference', 'origin', 'trigger', 'node')),
            created_at TEXT NOT NULL,
            UNIQUE (from_uid, to_uid, role)
        )""",
        "INSERT INTO workspace_links(uid, from_uid, to_uid, role, created_at) "
        "SELECT uid, from_uid, to_uid, role, created_at FROM workspace_links_v2",
        "DROP TABLE workspace_links_v2",
        "CREATE INDEX workspace_links_to ON workspace_links(to_uid)",
    ):
        connection.exec_driver_sql(statement)


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1), Migration(2, _v2), Migration(3, _v3))

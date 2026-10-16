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


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1),)

"""Migrationen von `backlog`: feste Wertelisten als Nachschlagetabellen, Items, Bereiche, Abhängigkeiten."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.backlog.domain.model import FINAL_STATUSES, PRIORITIES, STATUSES, TYPES


def _v1(connection: Any) -> None:
    for statement in (
        "CREATE TABLE backlog_types (code TEXT PRIMARY KEY)",
        "CREATE TABLE backlog_statuses (code TEXT PRIMARY KEY, final INTEGER NOT NULL CHECK (final IN (0, 1)))",
        "CREATE TABLE backlog_priorities (code TEXT PRIMARY KEY, rank INTEGER NOT NULL UNIQUE)",
        """CREATE TABLE backlog_areas (
            uid TEXT PRIMARY KEY,
            project_uid TEXT NOT NULL REFERENCES workspace_projects(uid),
            name TEXT NOT NULL,
            UNIQUE (project_uid, name)
        )""",
        """CREATE TABLE backlog_items (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            type TEXT NOT NULL REFERENCES backlog_types(code),
            title TEXT NOT NULL,
            status TEXT NOT NULL REFERENCES backlog_statuses(code),
            priority TEXT NOT NULL REFERENCES backlog_priorities(code),
            area_uid TEXT REFERENCES backlog_areas(uid),
            parent_uid TEXT REFERENCES backlog_items(uid),
            required_for_parent INTEGER CHECK (required_for_parent IN (0, 1)),
            goal TEXT,
            completion_criteria TEXT,
            summary TEXT,
            resolution TEXT,
            created TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0
        )""",
        "CREATE INDEX backlog_items_parent ON backlog_items(parent_uid)",
        """CREATE TABLE backlog_dependencies (
            item_uid TEXT NOT NULL REFERENCES backlog_items(uid) ON DELETE CASCADE,
            depends_on_uid TEXT NOT NULL REFERENCES backlog_items(uid) ON DELETE CASCADE,
            PRIMARY KEY (item_uid, depends_on_uid),
            CHECK (item_uid <> depends_on_uid)
        )""",
        "CREATE INDEX backlog_dependencies_target ON backlog_dependencies(depends_on_uid)",
    ):
        connection.exec_driver_sql(statement)
    for code in TYPES:
        connection.execute(text("INSERT INTO backlog_types(code) VALUES (:c)"), {"c": code})
    for code in STATUSES:
        connection.execute(
            text("INSERT INTO backlog_statuses(code, final) VALUES (:c, :f)"),
            {"c": code, "f": 1 if code in FINAL_STATUSES else 0},
        )
    for code, rank in PRIORITIES.items():
        connection.execute(text("INSERT INTO backlog_priorities(code, rank) VALUES (:c, :r)"), {"c": code, "r": rank})


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1),)

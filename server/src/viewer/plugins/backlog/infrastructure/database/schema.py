"""Migrationen von `backlog`: feste Wertelisten als Nachschlagetabellen, Items, Bereiche, Abhängigkeiten."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.backlog.domain.model import FINAL_STATUSES, PRIORITIES, STATUSES, TYPES
from viewer.plugins.backlog.domain.notes import split_lossless


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


def _v2(connection: Any) -> None:
    """Notizen und Specs der Items."""
    connection.exec_driver_sql(
        """CREATE TABLE backlog_documents (
            item_uid TEXT NOT NULL REFERENCES backlog_items(uid) ON DELETE CASCADE,
            name TEXT NOT NULL,
            kind TEXT NOT NULL CHECK (kind IN ('notes', 'spec')),
            content TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (item_uid, name)
        )"""
    )


def _v3(connection: Any) -> None:
    """Notes der Items in eigenen Tabellen: Vorspann, Kopf mit Stempel und Protokolleinträge. Die Notes-Dokumente aus
    `backlog_documents` werden zerlegt übernommen (ohne Textverlust, notfalls alles als Vorspann); dort bleiben nur
    die Specs."""
    for statement in (
        """CREATE TABLE backlog_notes (
            item_uid TEXT PRIMARY KEY REFERENCES backlog_items(uid) ON DELETE CASCADE,
            name TEXT NOT NULL,
            preamble TEXT NOT NULL,
            state TEXT NOT NULL,
            stamp_day TEXT,
            stamp_topic TEXT,
            stamp_checksum TEXT,
            state_revision INTEGER NOT NULL DEFAULT 1,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            CHECK ((stamp_day IS NULL) = (stamp_topic IS NULL) AND (stamp_day IS NULL) = (stamp_checksum IS NULL))
        )""",
        """CREATE TABLE backlog_notes_entries (
            item_uid TEXT NOT NULL REFERENCES backlog_notes(item_uid) ON DELETE CASCADE,
            position INTEGER NOT NULL,
            day TEXT NOT NULL,
            topic TEXT NOT NULL,
            body TEXT NOT NULL,
            PRIMARY KEY (item_uid, position)
        )""",
    ):
        connection.exec_driver_sql(statement)
    rows = connection.execute(
        text("SELECT item_uid, name, content, revision, updated_at FROM backlog_documents WHERE kind = 'notes'")
    ).all()
    for row in rows:
        parts = split_lossless(row.content)
        stamp = parts.stamp
        connection.execute(
            text(
                "INSERT INTO backlog_notes(item_uid, name, preamble, state, stamp_day, stamp_topic, stamp_checksum, "
                "state_revision, revision, updated_at) VALUES (:u, :n, :p, :s, :sd, :st, :sc, 1, :r, :t)"
            ),
            {
                "u": row.item_uid,
                "n": row.name,
                "p": parts.preamble,
                "s": parts.state,
                "sd": stamp.day if stamp else None,
                "st": stamp.topic if stamp else None,
                "sc": stamp.checksum if stamp else None,
                "r": row.revision,
                "t": row.updated_at,
            },
        )
        for position, entry in enumerate(parts.entries):
            connection.execute(
                text(
                    "INSERT INTO backlog_notes_entries(item_uid, position, day, topic, body) "
                    "VALUES (:u, :i, :d, :o, :b)"
                ),
                {"u": row.item_uid, "i": position, "d": entry.day, "o": entry.topic, "b": entry.body},
            )
    connection.exec_driver_sql("DELETE FROM backlog_documents WHERE kind = 'notes'")


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1), Migration(2, _v2), Migration(3, _v3))

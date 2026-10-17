"""Migrationen von `notes`: feste Status, Topics, Notes, Dokumente und Einstellungen."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.notes.domain.model import STATUSES


def _v1(connection: Any) -> None:
    for statement in (
        "CREATE TABLE notes_statuses (code TEXT PRIMARY KEY)",
        """CREATE TABLE notes_topics (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            name TEXT NOT NULL,
            parent_uid TEXT REFERENCES notes_topics(uid),
            due_at TEXT,
            archived_at TEXT,
            system INTEGER NOT NULL DEFAULT 0 CHECK (system IN (0, 1))
        )""",
        "CREATE INDEX notes_topics_parent ON notes_topics(parent_uid)",
        """CREATE TABLE notes_notes (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            summary TEXT NOT NULL,
            body TEXT,
            status TEXT NOT NULL REFERENCES notes_statuses(code),
            topic_uid TEXT REFERENCES notes_topics(uid),
            review_at TEXT,
            trigger_mode TEXT NOT NULL DEFAULT 'any' CHECK (trigger_mode IN ('any', 'all')),
            archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1))
        )""",
        "CREATE INDEX notes_notes_topic ON notes_notes(topic_uid)",
        """CREATE TABLE notes_documents (
            note_uid TEXT NOT NULL REFERENCES notes_notes(uid) ON DELETE CASCADE,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (note_uid, name)
        )""",
        "CREATE TABLE notes_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    ):
        connection.exec_driver_sql(statement)
    for code in STATUSES:
        connection.execute(text("INSERT INTO notes_statuses(code) VALUES (:c)"), {"c": code})


def _v2(connection: Any) -> None:
    """Auslöser und Hinweise. `target_uid`, `subject_uid` und `source_uid` verweisen auf Elemente verschiedener
    Plugins und haben deshalb keinen Fremdschlüssel; ein endgültig gelöschtes Item lässt seine Auslöser nur nie mehr
    feuern."""
    for statement in (
        """CREATE TABLE notes_triggers (
            uid TEXT PRIMARY KEY,
            note_uid TEXT NOT NULL REFERENCES notes_notes(uid) ON DELETE CASCADE,
            kind TEXT NOT NULL CHECK (kind IN ('event', 'topic_date')),
            target_uid TEXT,
            status TEXT,
            fired_at TEXT,
            already_met INTEGER NOT NULL DEFAULT 0 CHECK (already_met IN (0, 1)),
            link_uid TEXT
        )""",
        "CREATE INDEX notes_triggers_note ON notes_triggers(note_uid)",
        "CREATE INDEX notes_triggers_target ON notes_triggers(target_uid)",
        """CREATE TABLE notes_notices (
            uid TEXT PRIMARY KEY,
            side TEXT NOT NULL CHECK (side IN ('note', 'item')),
            subject_uid TEXT NOT NULL,
            source_uid TEXT NOT NULL,
            kind TEXT NOT NULL,
            created_at TEXT NOT NULL,
            decided_at TEXT,
            decision TEXT
        )""",
        "CREATE INDEX notes_notices_subject ON notes_notices(subject_uid)",
    ):
        connection.exec_driver_sql(statement)


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1), Migration(2, _v2))

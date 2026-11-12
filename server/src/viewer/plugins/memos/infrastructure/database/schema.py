"""Migrationen von `memos`: feste Status, Topics, Memos, Dokumente und Einstellungen.

Das Plugin hieß bis Version 2 `notes` (Memos hießen Notes, Hinweise Notices). Version 1 und 2 legen die Tabellen gleich
unter dem neuen Namen an; Version 3 nimmt eine Datenbank aus der Zeit von `notes` auf (nur diese hat `notes_*`)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.memos.domain.model import STATUSES


def _v1(connection: Any) -> None:
    for statement in (
        "CREATE TABLE memos_statuses (code TEXT PRIMARY KEY)",
        """CREATE TABLE memos_topics (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            name TEXT NOT NULL,
            parent_uid TEXT REFERENCES memos_topics(uid),
            due_at TEXT,
            archived_at TEXT,
            system INTEGER NOT NULL DEFAULT 0 CHECK (system IN (0, 1))
        )""",
        "CREATE INDEX memos_topics_parent ON memos_topics(parent_uid)",
        """CREATE TABLE memos_memos (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            summary TEXT NOT NULL,
            body TEXT,
            status TEXT NOT NULL REFERENCES memos_statuses(code),
            topic_uid TEXT REFERENCES memos_topics(uid),
            review_at TEXT,
            trigger_mode TEXT NOT NULL DEFAULT 'any' CHECK (trigger_mode IN ('any', 'all')),
            archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1))
        )""",
        "CREATE INDEX memos_memos_topic ON memos_memos(topic_uid)",
        """CREATE TABLE memos_documents (
            memo_uid TEXT NOT NULL REFERENCES memos_memos(uid) ON DELETE CASCADE,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (memo_uid, name)
        )""",
        "CREATE TABLE memos_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    ):
        connection.exec_driver_sql(statement)
    for code in STATUSES:
        connection.execute(text("INSERT INTO memos_statuses(code) VALUES (:c)"), {"c": code})


def _v2(connection: Any) -> None:
    """Auslöser und Hinweise. `target_uid`, `subject_uid` und `source_uid` verweisen auf Elemente verschiedener
    Plugins und haben deshalb keinen Fremdschlüssel; ein endgültig gelöschtes Item lässt seine Auslöser nur nie mehr
    feuern."""
    for statement in (
        """CREATE TABLE memos_triggers (
            uid TEXT PRIMARY KEY,
            memo_uid TEXT NOT NULL REFERENCES memos_memos(uid) ON DELETE CASCADE,
            kind TEXT NOT NULL CHECK (kind IN ('event', 'topic_date')),
            target_uid TEXT,
            status TEXT,
            fired_at TEXT,
            already_met INTEGER NOT NULL DEFAULT 0 CHECK (already_met IN (0, 1)),
            link_uid TEXT
        )""",
        "CREATE INDEX memos_triggers_memo ON memos_triggers(memo_uid)",
        "CREATE INDEX memos_triggers_target ON memos_triggers(target_uid)",
        """CREATE TABLE memos_hints (
            uid TEXT PRIMARY KEY,
            side TEXT NOT NULL CHECK (side IN ('memo', 'item')),
            subject_uid TEXT NOT NULL,
            source_uid TEXT NOT NULL,
            kind TEXT NOT NULL,
            created_at TEXT NOT NULL,
            decided_at TEXT,
            decision TEXT
        )""",
        "CREATE INDEX memos_hints_subject ON memos_hints(subject_uid)",
    ):
        connection.exec_driver_sql(statement)


_OLD_TABLES = (
    "notes_notices",
    "notes_triggers",
    "notes_documents",
    "notes_notes",
    "notes_topics",
    "notes_settings",
    "notes_statuses",
)


def _v3(connection: Any) -> None:
    """Übernimmt die Daten aus `notes_*` (Plugin `notes`), benennt Elementtyp und Labels (`NOTE-001` → `MEMO-001`)
    um und entfernt die alten Tabellen. Fehlt `notes_notes`, ist die Datenbank neu und nichts zu tun."""
    if not connection.exec_driver_sql("SELECT 1 FROM sqlite_master WHERE name = 'notes_notes'").first():
        return
    _v1(connection)
    _v2(connection)
    for statement in (
        "DELETE FROM memos_statuses",
        "INSERT INTO memos_statuses(code) SELECT code FROM notes_statuses",
        "INSERT INTO memos_settings(key, value) SELECT key, value FROM notes_settings",
        "INSERT INTO memos_topics(uid, name, parent_uid, due_at, archived_at, system) "
        "SELECT uid, name, parent_uid, due_at, archived_at, system FROM notes_topics",
        "INSERT INTO memos_memos(uid, summary, body, status, topic_uid, review_at, trigger_mode, archived) "
        "SELECT uid, summary, body, status, topic_uid, review_at, trigger_mode, archived FROM notes_notes",
        "INSERT INTO memos_documents(memo_uid, name, content, revision, updated_at) "
        "SELECT note_uid, replace(name, 'NOTE-', 'MEMO-'), content, revision, updated_at FROM notes_documents",
        "INSERT INTO memos_triggers(uid, memo_uid, kind, target_uid, status, fired_at, already_met, link_uid) "
        "SELECT uid, note_uid, kind, target_uid, status, fired_at, already_met, link_uid FROM notes_triggers",
        "INSERT INTO memos_hints(uid, side, subject_uid, source_uid, kind, created_at, decided_at, decision) "
        "SELECT uid, CASE side WHEN 'note' THEN 'memo' ELSE side END, subject_uid, source_uid, "
        "CASE kind WHEN 'note_dropped' THEN 'memo_dropped' WHEN 'note_promoted' THEN 'memo_promoted' ELSE kind END, "
        "created_at, decided_at, decision FROM notes_notices",
        # Texte der Memos: Verweise auf andere Memos und die Überschrift der Dokumente
        "UPDATE memos_memos SET summary = replace(summary, 'NOTE-', 'MEMO-'), body = replace(body, 'NOTE-', 'MEMO-')",
        "UPDATE memos_documents SET content = replace(content, 'NOTE-', 'MEMO-')",
        # Register: Elementtyp, Labels, Zähler und Label-Verlauf
        "INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES ('memo', 'memos', 'MEMO') "
        "ON CONFLICT(kind) DO UPDATE SET owner = excluded.owner, label_prefix = excluded.label_prefix",
        "UPDATE workspace_elements SET kind = 'memo', label = 'MEMO-' || substr(label, 6) WHERE kind = 'note'",
        "UPDATE workspace_elements SET title = replace(title, 'NOTE-', 'MEMO-') WHERE kind = 'memo'",
        "UPDATE workspace_label_counters SET prefix = 'MEMO' WHERE prefix = 'NOTE'",
        "UPDATE workspace_label_history SET label = 'MEMO-' || substr(label, 6) WHERE label LIKE 'NOTE-%'",
        "DELETE FROM workspace_element_kinds WHERE kind = 'note'",
        # Oberflächenzustand des Plugins (Besitzer = Plugin-ID)
        "UPDATE core_ui_state SET owner = 'memos' WHERE owner = 'notes'",
    ):
        connection.exec_driver_sql(statement)
    for table in _OLD_TABLES:
        connection.exec_driver_sql(f"DROP TABLE {table}")


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1), Migration(2, _v2), Migration(3, _v3))

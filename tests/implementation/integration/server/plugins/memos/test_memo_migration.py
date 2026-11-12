"""Migration 3 von `memos`: eine Datenbank aus der Zeit des Plugins `notes` wird übernommen und umbenannt."""

from __future__ import annotations

import json
from typing import Any

from migration_helpers import ordered, plugin, tables, versions
from notes_legacy_schema import OLD_NOTES_MIGRATIONS
from sqlalchemy import text
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase
from viewer.plugins.memos.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS as WORKSPACE

NOW = "2026-11-01T10:00:00+00:00"
MEMO_TABLES = {
    "memos_statuses",
    "memos_topics",
    "memos_memos",
    "memos_documents",
    "memos_settings",
    "memos_triggers",
    "memos_hints",
}


def _old_defs() -> list[Any]:
    return ordered(
        plugin("workspace", migrations=WORKSPACE),
        plugin("backlog", requires=("workspace",)),
        plugin("notes", requires=("workspace", "backlog"), migrations=OLD_NOTES_MIGRATIONS),
    )


def _new_defs() -> list[Any]:
    return ordered(
        plugin("workspace", migrations=WORKSPACE),
        plugin("backlog", requires=("workspace",)),
        plugin("memos", requires=("workspace", "backlog"), migrations=MIGRATIONS, former_ids=("notes",)),
    )


def _fill_old_database(database: SqliteDatabase) -> None:
    """Zwei Notes (eine mit Dokument, Auslöser und Hinweisen), ein Topic, ein Item, Zähler, Verlauf, UI-Zustand."""
    with database.engine.begin() as c:
        project: str = c.execute(text("SELECT uid FROM workspace_projects")).scalar_one()
        for kind, owner, prefix in (
            ("note", "notes", "NOTE"),
            ("topic", "memos", "TOPIC"),
            ("item", "backlog", "STORY"),
        ):
            c.execute(
                text("INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES (:k, :o, :p)"),
                {"k": kind, "o": owner, "p": prefix},
            )
        for uid, kind, label, title in (
            ("t1", "topic", "TOPIC-001", "Thema"),
            ("n1", "note", "NOTE-001", "Erste Note"),
            ("n2", "note", "NOTE-002", "Zweite, siehe NOTE-001"),
            ("s1", "item", "STORY-001", "Ein Item"),
        ):
            c.execute(
                text(
                    "INSERT INTO workspace_elements(uid, project_uid, kind, label, created_at, updated_at, title) "
                    "VALUES (:u, :p, :k, :l, :n, :n, :t)"
                ),
                {"u": uid, "p": project, "k": kind, "l": label, "n": NOW, "t": title},
            )
            c.execute(
                text("INSERT INTO workspace_label_history(project_uid, label, element_uid) VALUES (:p, :l, :u)"),
                {"p": project, "l": label, "u": uid},
            )
        for prefix, last in (("NOTE", 2), ("TOPIC", 1), ("STORY", 1)):
            c.execute(
                text("INSERT INTO workspace_label_counters(project_uid, prefix, last) VALUES (:p, :x, :l)"),
                {"p": project, "x": prefix, "l": last},
            )
        for statement in (
            "INSERT INTO notes_topics(uid, name) VALUES ('t1', 'Thema')",
            "INSERT INTO notes_notes(uid, summary, body, status, topic_uid, review_at, trigger_mode, archived) "
            "VALUES ('n1', 'Erste Note', 'Langtext', 'snoozed', 't1', '2026-12-12T00:00:00Z', 'all', 0)",
            "INSERT INTO notes_notes(uid, summary, body, status, trigger_mode, archived) "
            "VALUES ('n2', 'Zweite, siehe NOTE-001', 'Mehr zu NOTE-001', 'waiting', 'any', 1)",
            "INSERT INTO notes_documents(note_uid, name, content, revision, updated_at) "
            f"VALUES ('n1', 'NOTE-001_notes.md', '# NOTE-001 — Erste Note', 3, '{NOW}')",
            "INSERT INTO notes_triggers(uid, note_uid, kind, target_uid, status, fired_at, already_met, link_uid) "
            "VALUES ('g1', 'n1', 'event', 's1', 'Completed', NULL, 1, NULL)",
            "INSERT INTO notes_notices(uid, side, subject_uid, source_uid, kind, created_at) "
            f"VALUES ('h1', 'note', 'n1', 's1', 'item_completed', '{NOW}')",
            "INSERT INTO notes_notices(uid, side, subject_uid, source_uid, kind, created_at, decided_at, decision) "
            f"VALUES ('h2', 'item', 's1', 'n2', 'note_promoted', '{NOW}', '{NOW}', 'acknowledge')",
            "INSERT INTO notes_settings(key, value) VALUES ('review_days', '45')",
        ):
            c.exec_driver_sql(statement)
        c.execute(
            text("INSERT INTO core_ui_state(owner, document, updated_at) VALUES ('notes', :d, :n)"),
            {"d": json.dumps({"extended": True}), "n": NOW},
        )


def _rows(database: SqliteDatabase, sql: str) -> list[tuple[Any, ...]]:
    with database.engine.begin() as c:
        return [tuple(r) for r in c.exec_driver_sql(sql)]


def test_an_old_database_is_taken_over_and_renamed(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_old_defs())
    _fill_old_database(database)

    assert runner.run(_new_defs()) == [("memos", 3)]

    assert versions(database)["memos"] == 3 and "notes" not in versions(database)
    assert {t for t in tables(database) if t.startswith(("notes_", "memos_"))} == MEMO_TABLES
    assert _rows(database, "SELECT uid, name FROM memos_topics") == [("t1", "Thema")]
    assert _rows(
        database, "SELECT uid, summary, body, status, topic_uid, trigger_mode, archived FROM memos_memos ORDER BY uid"
    ) == [
        ("n1", "Erste Note", "Langtext", "snoozed", "t1", "all", 0),
        ("n2", "Zweite, siehe MEMO-001", "Mehr zu MEMO-001", "waiting", None, "any", 1),
    ]
    assert _rows(database, "SELECT memo_uid, name, content, revision FROM memos_documents") == [
        ("n1", "MEMO-001_notes.md", "# MEMO-001 — Erste Note", 3)
    ]
    assert _rows(database, "SELECT uid, memo_uid, kind, target_uid, status, already_met FROM memos_triggers") == [
        ("g1", "n1", "event", "s1", "Completed", 1)
    ]
    assert _rows(database, "SELECT uid, side, kind, decision FROM memos_hints ORDER BY uid") == [
        ("h1", "memo", "item_completed", None),
        ("h2", "item", "memo_promoted", "acknowledge"),
    ]
    assert _rows(database, "SELECT key, value FROM memos_settings") == [("review_days", "45")]


def test_the_register_knows_the_memos_under_their_new_names(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_old_defs())
    _fill_old_database(database)

    runner.run(_new_defs())

    assert _rows(database, "SELECT kind, owner, label_prefix FROM workspace_element_kinds ORDER BY kind") == [
        ("item", "backlog", "STORY"),
        ("memo", "memos", "MEMO"),
        ("topic", "memos", "TOPIC"),
    ]
    assert _rows(database, "SELECT uid, kind, label, title FROM workspace_elements ORDER BY uid") == [
        ("n1", "memo", "MEMO-001", "Erste Note"),
        ("n2", "memo", "MEMO-002", "Zweite, siehe MEMO-001"),
        ("s1", "item", "STORY-001", "Ein Item"),
        ("t1", "topic", "TOPIC-001", "Thema"),
    ]
    assert _rows(database, "SELECT prefix, last FROM workspace_label_counters ORDER BY prefix") == [
        ("MEMO", 2),
        ("STORY", 1),
        ("TOPIC", 1),
    ]
    assert [r[0] for r in _rows(database, "SELECT label FROM workspace_label_history ORDER BY label")] == [
        "MEMO-001",
        "MEMO-002",
        "STORY-001",
        "TOPIC-001",
    ]
    assert _rows(database, "SELECT owner FROM core_ui_state") == [("memos",)]


def test_a_new_database_gets_the_memo_tables_directly(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_new_defs())

    assert versions(database)["memos"] == 3
    assert {t for t in tables(database) if t.startswith(("notes_", "memos_"))} == MEMO_TABLES


def test_the_migration_runs_once(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_old_defs())
    _fill_old_database(database)
    runner.run(_new_defs())

    assert runner.run(_new_defs()) == []

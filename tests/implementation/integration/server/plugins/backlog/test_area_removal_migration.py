"""Migration 5 von `backlog` entfernt `backlog_items.area_uid` und `backlog_areas`; sonst bleibt alles erhalten."""

from __future__ import annotations

from migration_helpers import ordered, plugin, versions
from sqlalchemy import text
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase
from viewer.plugins.backlog.infrastructure.database.schema import MIGRATIONS
from viewer.plugins.workspace.infrastructure.database.schema import MIGRATIONS as WORKSPACE

NOW = "2026-11-24T12:00:00+00:00"


def _defs(backlog_versions: int):  # type: ignore[no-untyped-def]
    return ordered(
        plugin("workspace", migrations=WORKSPACE),
        plugin("backlog", requires=("workspace",), migrations=MIGRATIONS[:backlog_versions]),
    )


def _fill_version_4(database: SqliteDatabase) -> None:
    """Zwei Items (eines mit Bereich, mit Eltern, Abhängigkeit, Dokumenten, Notes, Papierkorb) in der Vorversion."""
    with database.engine.begin() as connection:
        project: str = connection.execute(text("SELECT uid FROM workspace_projects")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES "
                "('story', 'backlog', 'STORY'), ('task', 'backlog', 'TASK')"
            )
        )
        connection.execute(
            text("INSERT INTO backlog_areas(uid, project_uid, name) VALUES ('a1', :p, 'Backend-API')"), {"p": project}
        )
        for uid, kind, label in (("s1", "story", "STORY-001"), ("t1", "task", "TASK-001")):
            connection.execute(
                text(
                    "INSERT INTO workspace_elements(uid, project_uid, kind, label, created_at, updated_at) "
                    "VALUES (:u, :p, :k, :l, :n, :n)"
                ),
                {"u": uid, "p": project, "k": kind, "l": label, "n": NOW},
            )
        connection.execute(
            text(
                "INSERT INTO backlog_items(uid, type, title, status, priority, area_uid, parent_uid, "
                "required_for_parent, goal, completion_criteria, summary, resolution, created, position) VALUES "
                "('s1', 'Story', 'Geschichte', 'Open', 'Normal', 'a1', NULL, NULL, 'Ziel', '1. A', 'Kurz', NULL, "
                "'2026-11-01', 3), "
                "('t1', 'Task', 'Aufgabe', 'In progress', 'Important', NULL, 's1', 1, 'Ziel2', '1. B', NULL, NULL, "
                "'2026-11-02', 7)"
            )
        )
        for statement in (
            "INSERT INTO backlog_dependencies(item_uid, depends_on_uid) VALUES ('t1', 's1')",
            "INSERT INTO backlog_documents(item_uid, name, kind, content, revision, updated_at) "
            f"VALUES ('t1', 'TASK-001_spec.md', 'spec', '# Spec', 2, '{NOW}')",
            "INSERT INTO backlog_notes(item_uid, name, preamble, state, revision, updated_at) "
            f"VALUES ('t1', 'TASK-001_notes.md', '# N', '', 4, '{NOW}')",
            "INSERT INTO backlog_notes_entries(item_uid, position, day, topic, body) "
            "VALUES ('t1', 0, '2026-11-02', 'Thema', 'Text')",
            "INSERT INTO backlog_trashed_documents(uid, item_uid, name, kind, content, summary, deleted_at) "
            f"VALUES ('d1', 't1', 'TASK-001_spec_x.md', 'spec', '# X', NULL, '{NOW}')",
        ):
            connection.exec_driver_sql(statement)


def test_migration_5_removes_area_and_keeps_everything_else(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(_defs(4))
    _fill_version_4(database)

    assert runner.run(_defs(len(MIGRATIONS))) == [("backlog", 5)]

    assert versions(database)["backlog"] == 5
    with database.engine.begin() as connection:
        tables = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'table'"))}
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(backlog_items)")}
        items = connection.execute(
            text(
                "SELECT uid, type, title, status, priority, parent_uid, required_for_parent, goal, "
                "completion_criteria, summary, resolution, created, position FROM backlog_items ORDER BY uid"
            )
        ).all()
        counts = {
            table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in (
                "backlog_dependencies",
                "backlog_documents",
                "backlog_notes",
                "backlog_notes_entries",
                "backlog_trashed_documents",
            )
        }
        foreign_key_problems = connection.exec_driver_sql("PRAGMA foreign_key_check").all()
        indexes = {row[0] for row in connection.execute(text("SELECT name FROM sqlite_master WHERE type = 'index'"))}

    assert "backlog_areas" not in tables
    assert "area_uid" not in columns
    assert [tuple(row) for row in items] == [
        ("s1", "Story", "Geschichte", "Open", "Normal", None, None, "Ziel", "1. A", "Kurz", None, "2026-11-01", 3),
        ("t1", "Task", "Aufgabe", "In progress", "Important", "s1", 1, "Ziel2", "1. B", None, None, "2026-11-02", 7),
    ]
    assert counts == {
        "backlog_dependencies": 1,
        "backlog_documents": 1,
        "backlog_notes": 1,
        "backlog_notes_entries": 1,
        "backlog_trashed_documents": 1,
    }
    assert foreign_key_problems == []
    assert {
        "backlog_items_parent",
        "backlog_dependencies_target",
        "backlog_trashed_documents_item",
    } <= indexes

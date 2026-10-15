"""The database schema comes only from versioned migrations, which run on first use."""
from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa

from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.migrations import CURRENT_VERSION, MIGRATIONS
from todo_viewer.infrastructure.database.schema import metadata


def _db(tmp_path: Path) -> Database:
    return Database(f"sqlite:///{tmp_path / 'todo.db'}")


def test_nothing_is_created_before_first_use(tmp_path: Path):
    _db(tmp_path)

    assert not (tmp_path / "todo.db").exists()


def test_an_empty_database_is_upgraded_to_the_current_version(tmp_path: Path):
    db = _db(tmp_path)

    with db.begin() as conn:
        version = conn.execute(sa.text("SELECT version FROM schema_version")).scalar_one()

    assert version == CURRENT_VERSION
    assert set(metadata.tables) <= set(sa.inspect(db.engine).get_table_names())


def test_a_second_start_runs_no_migration_again(tmp_path: Path):
    with _db(tmp_path).begin():
        pass

    with _db(tmp_path).begin() as conn:
        rows = conn.execute(sa.text("SELECT version FROM schema_version")).all()

    assert rows == [(CURRENT_VERSION,)]


def test_the_table_definitions_match_what_the_migrations_create(tmp_path: Path):
    db = _db(tmp_path)
    with db.begin():
        pass
    inspector = sa.inspect(db.engine)

    for table in metadata.tables.values():
        assert {c["name"] for c in inspector.get_columns(table.name)} == {c.name for c in table.columns}, table.name


def test_foreign_keys_are_enforced(tmp_path: Path):
    db = _db(tmp_path)

    with pytest.raises(sa.exc.IntegrityError), db.begin() as conn:
        conn.execute(sa.text(
            "INSERT INTO items (uid, project_id, label, item_type, title, status, location, position) "
            "VALUES ('u', 'no-such-project', 'T-1', 'Task', 't', 'Open', 'active', 0)"))


def test_a_database_from_before_the_notes_gets_the_notes_tables(tmp_path: Path):
    db = _db(tmp_path)
    with db.engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (5)"))
        for number in range(1, 6):
            for statement in MIGRATIONS[number]:
                conn.execute(sa.text(statement))
        conn.execute(sa.text("INSERT INTO projects (id) VALUES ('old')"))

    with db.begin() as conn:
        version = conn.execute(sa.text("SELECT version FROM schema_version")).scalar_one()
        kept = list(conn.execute(sa.text("SELECT id FROM projects")).scalars())

    assert version == CURRENT_VERSION and kept == ["old"]
    assert {"topics", "notes", "note_links", "note_triggers", "note_documents", "note_counters"} <= set(
        sa.inspect(db.engine).get_table_names())


def test_a_database_from_before_the_sync_state_gets_its_table_and_keeps_its_data(tmp_path: Path):
    db = _db(tmp_path)
    with db.engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (7)"))
        for number in range(1, 8):
            for statement in MIGRATIONS[number]:
                conn.execute(sa.text(statement))
        conn.execute(sa.text("INSERT INTO projects (id, synced_primary, synced_mirror) VALUES ('old', 'p0', 'm0')"))

    with db.begin() as conn:
        version = conn.execute(sa.text("SELECT version FROM schema_version")).scalar_one()
        kept = conn.execute(sa.text("SELECT id, synced_primary, synced_mirror FROM projects")).all()
        entries = conn.execute(sa.text("SELECT COUNT(*) FROM sync_entries")).scalar_one()

    assert version == CURRENT_VERSION >= 8
    assert [tuple(r) for r in kept] == [("old", "p0", "m0")] and entries == 0


def test_projects_from_before_the_automatic_sync_get_the_switch_off(tmp_path: Path):
    db = _db(tmp_path)
    with db.engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE schema_version (version INTEGER NOT NULL)"))
        conn.execute(sa.text("INSERT INTO schema_version (version) VALUES (8)"))
        for number in range(1, 9):
            for statement in MIGRATIONS[number]:
                conn.execute(sa.text(statement))
        conn.execute(sa.text("INSERT INTO projects (id, name, backend, path, position) VALUES ('p', 'P', 'markdown', '/p', 0)"))

    with db.begin() as conn:
        switches = list(conn.execute(sa.text("SELECT auto_sync FROM projects")).scalars())

    assert switches == [0] and CURRENT_VERSION >= 9

"""The database schema comes only from versioned migrations, which run on first use."""
from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa

from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.migrations import CURRENT_VERSION
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

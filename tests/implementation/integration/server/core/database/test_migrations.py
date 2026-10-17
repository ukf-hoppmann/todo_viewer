from __future__ import annotations

import pytest
from migration_helpers import mig, ordered, plugin, tables, versions
from sqlalchemy import text
from viewer.core.domain.errors import DatabaseTooNew, MigrationFailed, SchemaViolation
from viewer.core.infrastructure.database import MigrationRunner, SqliteDatabase


def test_empty_database_is_migrated_to_the_current_version(runner: MigrationRunner, database: SqliteDatabase) -> None:
    defs = ordered(
        plugin("workspace", migrations=(mig(1, "CREATE TABLE workspace_elements (uid TEXT PRIMARY KEY)"),)),
        plugin(
            "backlog",
            requires=("workspace",),
            migrations=(
                mig(1, "CREATE TABLE backlog_items (uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid))"),
                mig(2, "CREATE TABLE backlog_areas (name TEXT PRIMARY KEY)"),
            ),
        ),
    )
    applied = runner.run(defs)
    assert applied == [("core", 1), ("workspace", 1), ("backlog", 1), ("backlog", 2)]
    assert versions(database) == {"core": 1, "workspace": 1, "backlog": 2}
    assert {"core_ui_state", "core_sync_state", "workspace_elements", "backlog_items", "backlog_areas"} <= tables(
        database
    )


def test_second_run_changes_nothing(runner: MigrationRunner, database: SqliteDatabase) -> None:
    defs = ordered(plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id INTEGER)"),)))
    runner.run(defs)
    assert runner.run(defs) == []
    assert versions(database) == {"core": 1, "a": 1}


def test_only_pending_migrations_run_after_an_upgrade(runner: MigrationRunner, database: SqliteDatabase) -> None:
    runner.run(ordered(plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id INTEGER)"),))))
    applied = runner.run(
        ordered(plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id INTEGER)"), mig(2, "ALTER TABLE a_x ADD y TEXT"))))
    )
    assert applied == [("a", 2)]


def test_plugins_run_after_the_plugins_they_require_even_if_listed_first(runner: MigrationRunner) -> None:
    defs = ordered(
        plugin("b", requires=("a",), migrations=(mig(1, "CREATE TABLE b_x (a TEXT REFERENCES a_x(id))"),)),
        plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id TEXT PRIMARY KEY)"),)),
    )
    assert [d.id for d in defs] == ["core", "a", "b"]
    assert runner.run(defs) == [("core", 1), ("a", 1), ("b", 1)]


def test_failing_migration_rolls_back_completely_and_keeps_the_previous_version(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    good = plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id INTEGER)"),))
    runner.run(ordered(good))
    broken = plugin(
        "a",
        migrations=(
            mig(1, "CREATE TABLE a_x (id INTEGER)"),
            mig(2, "CREATE TABLE a_y (id INTEGER)", "THIS IS NOT SQL"),
        ),
    )
    with pytest.raises(MigrationFailed) as err:
        runner.run(ordered(broken))
    assert err.value.details == {"owner": "a", "version": 2}
    assert versions(database)["a"] == 1
    assert "a_y" not in tables(database)


def test_database_newer_than_code_is_refused(runner: MigrationRunner) -> None:
    runner.run(
        ordered(plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id INTEGER)"), mig(2, "ALTER TABLE a_x ADD y"))))
    )
    with pytest.raises(DatabaseTooNew):
        runner.run(ordered(plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id INTEGER)"),))))


def test_table_without_the_owners_prefix_fails_and_is_rolled_back(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    with pytest.raises(SchemaViolation) as err:
        runner.run(ordered(plugin("a", migrations=(mig(1, "CREATE TABLE fremd_x (id INTEGER)"),))))
    assert "fremd_x" in str(err.value)
    assert "fremd_x" not in tables(database)
    assert versions(database) == {"core": 1}


def test_foreign_key_to_a_plugin_outside_requires_fails(runner: MigrationRunner, database: SqliteDatabase) -> None:
    defs = ordered(
        plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id TEXT PRIMARY KEY)"),)),
        plugin("b", migrations=(mig(1, "CREATE TABLE b_x (a TEXT REFERENCES a_x(id))"),)),
    )
    with pytest.raises(SchemaViolation) as err:
        runner.run(defs)
    assert "Fremdschlüssel von 'b_x' auf 'a_x'" in str(err.value)
    assert "b_x" not in tables(database)


def test_foreign_key_to_core_and_to_a_required_plugin_is_fine(runner: MigrationRunner) -> None:
    defs = ordered(
        plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id TEXT PRIMARY KEY)"),)),
        plugin(
            "b",
            requires=("a",),
            migrations=(
                mig(1, "CREATE TABLE b_x (a TEXT REFERENCES a_x(id), s TEXT REFERENCES core_ui_state(owner))"),
            ),
        ),
    )
    assert runner.run(defs)[-1] == ("b", 1)


def test_foreign_key_added_later_by_alter_table_is_checked_too(runner: MigrationRunner) -> None:
    defs = ordered(
        plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id TEXT PRIMARY KEY)"),)),
        plugin(
            "b",
            migrations=(
                mig(1, "CREATE TABLE b_x (id INTEGER)"),
                mig(2, "ALTER TABLE b_x ADD COLUMN a TEXT REFERENCES a_x(id)"),
            ),
        ),
    )
    with pytest.raises(SchemaViolation):
        runner.run(defs)


def test_migrations_table_is_created_by_the_runner_and_visible(
    runner: MigrationRunner, database: SqliteDatabase
) -> None:
    runner.run(ordered())
    with database.transaction() as tx:
        assert tx.connection.execute(text("SELECT version FROM core_migrations WHERE owner='core'")).scalar() == 1

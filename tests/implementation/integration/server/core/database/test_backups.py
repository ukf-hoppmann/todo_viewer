from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest
from fakes import FixedClock
from migration_helpers import mig, ordered, plugin
from viewer.core.infrastructure.database import MigrationRunner, SqliteBackupMaker, SqliteDatabase


def test_backup_contains_the_data_and_has_a_speaking_name(
    database: SqliteDatabase, backups: SqliteBackupMaker, tmp_path: Path
) -> None:
    with database.transaction() as tx:
        tx.connection.exec_driver_sql("CREATE TABLE t (v TEXT)")
        tx.connection.exec_driver_sql("INSERT INTO t VALUES ('wichtig')")
    target = backups.create("migration")
    assert target.parent == tmp_path / "backups"
    assert target.name == "viewer-20261016T120000000000Z-migration.db"
    copy = sqlite3.connect(target)
    try:
        assert copy.execute("SELECT v FROM t").fetchall() == [("wichtig",)]
    finally:
        copy.close()


def test_last_ten_per_reason_are_kept(
    database: SqliteDatabase, backups: SqliteBackupMaker, clock: FixedClock, tmp_path: Path
) -> None:
    with database.transaction() as tx:
        tx.connection.exec_driver_sql("CREATE TABLE t (v TEXT)")
    for _ in range(13):
        backups.create("migration")
        clock.advance(timedelta(minutes=1))
    backups.create("sync")
    names = sorted(p.name for p in (tmp_path / "backups").iterdir())
    migration = [n for n in names if n.endswith("-migration.db")]
    assert len(migration) == 10
    assert migration[0].startswith("viewer-20261016T120300")  # die ersten drei sind weg
    assert len([n for n in names if n.endswith("-sync.db")]) == 1


def test_two_backups_at_the_same_instant_do_not_overwrite_each_other(
    database: SqliteDatabase, backups: SqliteBackupMaker
) -> None:
    with database.transaction() as tx:
        tx.connection.exec_driver_sql("CREATE TABLE t (v TEXT)")
    assert backups.create("sync") != backups.create("sync")


def test_invalid_reason_is_rejected(backups: SqliteBackupMaker) -> None:
    with pytest.raises(ValueError):
        backups.create("../böse")


def test_runner_backs_up_once_before_pending_migrations_but_not_an_empty_database(
    runner: MigrationRunner, tmp_path: Path
) -> None:
    backup_dir = tmp_path / "backups"
    first = ordered(plugin("a", migrations=(mig(1, "CREATE TABLE a_x (id INTEGER)"),)))
    runner.run(first)
    assert not backup_dir.exists() or not list(backup_dir.iterdir())  # Erstanlauf: nichts zu sichern

    runner.run(first)  # nichts ausstehend
    assert not backup_dir.exists() or not list(backup_dir.iterdir())

    second = ordered(
        plugin(
            "a",
            migrations=(
                mig(1, "CREATE TABLE a_x (id INTEGER)"),
                mig(2, "ALTER TABLE a_x ADD y TEXT"),
                mig(3, "ALTER TABLE a_x ADD z TEXT"),
            ),
        )
    )
    runner.run(second)
    assert len(list(backup_dir.glob("*-migration.db"))) == 1  # ein Backup für beide Migrationen

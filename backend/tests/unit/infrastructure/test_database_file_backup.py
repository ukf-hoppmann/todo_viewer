"""The backup of the SQLite file: consistent, checked, and pruned; plus the guard before a migration."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa

from todo_viewer.domain.database_backup import backup_file_name
from todo_viewer.domain.errors import DatabaseBackupFailedError
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.file_backup import SqliteFileBackup
from todo_viewer.infrastructure.database.migrations import CURRENT_VERSION, migrate

AT = datetime(2026, 10, 14, 15, 27, 48)


def _database(tmp_path: Path, version: int = CURRENT_VERSION) -> Path:
    path = tmp_path / "todo.db"
    engine = sa.create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        migrate(conn, version)
    engine.dispose()
    return path


def _backup(tmp_path: Path, path: Path, **kwargs: object) -> SqliteFileBackup:
    return SqliteFileBackup(path, tmp_path / "backups", clock=lambda: AT, **kwargs)  # type: ignore[arg-type]


def test_a_backup_is_a_consistent_copy_named_by_time_and_reason(tmp_path: Path):
    path = _database(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO projects (id) VALUES ('p1')")

    created = _backup(tmp_path, path).create("sync")

    assert created == str(tmp_path / "backups" / "todo-20261014-152748-sync.db")
    copy = sqlite3.connect(created)
    assert copy.execute("SELECT id FROM projects").fetchall() == [("p1",)]
    assert copy.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    assert sorted(p.name for p in (tmp_path / "backups").iterdir()) == ["todo-20261014-152748-sync.db"]


def test_rows_that_only_stand_in_the_wal_are_in_the_backup(tmp_path: Path):
    path = _database(tmp_path)
    live = sqlite3.connect(path)  # stays open: its changes live in the -wal file
    live.execute("PRAGMA journal_mode=WAL")
    live.execute("PRAGMA wal_autocheckpoint=0")
    live.execute("INSERT INTO projects (id) VALUES ('only-in-wal')")
    live.commit()
    assert (tmp_path / "todo.db-wal").stat().st_size > 0

    created = _backup(tmp_path, path).create("sync")

    assert sqlite3.connect(created).execute("SELECT id FROM projects").fetchall() == [("only-in-wal",)]
    live.close()


def test_there_is_nothing_to_back_up_before_the_database_exists(tmp_path: Path):
    assert _backup(tmp_path, tmp_path / "todo.db").create("sync") is None
    (tmp_path / "todo.db").write_bytes(b"")
    assert _backup(tmp_path, tmp_path / "todo.db").create("sync") is None
    assert not (tmp_path / "backups").exists()


def test_two_backups_in_one_second_do_not_overwrite_each_other(tmp_path: Path):
    path = _database(tmp_path)
    backup = _backup(tmp_path, path)

    first, second = backup.create("sync"), backup.create("sync")

    assert first != second
    assert Path(str(second)).name == "todo-20261014-152748-sync-2.db"


def test_the_eleventh_backup_removes_the_oldest_automatic_one_and_never_a_manual_one(tmp_path: Path):
    path = _database(tmp_path)
    folder = tmp_path / "backups"
    folder.mkdir()
    manual = folder / "todo-20260101-000000-vor-notes-sync.db"
    manual.write_bytes(b"manual")
    names = [backup_file_name(datetime(2026, 10, 1, 12, 0, s), "migration" if s % 2 else "sync") for s in range(10)]
    for name in names:
        (folder / name).write_bytes(b"old")

    _backup(tmp_path, path).create("sync")

    remaining = sorted(p.name for p in folder.iterdir())
    assert names[0] not in remaining and names[1] in remaining and manual.name in remaining
    assert len(remaining) == 11  # ten automatic ones and the manual one


def test_a_folder_that_cannot_be_written_fails_with_a_stable_code(tmp_path: Path):
    path = _database(tmp_path)
    (tmp_path / "backups").write_text("a file, not a folder")

    with pytest.raises(DatabaseBackupFailedError) as error:
        _backup(tmp_path, path).create("sync")

    assert error.value.code == "database_backup_failed"


def test_only_a_sqlite_file_database_has_a_file_backup(tmp_path: Path):
    assert SqliteFileBackup.for_url(f"sqlite:///{tmp_path / 'x.db'}", tmp_path) is not None
    assert SqliteFileBackup.for_url("sqlite://", tmp_path) is None
    assert SqliteFileBackup.for_url("postgresql://u:p@h/db", tmp_path) is None


# --- before a migration ---

def test_an_older_schema_is_backed_up_before_it_is_migrated(tmp_path: Path):
    path = _database(tmp_path, version=5)
    seen: list[int] = []

    def before() -> None:
        with sqlite3.connect(path) as conn:  # nothing is migrated yet
            seen.append(conn.execute("SELECT version FROM schema_version").fetchone()[0])

    Database(f"sqlite:///{path}", before_migration=before).describe()

    assert seen == [5]


def test_no_backup_for_a_current_or_a_new_database(tmp_path: Path):
    calls: list[int] = []
    Database(f"sqlite:///{tmp_path / 'new.db'}", before_migration=lambda: calls.append(1)).describe()
    Database(f"sqlite:///{tmp_path / 'new.db'}", before_migration=lambda: calls.append(2)).describe()

    assert calls == []


def test_a_failed_backup_stops_the_migration_and_is_tried_again(tmp_path: Path):
    path = _database(tmp_path, version=5)
    attempts: list[int] = []

    def before() -> None:
        attempts.append(1)
        if len(attempts) == 1:
            raise DatabaseBackupFailedError("disk full")

    db = Database(f"sqlite:///{path}", before_migration=before)
    with pytest.raises(DatabaseBackupFailedError):
        db.describe()
    assert sqlite3.connect(path).execute("SELECT version FROM schema_version").fetchone() == (5,)

    assert db.describe().schema_version == CURRENT_VERSION
    assert len(attempts) == 2


# --- automatic runs (STORY-059) ---

def test_an_automatic_run_makes_at_most_one_backup_an_hour(tmp_path: Path):
    path = _database(tmp_path)
    now = [AT]
    backup = SqliteFileBackup(path, tmp_path / "backups", clock=lambda: now[0])

    first = backup.create("auto")
    now[0] = AT.replace(minute=50)
    again = backup.create("auto")
    now[0] = AT.replace(hour=16, minute=40)
    later = backup.create("auto")

    assert again == first and later != first
    assert sorted(p.name for p in (tmp_path / "backups").iterdir()) == ["todo-20261014-152748-auto.db",
                                                                         "todo-20261014-164048-auto.db"]


def test_a_manual_sync_always_makes_its_backup_even_right_after_an_automatic_one(tmp_path: Path):
    path = _database(tmp_path)
    backup = _backup(tmp_path, path)

    backup.create("auto")
    backup.create("sync")

    assert sorted(p.name for p in (tmp_path / "backups").iterdir()) == ["todo-20261014-152748-auto.db",
                                                                         "todo-20261014-152748-sync.db"]


def test_frequent_automatic_backups_do_not_push_out_the_one_of_an_earlier_day(tmp_path: Path):
    path = _database(tmp_path)
    folder = tmp_path / "backups"
    folder.mkdir()
    old = folder / backup_file_name(datetime(2026, 10, 10, 8, 0, 0), "auto")
    old.write_bytes(b"old")
    for hour in range(1, 12):
        (folder / backup_file_name(datetime(2026, 10, 14, hour, 0, 0), "auto")).write_bytes(b"x")

    _backup(tmp_path, path).create("sync")

    assert old.exists()
    assert len([p for p in folder.iterdir() if p.name.startswith("todo-20261014")]) == 10

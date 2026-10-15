"""Backups of the SQLite file of the central database."""
from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
import structlog

from todo_viewer.domain.database_backup import KEEP_AUTOMATIC, backup_file_name, backups_to_remove
from todo_viewer.domain.errors import DatabaseBackupFailedError

log = structlog.get_logger(__name__)


class SqliteFileBackup:
    """Copies the database file with SQLite's backup function, which is consistent while the database runs in WAL mode
    (rows that only stand in the WAL are included). The copy is checked before it is kept; only the automatic
    backups in the folder are ever removed."""

    def __init__(self, database: Path, folder: Path, clock: Callable[[], datetime] = datetime.now,
                 keep: int = KEEP_AUTOMATIC):
        self._database = database
        self._folder = folder
        self._clock = clock
        self._keep = keep

    @classmethod
    def for_url(cls, url: str, folder: Path) -> SqliteFileBackup | None:
        """The backup of a SQLite file database; None for any other kind (nothing to copy as a file)."""
        parsed = sa.engine.make_url(url)
        if parsed.get_backend_name() != "sqlite" or not parsed.database or parsed.database == ":memory:":
            return None
        return cls(Path(parsed.database), folder)

    def create(self, reason: str) -> str | None:
        if not self._database.is_file() or self._database.stat().st_size == 0:
            return None
        try:
            target = self._unused(reason)
            self._folder.mkdir(parents=True, exist_ok=True)
            partial = target.with_name(target.name + ".partial")
            try:
                self._copy(partial)
                partial.rename(target)
            finally:
                with contextlib.suppress(OSError):
                    partial.unlink(missing_ok=True)
            self._prune()
        except (OSError, sqlite3.Error, ValueError) as error:
            log.warning("database_backup_failed", reason=reason, error=f"{type(error).__name__}: {error}")
            raise DatabaseBackupFailedError(str(error)) from error
        log.info("database_backup_created", reason=reason, file=str(target))
        return str(target)

    def _unused(self, reason: str) -> Path:
        at, attempt = self._clock(), 1
        while (self._folder / backup_file_name(at, reason, attempt)).exists():
            attempt += 1
        return self._folder / backup_file_name(at, reason, attempt)

    def _copy(self, partial: Path) -> None:
        source = sqlite3.connect(self._database)
        copy = sqlite3.connect(partial)
        try:
            source.backup(copy)
            copy.execute("PRAGMA journal_mode=DELETE")  # one self-contained file, no -wal/-shm beside it
            if copy.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise ValueError("The copy of the database is damaged.")
            for table in _tables(source):
                if _count(source, table) != _count(copy, table):
                    raise ValueError(f"The copy of the database differs in table {table}.")
        finally:
            copy.close()
            source.close()

    def _prune(self) -> None:
        for name in backups_to_remove(p.name for p in self._folder.iterdir()):
            with contextlib.suppress(OSError):
                (self._folder / name).unlink()


def _tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
    return [name for (name,) in rows]


def _count(conn: sqlite3.Connection, table: str) -> int:
    count: int = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    return count

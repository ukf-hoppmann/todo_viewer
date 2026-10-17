from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, Engine, create_engine, event


class SqlTransaction:
    """Die Transaktion, die `SqliteDatabase` ausgibt; Adapter greifen auf `connection` zu."""

    def __init__(self, connection: Connection) -> None:
        self.connection = connection


class SqliteDatabase:
    """Eine SQLite-Datei. Fremdschlüssel sind an; jede Transaktion beginnt mit eigenem `BEGIN`, damit auch DDL
    (Migrationen) atomar ist, was pysqlite von sich aus nicht tut."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(f"sqlite:///{self.path}", connect_args={"check_same_thread": False})
        event.listen(self.engine, "connect", _on_connect)
        event.listen(self.engine, "begin", _on_begin)

    @contextmanager
    def transaction(self) -> Iterator[SqlTransaction]:
        with self.engine.begin() as connection:
            yield SqlTransaction(connection)

    def dispose(self) -> None:
        self.engine.dispose()


def _on_connect(dbapi_connection: Any, record: Any) -> None:
    dbapi_connection.isolation_level = None  # pysqlite soll nicht selbst BEGIN/COMMIT einfügen
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


def _on_begin(connection: Connection) -> None:
    connection.exec_driver_sql("BEGIN")

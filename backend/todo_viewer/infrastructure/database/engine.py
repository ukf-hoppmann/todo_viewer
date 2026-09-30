"""The central database: connected lazily, migrated on first use."""
from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import sqlalchemy as sa

from .migrations import migrate


class Database:
    """Nothing is opened or created before the first transaction, so markdown-only setups never get a file."""

    def __init__(self, url: str):
        self._url = url
        self._engine: sa.Engine | None = None
        self._migrated = False
        self._lock = threading.Lock()

    @property
    def engine(self) -> sa.Engine:
        with self._lock:
            if self._engine is None:
                self._engine = self._create_engine()
            return self._engine

    @contextmanager
    def begin(self) -> Iterator[sa.Connection]:
        """One transaction: committed on normal exit, rolled back on an exception."""
        engine = self.engine
        if not self._migrated:
            with self._lock:
                if not self._migrated:
                    with engine.begin() as conn:
                        migrate(conn)
                    self._migrated = True
        with engine.begin() as conn:
            yield conn

    def _create_engine(self) -> sa.Engine:
        engine = sa.create_engine(self._url)
        if engine.dialect.name == "sqlite":
            # pysqlite starts transactions late and ignores deferred constraints unless it is told to begin.
            @sa.event.listens_for(engine, "connect")
            def _on_connect(dbapi_conn: Any, _record: Any) -> None:
                dbapi_conn.isolation_level = None
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

            @sa.event.listens_for(engine, "begin")
            def _on_begin(conn: sa.Connection) -> None:
                conn.exec_driver_sql("BEGIN IMMEDIATE")
        return engine

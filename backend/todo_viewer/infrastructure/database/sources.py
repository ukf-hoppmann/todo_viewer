"""The registered projects (sources) in the central database, markdown and database ones alike."""
from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager

import sqlalchemy as sa

from todo_viewer.domain.errors import ProjectNotEmptyError
from todo_viewer.domain.source import Source

from .engine import Database
from .schema import items, projects


class DatabaseSourceRepository:
    """`before_access` runs before every read, e.g. to take over sources still listed in config.json."""

    def __init__(self, db: Database, before_access: Callable[[], None] = lambda: None):
        self._db = db
        self._before_access = before_access
        self._lock = threading.RLock()

    def all(self) -> list[Source]:
        with self._lock:
            self._before_access()
            with self._db.begin() as conn:
                return _read(conn)

    @contextmanager
    def edit(self) -> Iterator[list[Source]]:
        """The yielded list is saved in one transaction on normal exit; nothing is saved on an exception.

        A database project that still has items cannot be removed (ProjectNotEmptyError).
        """
        with self._lock:
            self._before_access()
            with self._db.begin() as conn:
                before = _read(conn)
            working = list(before)
            yield working
            with self._db.begin() as conn:
                _write(conn, before, working)


def _read(conn: sa.Connection) -> list[Source]:
    rows = conn.execute(sa.select(projects).where(projects.c.name.is_not(None)).order_by(projects.c.position))
    return [Source(project=row.name, path=row.path or "", backend=row.backend, id=row.id, sync_path=row.sync_path,
                   extra=json.loads(row.extra) if row.extra else {}) for row in rows]


def _write(conn: sa.Connection, before: list[Source], after: list[Source]) -> None:
    kept = {s.id for s in after}
    for source in before:
        if source.id not in kept:
            if conn.execute(sa.select(items.c.uid).where(items.c.project_id == source.id).limit(1)).first():
                raise ProjectNotEmptyError(source.project)
            conn.execute(sa.delete(projects).where(projects.c.id == source.id))
    existing: set[str] = set(conn.execute(sa.select(projects.c.id)).scalars())
    for position, source in enumerate(after):
        values = dict(name=source.project, backend=source.backend, path=source.path, sync_path=source.sync_path,
                      position=position, extra=json.dumps(source.extra, ensure_ascii=False) if source.extra else None)
        if source.id in existing:
            conn.execute(sa.update(projects).where(projects.c.id == source.id).values(**values))
        else:
            conn.execute(sa.insert(projects).values(id=source.id, **values))

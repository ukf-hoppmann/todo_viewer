"""Backlog repository backed by the central database.

Items are stored with an internal `uid`; references between them use it. Outside this package items are
addressed by their label (`Item.id`), and the uid never leaves the adapter.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable, Sequence

import sqlalchemy as sa
import structlog

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.errors import LifecycleViolationError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SourceProblem

from .engine import Database
from .schema import item_dependencies, item_document_names, item_extra_fields, items, projects

log = structlog.get_logger(__name__)

NOTES, SPEC = "notes", "spec"


def new_uid() -> str:
    return str(uuid.uuid4())


class DatabaseBacklogRepository:
    def __init__(self, db: Database, uids: Callable[[], str] = new_uid):
        self._db = db
        self._uids = uids

    # ---------- reading ----------

    def check(self, source: Source) -> SourceProblem | None:
        try:
            with self._db.begin():
                return None
        except sa.exc.SQLAlchemyError as exc:
            return self._unavailable(source, exc)

    def load(self, source: Source) -> Backlog:
        try:
            with self._db.begin() as conn:
                return Backlog(items=[item for _, item in _Rows(conn, source).all()], archive_available=True)
        except sa.exc.SQLAlchemyError as exc:
            return Backlog(problem=self._unavailable(source, exc))

    def get(self, source: Source, item_id: str) -> Item:
        return self.load(source).find(item_id)

    def archive_available(self, source: Source) -> bool:
        return True

    # ---------- writing ----------

    def store_all(self, source: Source, backlog: Sequence[Item]) -> None:
        """Replaces all items of the project (and with them their documents) in one transaction."""
        with self._db.begin() as conn:
            _ensure_project(conn, source)
            conn.execute(sa.delete(items).where(items.c.project_id == source.id))
            uids = {item.id: self._uids() for item in backlog}
            for position, item in enumerate(backlog):
                _insert(conn, source, uids[item.id], item, position, uids)

    @staticmethod
    def _unavailable(source: Source, exc: Exception) -> SourceProblem:
        log.warning("database_unavailable", source=source.id, error=f"{type(exc).__name__}: {exc}")
        return SourceProblem("db_unavailable", "The database cannot be opened.")


class _Rows:
    """Reads the items of one project with everything that belongs to them."""

    def __init__(self, conn: sa.Connection, source: Source):
        self._conn = conn
        self._source = source

    def all(self) -> list[tuple[str, Item]]:
        """(uid, item) pairs: the active list first, then the archive, each in stored order."""
        in_project = sa.select(items.c.uid).where(items.c.project_id == self._source.id).scalar_subquery()
        rows = self._conn.execute(
            sa.select(items).where(items.c.project_id == self._source.id)
            .order_by(sa.case((items.c.location == Location.ACTIVE.value, 0), else_=1), items.c.position)).all()
        labels = {row.uid: row.label for row in rows}
        dependencies = self._grouped(item_dependencies, in_project, "depends_on_uid")
        extra = self._pairs(in_project)
        documents = self._documents(in_project)
        return [(row.uid, Item(
            id=row.label, title=row.title, project=self._source.project, item_type=row.item_type,
            status=row.status, parent=labels.get(row.parent_uid) if row.parent_uid else None,
            required_for_parent=row.required_for_parent,
            dependencies=[labels[d] for d in dependencies.get(row.uid, [])],
            created=row.created, area=row.area, priority=row.priority, goal=row.goal,
            completion_criteria=row.completion_criteria, summary=row.summary, resolution=row.resolution,
            notes=documents.get((row.uid, NOTES), []), spec=documents.get((row.uid, SPEC), []),
            extra_fields=extra.get(row.uid, {}), location=Location(row.location), deleted=row.deleted,
        )) for row in rows]

    def _grouped(self, table: sa.Table, uids: sa.ScalarSelect[str], column: str) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for row in self._conn.execute(sa.select(table).where(table.c.item_uid.in_(uids))
                                      .order_by(table.c.item_uid, table.c.position)):
            grouped.setdefault(row.item_uid, []).append(getattr(row, column))
        return grouped

    def _pairs(self, uids: sa.ScalarSelect[str]) -> dict[str, dict[str, str]]:
        pairs: dict[str, dict[str, str]] = {}
        for row in self._conn.execute(sa.select(item_extra_fields).where(item_extra_fields.c.item_uid.in_(uids))
                                      .order_by(item_extra_fields.c.item_uid, item_extra_fields.c.position)):
            pairs.setdefault(row.item_uid, {})[row.key] = row.value
        return pairs

    def _documents(self, uids: sa.ScalarSelect[str]) -> dict[tuple[str, str], list[str]]:
        names: dict[tuple[str, str], list[str]] = {}
        table = item_document_names
        for row in self._conn.execute(sa.select(table).where(table.c.item_uid.in_(uids))
                                      .order_by(table.c.item_uid, table.c.kind, table.c.position)):
            names.setdefault((row.item_uid, row.kind), []).append(row.name)
        return names


def _ensure_project(conn: sa.Connection, source: Source) -> None:
    if conn.execute(sa.select(projects.c.id).where(projects.c.id == source.id)).first() is None:
        conn.execute(sa.insert(projects).values(id=source.id))


def _resolve(item: Item, labels: Iterable[str], uids: dict[str, str]) -> list[str]:
    """The uids of referenced items; references to items the project does not have are refused."""
    labels = list(labels)
    unknown = tuple(label for label in labels if label not in uids)
    if unknown:
        raise LifecycleViolationError("unknown_reference", item.id, unknown)
    return [uids[label] for label in labels]


def _values(source: Source, item: Item, position: int, uids: dict[str, str]) -> dict[str, object]:
    parent = _resolve(item, [item.parent] if item.parent else [], uids)
    return dict(
        project_id=source.id, label=item.id, item_type=item.item_type, title=item.title, status=item.status,
        parent_uid=parent[0] if parent else None, required_for_parent=item.required_for_parent,
        created=item.created, area=item.area, priority=item.priority, goal=item.goal,
        completion_criteria=item.completion_criteria, summary=item.summary, resolution=item.resolution,
        location=item.location.value, deleted=item.deleted, position=position,
    )


def _insert(conn: sa.Connection, source: Source, uid: str, item: Item, position: int,
            uids: dict[str, str]) -> None:
    conn.execute(sa.insert(items).values(uid=uid, **_values(source, item, position, uids)))
    _write_parts(conn, uid, item, uids)


def _write_parts(conn: sa.Connection, uid: str, item: Item, uids: dict[str, str]) -> None:
    """Dependencies, free fields, and document names of an item, replacing what was stored."""
    for table in (item_dependencies, item_extra_fields, item_document_names):
        conn.execute(sa.delete(table).where(table.c.item_uid == uid))
    dependencies = _resolve(item, item.dependencies, uids)
    rows = [
        (item_dependencies, [dict(item_uid=uid, position=p, depends_on_uid=d) for p, d in enumerate(dependencies)]),
        (item_extra_fields, [dict(item_uid=uid, position=p, key=k, value=v)
                             for p, (k, v) in enumerate(item.extra_fields.items())]),
        (item_document_names, [dict(item_uid=uid, kind=kind, position=p, name=n)
                               for kind, names in ((NOTES, item.notes), (SPEC, item.spec))
                               for p, n in enumerate(names)]),
    ]
    for table, values in rows:
        if values:
            conn.execute(sa.insert(table), values)

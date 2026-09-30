"""Backlog repository backed by the central database.

Items are stored with an internal `uid`; references between them use it. Outside this package items are
addressed by their label (`Item.id`), and the uid never leaves the adapter.
"""
from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Callable, Iterable, Sequence

import sqlalchemy as sa
import structlog

from todo_viewer.domain.backlog import Backlog
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import (
    BacklogExistsError,
    DuplicateItemError,
    LifecycleViolationError,
    VersionConflictError,
)
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

    def apply(self, source: Source, item: Item, changes: ChangeSet) -> Item:
        return self.apply_all(source, [(item, changes)])[0]

    def apply_all(self, source: Source, plan: Sequence[tuple[Item, ChangeSet]]) -> list[Item]:
        """All changes in one transaction; each item must still be at its version.

        Ids change first, so references in the same plan may already use the new ids.
        """
        with self._db.begin() as conn:
            uid_of = self._current(conn, source, [item for item, _ in plan])
            uids = {item.id: uid for uid, item in _Rows(conn, source).all()}
            after = [(uid_of[item.id], item, changes.applied_to(item)) for item, changes in plan]
            for _, old, _ in after:
                del uids[old.id]
            uids.update({new.id: uid for uid, _, new in after})
            position = _next_position(conn, source)
            for uid, old, new in after:
                values = _values(source, new, uids)
                if new.location is not old.location:  # moved entries go to the end of their new list
                    values["position"], position = position, position + 1
                conn.execute(sa.update(items).where(items.c.uid == uid).values(**values))
                _write_parts(conn, uid, new, uids)
            stored = dict(_Rows(conn, source).all())
            return [stored[uid] for uid, _, _ in after]

    def create(self, source: Source, item: Item) -> Item:
        """Adds a new active item at the end of the active list."""
        with self._db.begin() as conn:
            _ensure_project(conn, source)
            uids = {i.id: uid for uid, i in _Rows(conn, source).all()}
            if item.id in uids:
                raise DuplicateItemError(item.id)
            uid = uids[item.id] = self._uids()
            new = dataclasses.replace(item, location=Location.ACTIVE)
            _insert(conn, source, uid, new, _next_position(conn, source), uids)
            return dict(_Rows(conn, source).all())[uid]

    def delete(self, source: Source, targets: Sequence[Item]) -> None:
        """Removes the items for good (their documents go with them); each must still be at its version."""
        try:
            with self._db.begin() as conn:
                stored = self._current(conn, source, targets)
                conn.execute(sa.delete(items).where(items.c.uid.in_(list(stored.values()))))
        except sa.exc.IntegrityError:
            # Another item still refers to one of them; the lifecycle rules normally prevent this.
            raise LifecycleViolationError("item_referenced", targets[0].id) from None

    def initialize(self, source: Source, language: str) -> None:
        """Creates the project without items; raises BacklogExistsError if it exists."""
        with self._db.begin() as conn:
            if conn.execute(sa.select(projects.c.id).where(projects.c.id == source.id)).first() is not None:
                raise BacklogExistsError()
            conn.execute(sa.insert(projects).values(id=source.id))

    def write_backlog(self, source: Source, backlog: Sequence[Item], language: str) -> None:
        """Makes the project hold exactly these items in one transaction; stored items keep their uid and documents."""
        with self._db.begin() as conn:
            _ensure_project(conn, source)
            stored = {item.id: uid for uid, item in _Rows(conn, source).all()}
            uids = {item.id: stored.get(item.id) or self._uids() for item in backlog}
            for position, item in enumerate(backlog):
                if item.id in stored:
                    conn.execute(sa.update(items).where(items.c.uid == uids[item.id])
                                 .values(position=position, **_values(source, item, uids)))
                    _write_parts(conn, uids[item.id], item, uids)
                else:
                    _insert(conn, source, uids[item.id], item, position, uids)
            gone = [uid for label, uid in stored.items() if label not in uids]
            if gone:
                conn.execute(sa.delete(items).where(items.c.uid.in_(gone)))

    @staticmethod
    def _current(conn: sa.Connection, source: Source, expected: Sequence[Item]) -> dict[str, str]:
        """Label -> uid of the expected items; raises VersionConflictError if one changed or is gone."""
        stored = {item.id: (uid, item) for uid, item in _Rows(conn, source).all()}
        for item in expected:
            found = stored.get(item.id)
            if found is None or found[1].version != item.version:
                raise VersionConflictError(item.id)
        return {item.id: stored[item.id][0] for item in expected}

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


def _next_position(conn: sa.Connection, source: Source) -> int:
    last = conn.execute(sa.select(sa.func.max(items.c.position)).where(items.c.project_id == source.id)).scalar()
    return 0 if last is None else int(last) + 1


def _values(source: Source, item: Item, uids: dict[str, str]) -> dict[str, object]:
    parent = _resolve(item, [item.parent] if item.parent else [], uids)
    return dict(
        project_id=source.id, label=item.id, item_type=item.item_type, title=item.title, status=item.status,
        parent_uid=parent[0] if parent else None, required_for_parent=item.required_for_parent,
        created=item.created, area=item.area, priority=item.priority, goal=item.goal,
        completion_criteria=item.completion_criteria, summary=item.summary, resolution=item.resolution,
        location=item.location.value, deleted=item.deleted,
    )


def _insert(conn: sa.Connection, source: Source, uid: str, item: Item, position: int,
            uids: dict[str, str]) -> None:
    conn.execute(sa.insert(items).values(uid=uid, position=position, **_values(source, item, uids)))
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

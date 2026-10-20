from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.backlog.domain.model import Item

_SELECT = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at,
       i.type, i.title, i.status, i.priority, a.name AS area, i.parent_uid, i.required_for_parent,
       i.goal, i.completion_criteria, i.summary, i.resolution, i.created, i.position
FROM backlog_items i
JOIN workspace_elements e ON e.uid = i.uid
LEFT JOIN backlog_areas a ON a.uid = i.area_uid
"""


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _optional_bool(value: int | None) -> bool | None:
    return None if value is None else bool(value)


class SqlItemRepository:
    def insert(self, tx: Transaction, item: Item) -> None:
        connection = _conn(tx)
        area_uid = self._area_uid(connection, item) if item.area else None
        connection.execute(
            text(
                "INSERT INTO backlog_items(uid, type, title, status, priority, area_uid, parent_uid, "
                "required_for_parent, goal, completion_criteria, summary, resolution, created, position) "
                "VALUES (:uid, :type, :title, :status, :priority, :area, :parent, :required, :goal, :criteria, "
                ":summary, :resolution, :created, :position)"
            ),
            {
                "uid": item.uid,
                "type": item.type,
                "title": item.title,
                "status": item.status,
                "priority": item.priority,
                "area": area_uid,
                "parent": item.parent_uid,
                "required": None if item.required_for_parent is None else int(item.required_for_parent),
                "goal": item.goal,
                "criteria": item.completion_criteria,
                "summary": item.summary,
                "resolution": item.resolution,
                "created": item.created.isoformat(),
                "position": item.position,
            },
        )
        for target in item.dependencies:
            connection.execute(
                text("INSERT INTO backlog_dependencies(item_uid, depends_on_uid) VALUES (:i, :d)"),
                {"i": item.uid, "d": target},
            )

    def update(self, tx: Transaction, item: Item) -> None:
        connection = _conn(tx)
        area_uid = self._area_uid(connection, item) if item.area else None
        connection.execute(
            text(
                "UPDATE backlog_items SET type = :type, title = :title, status = :status, priority = :priority, "
                "area_uid = :area, parent_uid = :parent, required_for_parent = :required, goal = :goal, "
                "completion_criteria = :criteria, summary = :summary, resolution = :resolution, position = :position "
                "WHERE uid = :uid"
            ),
            {
                "uid": item.uid,
                "type": item.type,
                "title": item.title,
                "status": item.status,
                "priority": item.priority,
                "area": area_uid,
                "parent": item.parent_uid,
                "required": None if item.required_for_parent is None else int(item.required_for_parent),
                "goal": item.goal,
                "criteria": item.completion_criteria,
                "summary": item.summary,
                "resolution": item.resolution,
                "position": item.position,
            },
        )
        connection.execute(text("DELETE FROM backlog_dependencies WHERE item_uid = :u"), {"u": item.uid})
        for target in item.dependencies:
            connection.execute(
                text("INSERT INTO backlog_dependencies(item_uid, depends_on_uid) VALUES (:i, :d)"),
                {"i": item.uid, "d": target},
            )

    def area_names(self, tx: Transaction, project_uid: str) -> list[str]:
        rows = _conn(tx).execute(
            text("SELECT name FROM backlog_areas WHERE project_uid = :p ORDER BY name"), {"p": project_uid}
        )
        return [str(row[0]) for row in rows]

    def siblings(self, tx: Transaction, project_uid: str, parent_uid: str | None) -> list[Item]:
        where = "i.parent_uid IS NULL" if parent_uid is None else "i.parent_uid = :parent"
        return self._load(
            tx,
            _SELECT + f" WHERE e.project_uid = :p AND e.deleted_at IS NULL AND {where} ORDER BY i.position, e.label",
            {"p": project_uid, "parent": parent_uid},
        )

    def set_positions(self, tx: Transaction, uids: Sequence[str]) -> None:
        for position, uid in enumerate(uids):
            _conn(tx).execute(text("UPDATE backlog_items SET position = :n WHERE uid = :u"), {"n": position, "u": uid})

    @staticmethod
    def _area_uid(connection: Connection, item: Item) -> str:
        row = connection.execute(
            text("SELECT uid FROM backlog_areas WHERE project_uid = :p AND name = :n"),
            {"p": item.project_uid, "n": item.area},
        ).first()
        if row is not None:
            return str(row[0])
        uid = str(uuid.uuid4())
        connection.execute(
            text("INSERT INTO backlog_areas(uid, project_uid, name) VALUES (:u, :p, :n)"),
            {"u": uid, "p": item.project_uid, "n": item.area},
        )
        return uid

    def get(self, tx: Transaction, uid: str) -> Item | None:
        rows = self._load(tx, _SELECT + " WHERE i.uid = :u", {"u": uid})
        return rows[0] if rows else None

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Item]:
        query = _SELECT + " WHERE 1 = 1"
        params: dict[str, object] = {}
        if not include_deleted:
            query += " AND e.deleted_at IS NULL"
        if project_uids is not None:
            if not project_uids:
                return []
            names = {f"p{n}": uid for n, uid in enumerate(project_uids)}
            query += " AND e.project_uid IN (" + ", ".join(f":{name}" for name in names) + ")"
            params.update(names)
        return self._load(tx, query + " ORDER BY e.project_uid, i.position, e.label", params)

    def children(self, tx: Transaction, uid: str) -> list[Item]:
        return self._load(tx, _SELECT + " WHERE i.parent_uid = :u ORDER BY i.position, e.label", {"u": uid})

    def delete(self, tx: Transaction, uid: str) -> None:
        connection = _conn(tx)
        connection.execute(
            text("DELETE FROM backlog_dependencies WHERE item_uid = :u OR depends_on_uid = :u"), {"u": uid}
        )
        connection.execute(text("DELETE FROM backlog_items WHERE uid = :u"), {"u": uid})

    def _load(self, tx: Transaction, query: str, params: dict[str, object]) -> list[Item]:
        connection = _conn(tx)
        rows = connection.execute(text(query), params).all()
        if not rows:
            return []
        uids = [row.uid for row in rows]
        marks = {f"d{n}": uid for n, uid in enumerate(uids)}
        dependency_rows = connection.execute(
            text(
                "SELECT item_uid, depends_on_uid FROM backlog_dependencies WHERE item_uid IN ("
                + ", ".join(f":{name}" for name in marks)
                + ") ORDER BY item_uid, depends_on_uid"
            ),
            marks,
        ).all()
        dependencies: dict[str, list[str]] = {}
        for row in dependency_rows:
            dependencies.setdefault(row.item_uid, []).append(row.depends_on_uid)
        in_marks = ", ".join(f":{name}" for name in marks)
        document_rows = connection.execute(
            text(
                f"SELECT item_uid, name, kind FROM backlog_documents WHERE item_uid IN ({in_marks}) "
                f"UNION ALL SELECT item_uid, name, 'notes' AS kind FROM backlog_notes WHERE item_uid IN ({in_marks}) "
                "ORDER BY item_uid, kind DESC, name"
            ),
            marks,
        ).all()
        documents: dict[tuple[str, str], list[str]] = {}
        for row in document_rows:
            documents.setdefault((row.item_uid, row.kind), []).append(row.name)
        return [
            Item(
                uid=row.uid,
                project_uid=row.project_uid,
                label=row.label,
                type=row.type,
                title=row.title,
                status=row.status,
                priority=row.priority,
                area=row.area,
                parent_uid=row.parent_uid,
                required_for_parent=_optional_bool(row.required_for_parent),
                goal=row.goal,
                completion_criteria=row.completion_criteria,
                summary=row.summary,
                resolution=row.resolution,
                created=date.fromisoformat(row.created),
                position=row.position,
                revision=row.revision,
                deleted_at=datetime.fromisoformat(row.deleted_at) if row.deleted_at else None,
                dependencies=tuple(dependencies.get(row.uid, ())),
                notes=tuple(documents.get((row.uid, "notes"), ())),
                spec=tuple(documents.get((row.uid, "spec"), ())),
            )
            for row in rows
        ]

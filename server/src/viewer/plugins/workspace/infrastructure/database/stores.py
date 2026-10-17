from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Connection, delete, func, insert, select, text, update

from viewer.core.application.ports import Transaction
from viewer.core.domain.plugin import ElementKind
from viewer.core.infrastructure.database import SqlTransaction, update_with_revision
from viewer.plugins.workspace.domain.model import Element, Link, Project, SyncDirection
from viewer.plugins.workspace.infrastructure.database.tables import elements, links, projects


def conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _project(row: Any) -> Project:
    return Project(
        uid=row.uid,
        name=row.name,
        mirror_folder=row.mirror_folder,
        mirror_enabled=bool(row.mirror_enabled),
        auto_sync=bool(row.auto_sync),
        sync_direction=row.sync_direction,
        position=row.position,
        revision=row.revision,
        created_at=datetime.fromisoformat(row.created_at),
        deleted_at=_time(row.deleted_at),
    )


def _element(row: Any) -> Element:
    return Element(
        uid=row.uid,
        project_uid=row.project_uid,
        kind=row.kind,
        label=row.label,
        revision=row.revision,
        created_at=datetime.fromisoformat(row.created_at),
        updated_at=datetime.fromisoformat(row.updated_at),
        deleted_at=_time(row.deleted_at),
        title=row.title,
    )


def _link(row: Any) -> Link:
    return Link(row.uid, row.from_uid, row.to_uid, row.role, datetime.fromisoformat(row.created_at))


class SqlProjectStore:
    def list(self, tx: Transaction, *, include_deleted: bool = False) -> list[Project]:
        query = select(projects).order_by(projects.c.position, projects.c.name)
        if not include_deleted:
            query = query.where(projects.c.deleted_at.is_(None))
        return [_project(row) for row in conn(tx).execute(query)]

    def get(self, tx: Transaction, uid: str) -> Project | None:
        row = conn(tx).execute(select(projects).where(projects.c.uid == uid)).first()
        return _project(row) if row else None

    def name_taken(self, tx: Transaction, name: str, except_uid: str | None = None) -> bool:
        query = (
            select(func.count()).select_from(projects).where(projects.c.name == name, projects.c.deleted_at.is_(None))
        )
        if except_uid:
            query = query.where(projects.c.uid != except_uid)
        return bool(conn(tx).execute(query).scalar_one())

    def insert(self, tx: Transaction, project: Project) -> None:
        conn(tx).execute(
            insert(projects).values(
                uid=project.uid,
                name=project.name,
                mirror_folder=project.mirror_folder,
                mirror_enabled=int(project.mirror_enabled),
                auto_sync=int(project.auto_sync),
                sync_direction=project.sync_direction,
                position=project.position,
                revision=project.revision,
                created_at=project.created_at.isoformat(),
                deleted_at=project.deleted_at.isoformat() if project.deleted_at else None,
            )
        )

    def update(self, tx: Transaction, project: Project, expected_revision: int) -> Project:
        update_with_revision(
            conn(tx),
            projects,
            projects.c.uid == project.uid,
            expected_revision,
            {
                "name": project.name,
                "mirror_folder": project.mirror_folder,
                "mirror_enabled": int(project.mirror_enabled),
                "auto_sync": int(project.auto_sync),
                "sync_direction": project.sync_direction,
                "deleted_at": project.deleted_at.isoformat() if project.deleted_at else None,
            },
        )
        updated = self.get(tx, project.uid)
        assert updated is not None
        return updated

    def set_positions(self, tx: Transaction, uids: Sequence[str]) -> None:
        for position, uid in enumerate(uids):
            conn(tx).execute(update(projects).where(projects.c.uid == uid).values(position=position))

    def delete(self, tx: Transaction, uid: str) -> None:
        connection = conn(tx)
        connection.execute(text("DELETE FROM workspace_label_counters WHERE project_uid = :u"), {"u": uid})
        connection.execute(delete(projects).where(projects.c.uid == uid))

    def count_elements(self, tx: Transaction, project_uid: str, *, include_deleted: bool) -> int:
        query = select(func.count()).select_from(elements).where(elements.c.project_uid == project_uid)
        if not include_deleted:
            query = query.where(elements.c.deleted_at.is_(None))
        return int(conn(tx).execute(query).scalar_one())

    def mark_elements_deleted(self, tx: Transaction, project_uid: str, at: datetime) -> int:
        result = conn(tx).execute(
            update(elements)
            .where(elements.c.project_uid == project_uid, elements.c.deleted_at.is_(None))
            .values(deleted_at=at.isoformat(), updated_at=at.isoformat(), revision=elements.c.revision + 1)
        )
        return int(result.rowcount)


class SqlElementStore:
    def kind_prefix(self, tx: Transaction, kind: str) -> str | None:
        row = (
            conn(tx)
            .execute(text("SELECT label_prefix FROM workspace_element_kinds WHERE kind = :k"), {"k": kind})
            .first()
        )
        return str(row[0]) if row else None

    def upsert_kinds(self, tx: Transaction, owner: str, kinds: Sequence[ElementKind]) -> None:
        for kind in kinds:
            conn(tx).execute(
                text(
                    "INSERT INTO workspace_element_kinds(kind, owner, label_prefix) VALUES (:k, :o, :p) "
                    "ON CONFLICT(kind) DO UPDATE SET owner = excluded.owner, label_prefix = excluded.label_prefix"
                ),
                {"k": kind.kind, "o": owner, "p": kind.label_prefix},
            )

    def next_number(self, tx: Transaction, project_uid: str, prefix: str) -> int:
        connection = conn(tx)
        connection.execute(
            text(
                "INSERT INTO workspace_label_counters(project_uid, prefix, last) VALUES (:p, :x, 1) "
                "ON CONFLICT(project_uid, prefix) DO UPDATE SET last = last + 1"
            ),
            {"p": project_uid, "x": prefix},
        )
        row = connection.execute(
            text("SELECT last FROM workspace_label_counters WHERE project_uid = :p AND prefix = :x"),
            {"p": project_uid, "x": prefix},
        ).one()
        return int(row[0])

    def raise_counter(self, tx: Transaction, project_uid: str, prefix: str, number: int) -> None:
        conn(tx).execute(
            text(
                "INSERT INTO workspace_label_counters(project_uid, prefix, last) VALUES (:p, :x, :n) "
                "ON CONFLICT(project_uid, prefix) DO UPDATE SET last = MAX(last, :n)"
            ),
            {"p": project_uid, "x": prefix, "n": number},
        )

    def insert(self, tx: Transaction, element: Element) -> None:
        conn(tx).execute(
            insert(elements).values(
                uid=element.uid,
                project_uid=element.project_uid,
                kind=element.kind,
                label=element.label,
                revision=element.revision,
                created_at=element.created_at.isoformat(),
                updated_at=element.updated_at.isoformat(),
                deleted_at=element.deleted_at.isoformat() if element.deleted_at else None,
                title=element.title,
            )
        )

    def add_history(self, tx: Transaction, project_uid: str, label: str, element_uid: str) -> None:
        conn(tx).execute(
            text("INSERT INTO workspace_label_history(project_uid, label, element_uid) VALUES (:p, :l, :e)"),
            {"p": project_uid, "l": label, "e": element_uid},
        )

    def get(self, tx: Transaction, uid: str) -> Element | None:
        row = conn(tx).execute(select(elements).where(elements.c.uid == uid)).first()
        return _element(row) if row else None

    def find_uid_by_label(self, tx: Transaction, project_uid: str, label: str) -> str | None:
        row = (
            conn(tx)
            .execute(
                text("SELECT element_uid FROM workspace_label_history WHERE project_uid = :p AND label = :l"),
                {"p": project_uid, "l": label},
            )
            .first()
        )
        return str(row[0]) if row else None

    def set_kind_and_label(self, tx: Transaction, uid: str, kind: str, label: str, now: datetime) -> None:
        conn(tx).execute(
            update(elements)
            .where(elements.c.uid == uid)
            .values(kind=kind, label=label, updated_at=now.isoformat(), revision=elements.c.revision + 1)
        )

    def bump_revision(self, tx: Transaction, uid: str, expected: int, now: datetime) -> int:
        return update_with_revision(
            conn(tx), elements, elements.c.uid == uid, expected, {"updated_at": now.isoformat()}
        )

    def set_deleted(self, tx: Transaction, uid: str, at: datetime | None, now: datetime) -> None:
        conn(tx).execute(
            update(elements)
            .where(elements.c.uid == uid)
            .values(
                deleted_at=at.isoformat() if at else None, updated_at=now.isoformat(), revision=elements.c.revision + 1
            )
        )

    def delete(self, tx: Transaction, uid: str) -> None:
        conn(tx).execute(delete(elements).where(elements.c.uid == uid))

    def set_title(self, tx: Transaction, uid: str, title: str, now: datetime) -> None:
        conn(tx).execute(update(elements).where(elements.c.uid == uid).values(title=title, updated_at=now.isoformat()))

    def search(self, tx: Transaction, query: str, limit: int) -> list[Element]:
        """Nicht gelöschte Elemente aller Projekte, deren Label oder Titel `query` enthält (ohne Groß/Klein)."""
        pattern = "%" + query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        rows = conn(tx).execute(
            select(elements)
            .where(elements.c.deleted_at.is_(None))
            .where(elements.c.label.ilike(pattern, escape="\\") | elements.c.title.ilike(pattern, escape="\\"))
            .order_by(elements.c.label, elements.c.uid)
            .limit(limit)
        )
        return [_element(row) for row in rows]

    def list_deleted(self, tx: Transaction, project_uids: Sequence[str] | None, query: str) -> list[Element]:
        """Elemente im Papierkorb, neueste zuerst; optional nur aus diesen Projekten und mit `query` in Label/Titel."""
        statement = select(elements).where(elements.c.deleted_at.is_not(None))
        if project_uids is not None:
            statement = statement.where(elements.c.project_uid.in_(list(project_uids)))
        if query.strip():
            pattern = "%" + query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            statement = statement.where(
                elements.c.label.ilike(pattern, escape="\\") | elements.c.title.ilike(pattern, escape="\\")
            )
        rows = conn(tx).execute(statement.order_by(elements.c.deleted_at.desc(), elements.c.label, elements.c.uid))
        return [_element(row) for row in rows]


class SqlLinkStore:
    def insert(self, tx: Transaction, link: Link) -> None:
        conn(tx).execute(
            insert(links).values(
                uid=link.uid,
                from_uid=link.from_uid,
                to_uid=link.to_uid,
                role=link.role,
                created_at=link.created_at.isoformat(),
            )
        )

    def get(self, tx: Transaction, uid: str) -> Link | None:
        row = conn(tx).execute(select(links).where(links.c.uid == uid)).first()
        return _link(row) if row else None

    def find(self, tx: Transaction, from_uid: str, to_uid: str, role: str) -> Link | None:
        row = (
            conn(tx)
            .execute(select(links).where(links.c.from_uid == from_uid, links.c.to_uid == to_uid, links.c.role == role))
            .first()
        )
        return _link(row) if row else None

    def delete(self, tx: Transaction, uid: str) -> None:
        conn(tx).execute(delete(links).where(links.c.uid == uid))

    def outgoing(self, tx: Transaction, uid: str) -> list[Link]:
        rows = conn(tx).execute(select(links).where(links.c.from_uid == uid).order_by(links.c.created_at, links.c.uid))
        return [_link(row) for row in rows]

    def incoming(self, tx: Transaction, uid: str) -> list[Link]:
        rows = conn(tx).execute(select(links).where(links.c.to_uid == uid).order_by(links.c.created_at, links.c.uid))
        return [_link(row) for row in rows]


__all__ = ["SqlElementStore", "SqlLinkStore", "SqlProjectStore", "SyncDirection"]

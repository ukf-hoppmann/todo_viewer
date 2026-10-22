from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.backlog.application.ports import TrashedDocument, TrashedListing


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _document(row: object) -> TrashedDocument:
    r = row  # sqlalchemy Row
    return TrashedDocument(
        r.uid,  # type: ignore[attr-defined]
        r.item_uid,  # type: ignore[attr-defined]
        r.name,  # type: ignore[attr-defined]
        r.kind,  # type: ignore[attr-defined]
        r.content,  # type: ignore[attr-defined]
        r.summary,  # type: ignore[attr-defined]
        datetime.fromisoformat(r.deleted_at),  # type: ignore[attr-defined]
    )


class SqlTrashedDocumentRepository:
    def insert(self, tx: Transaction, document: TrashedDocument) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO backlog_trashed_documents(uid, item_uid, name, kind, content, summary, deleted_at) "
                "VALUES (:uid, :item, :name, :kind, :content, :summary, :at)"
            ),
            {
                "uid": document.uid,
                "item": document.item_uid,
                "name": document.name,
                "kind": document.kind,
                "content": document.content,
                "summary": document.summary,
                "at": document.deleted_at.isoformat(),
            },
        )

    def get(self, tx: Transaction, uid: str) -> TrashedDocument | None:
        row = _conn(tx).execute(text("SELECT * FROM backlog_trashed_documents WHERE uid = :u"), {"u": uid}).first()
        return _document(row) if row else None

    def list_deleted(self, tx: Transaction, project_uids: Sequence[str] | None, query: str) -> list[TrashedListing]:
        sql = (
            "SELECT d.*, e.label AS item_label, e.project_uid AS project_uid FROM backlog_trashed_documents d "
            "JOIN workspace_elements e ON e.uid = d.item_uid WHERE 1 = 1"
        )
        params: dict[str, object] = {}
        if project_uids is not None:
            if not project_uids:
                return []
            names = {f"p{n}": uid for n, uid in enumerate(project_uids)}
            sql += " AND e.project_uid IN (" + ", ".join(f":{name}" for name in names) + ")"
            params.update(names)
        if query:
            sql += " AND (lower(e.label) LIKE :q OR lower(d.name) LIKE :q)"
            params["q"] = f"%{query.lower()}%"
        rows = _conn(tx).execute(text(sql + " ORDER BY d.deleted_at DESC, d.uid DESC"), params)
        return [TrashedListing(_document(row), row.item_label, row.project_uid) for row in rows]

    def delete(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM backlog_trashed_documents WHERE uid = :u"), {"u": uid})

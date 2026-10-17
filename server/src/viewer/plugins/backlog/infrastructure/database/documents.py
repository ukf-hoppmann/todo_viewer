from __future__ import annotations

from datetime import datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import VersionConflict
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.backlog.application.ports import Document


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _document(row: object) -> Document:
    r = row  # sqlalchemy Row
    return Document(r.item_uid, r.name, r.kind, r.content, r.revision, datetime.fromisoformat(r.updated_at))  # type: ignore[attr-defined]


class SqlDocumentRepository:
    def list_for(self, tx: Transaction, item_uid: str) -> list[Document]:
        rows = _conn(tx).execute(
            text("SELECT * FROM backlog_documents WHERE item_uid = :u ORDER BY kind, name"), {"u": item_uid}
        )
        return [_document(row) for row in rows]

    def get(self, tx: Transaction, item_uid: str, name: str) -> Document | None:
        row = (
            _conn(tx)
            .execute(
                text("SELECT * FROM backlog_documents WHERE item_uid = :u AND name = :n"), {"u": item_uid, "n": name}
            )
            .first()
        )
        return _document(row) if row else None

    def insert(self, tx: Transaction, document: Document) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO backlog_documents(item_uid, name, kind, content, revision, updated_at) "
                "VALUES (:u, :n, :k, :c, :r, :t)"
            ),
            {
                "u": document.item_uid,
                "n": document.name,
                "k": document.kind,
                "c": document.content,
                "r": document.revision,
                "t": document.updated_at.isoformat(),
            },
        )

    def update(self, tx: Transaction, item_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        result = _conn(tx).execute(
            text(
                "UPDATE backlog_documents SET content = :c, revision = revision + 1, updated_at = :t "
                "WHERE item_uid = :u AND name = :n AND revision = :r"
            ),
            {"c": content, "t": at.isoformat(), "u": item_uid, "n": name, "r": expected},
        )
        if result.rowcount != 1:
            raise VersionConflict(
                "Das Dokument wurde inzwischen geändert", details={"name": name, "expected": expected}
            )
        return expected + 1

    def rename(self, tx: Transaction, item_uid: str, old: str, new: str) -> None:
        _conn(tx).execute(
            text("UPDATE backlog_documents SET name = :new WHERE item_uid = :u AND name = :old"),
            {"new": new, "u": item_uid, "old": old},
        )

    def delete(self, tx: Transaction, item_uid: str, name: str) -> None:
        _conn(tx).execute(
            text("DELETE FROM backlog_documents WHERE item_uid = :u AND name = :n"), {"u": item_uid, "n": name}
        )

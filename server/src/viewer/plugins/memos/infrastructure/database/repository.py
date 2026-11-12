from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import VersionConflict
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.memos.application.ports import Document
from viewer.plugins.memos.domain.documents import document_kind
from viewer.plugins.memos.domain.due import Trigger
from viewer.plugins.memos.domain.hints import Hint
from viewer.plugins.memos.domain.model import (
    DEFAULT_MAX_TOPIC_DEPTH,
    DEFAULT_REVIEW_DAYS,
    Memo,
    MemosSettings,
    Topic,
)

_MEMO_SELECT = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at,
       n.summary, n.body, n.status, n.topic_uid, n.review_at, n.trigger_mode, n.archived
FROM memos_memos n JOIN workspace_elements e ON e.uid = n.uid
"""
_TOPIC_SELECT = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at,
       t.name, t.parent_uid, t.due_at, t.archived_at, t.system
FROM memos_topics t JOIN workspace_elements e ON e.uid = t.uid
"""


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _moment(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _in_clause(prefix: str, values: Sequence[str]) -> tuple[str, dict[str, str]]:
    names = {f"{prefix}{n}": value for n, value in enumerate(values)}
    return ", ".join(f":{name}" for name in names), names


class SqlMemoRepository:
    def insert(self, tx: Transaction, memo: Memo) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO memos_memos(uid, summary, body, status, topic_uid, review_at, trigger_mode, archived) "
                "VALUES (:uid, :summary, :body, :status, :topic, :review, :mode, :archived)"
            ),
            self._params(memo),
        )

    def update(self, tx: Transaction, memo: Memo) -> None:
        _conn(tx).execute(
            text(
                "UPDATE memos_memos SET summary = :summary, body = :body, status = :status, topic_uid = :topic, "
                "review_at = :review, trigger_mode = :mode, archived = :archived WHERE uid = :uid"
            ),
            self._params(memo),
        )

    @staticmethod
    def _params(memo: Memo) -> dict[str, object]:
        return {
            "uid": memo.uid,
            "summary": memo.summary,
            "body": memo.body,
            "status": memo.status,
            "topic": memo.topic_uid,
            "review": _iso(memo.review_at),
            "mode": memo.trigger_mode,
            "archived": int(memo.archived),
        }

    def get(self, tx: Transaction, uid: str) -> Memo | None:
        rows = self._load(tx, _MEMO_SELECT + " WHERE n.uid = :u", {"u": uid})
        return rows[0] if rows else None

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Memo]:
        query = _MEMO_SELECT + " WHERE 1 = 1"
        params: dict[str, object] = {}
        if not include_deleted:
            query += " AND e.deleted_at IS NULL"
        if project_uids is not None:
            if not project_uids:
                return []
            marks, names = _in_clause("p", project_uids)
            query += f" AND e.project_uid IN ({marks})"
            params.update(names)
        return self._load(tx, query + " ORDER BY e.project_uid, e.label", params)

    def in_topic(self, tx: Transaction, topic_uid: str) -> list[Memo]:
        return self._load(tx, _MEMO_SELECT + " WHERE n.topic_uid = :t ORDER BY e.label", {"t": topic_uid})

    def delete(self, tx: Transaction, uid: str) -> None:
        connection = _conn(tx)
        connection.execute(text("DELETE FROM memos_documents WHERE memo_uid = :u"), {"u": uid})
        connection.execute(text("DELETE FROM memos_triggers WHERE memo_uid = :u"), {"u": uid})
        connection.execute(text("DELETE FROM memos_hints WHERE subject_uid = :u OR source_uid = :u"), {"u": uid})
        connection.execute(text("DELETE FROM memos_memos WHERE uid = :u"), {"u": uid})

    def _load(self, tx: Transaction, query: str, params: dict[str, object]) -> list[Memo]:
        connection = _conn(tx)
        rows = connection.execute(text(query), params).all()
        if not rows:
            return []
        marks, names = _in_clause("d", [row.uid for row in rows])
        document_rows = connection.execute(
            text(f"SELECT memo_uid, name FROM memos_documents WHERE memo_uid IN ({marks}) ORDER BY memo_uid, name"),
            names,
        ).all()
        documents: dict[str, list[str]] = {}
        for row in document_rows:
            documents.setdefault(row.memo_uid, []).append(row.name)
        return [
            Memo(
                uid=row.uid,
                project_uid=row.project_uid,
                label=row.label,
                summary=row.summary,
                body=row.body,
                status=row.status,
                topic_uid=row.topic_uid,
                review_at=_moment(row.review_at),
                trigger_mode=row.trigger_mode,
                archived=bool(row.archived),
                revision=row.revision,
                deleted_at=_moment(row.deleted_at),
                documents=tuple(
                    sorted(
                        documents.get(row.uid, ()),
                        key=lambda name, label=row.label: (document_kind(label, name) != "notes", name),
                    )
                ),
            )
            for row in rows
        ]


class SqlTopicRepository:
    def insert(self, tx: Transaction, topic: Topic) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO memos_topics(uid, name, parent_uid, due_at, archived_at, system) "
                "VALUES (:uid, :name, :parent, :due, :archived, :system)"
            ),
            self._params(topic),
        )

    def update(self, tx: Transaction, topic: Topic) -> None:
        _conn(tx).execute(
            text(
                "UPDATE memos_topics SET name = :name, parent_uid = :parent, due_at = :due, archived_at = :archived, "
                "system = :system WHERE uid = :uid"
            ),
            self._params(topic),
        )

    @staticmethod
    def _params(topic: Topic) -> dict[str, object]:
        return {
            "uid": topic.uid,
            "name": topic.name,
            "parent": topic.parent_uid,
            "due": _iso(topic.due_at),
            "archived": _iso(topic.archived_at),
            "system": int(topic.system),
        }

    def get(self, tx: Transaction, uid: str) -> Topic | None:
        rows = self._load(tx, _TOPIC_SELECT + " WHERE t.uid = :u", {"u": uid})
        return rows[0] if rows else None

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Topic]:
        query = _TOPIC_SELECT + " WHERE 1 = 1"
        params: dict[str, object] = {}
        if not include_deleted:
            query += " AND e.deleted_at IS NULL"
        if project_uids is not None:
            if not project_uids:
                return []
            marks, names = _in_clause("p", project_uids)
            query += f" AND e.project_uid IN ({marks})"
            params.update(names)
        return self._load(tx, query + " ORDER BY e.project_uid, e.label", params)

    def children(self, tx: Transaction, uid: str) -> list[Topic]:
        return self._load(tx, _TOPIC_SELECT + " WHERE t.parent_uid = :u ORDER BY e.label", {"u": uid})

    def archive_topic_of(self, tx: Transaction, project_uid: str) -> Topic | None:
        rows = self._load(
            tx, _TOPIC_SELECT + " WHERE t.system = 1 AND e.project_uid = :p ORDER BY e.label", {"p": project_uid}
        )
        return rows[0] if rows else None

    def delete(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM memos_topics WHERE uid = :u"), {"u": uid})

    @staticmethod
    def _load(tx: Transaction, query: str, params: dict[str, object]) -> list[Topic]:
        return [
            Topic(
                uid=row.uid,
                project_uid=row.project_uid,
                label=row.label,
                name=row.name,
                parent_uid=row.parent_uid,
                due_at=_moment(row.due_at),
                archived_at=_moment(row.archived_at),
                system=bool(row.system),
                revision=row.revision,
                deleted_at=_moment(row.deleted_at),
            )
            for row in _conn(tx).execute(text(query), params).all()
        ]


class SqlDocumentRepository:
    def list_for(self, tx: Transaction, memo_uid: str) -> list[Document]:
        rows = _conn(tx).execute(
            text(
                "SELECT d.*, e.label FROM memos_documents d JOIN workspace_elements e ON e.uid = d.memo_uid "
                "WHERE d.memo_uid = :u ORDER BY d.name"
            ),
            {"u": memo_uid},
        )
        documents = [self._document(row) for row in rows]
        return sorted(documents, key=lambda d: (d.kind != "notes", d.name))

    def get(self, tx: Transaction, memo_uid: str, name: str) -> Document | None:
        row = (
            _conn(tx)
            .execute(
                text(
                    "SELECT d.*, e.label FROM memos_documents d JOIN workspace_elements e ON e.uid = d.memo_uid "
                    "WHERE d.memo_uid = :u AND d.name = :n"
                ),
                {"u": memo_uid, "n": name},
            )
            .first()
        )
        return self._document(row) if row else None

    @staticmethod
    def _document(row: object) -> Document:
        r = row
        kind = document_kind(r.label, r.name) or "spec"  # type: ignore[attr-defined]
        return Document(r.memo_uid, r.name, kind, r.content, r.revision, datetime.fromisoformat(r.updated_at))  # type: ignore[attr-defined]

    def insert(self, tx: Transaction, document: Document) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO memos_documents(memo_uid, name, content, revision, updated_at) VALUES (:u, :n, :c, :r, :t)"
            ),
            {
                "u": document.memo_uid,
                "n": document.name,
                "c": document.content,
                "r": document.revision,
                "t": document.updated_at.isoformat(),
            },
        )

    def update(self, tx: Transaction, memo_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        result = _conn(tx).execute(
            text(
                "UPDATE memos_documents SET content = :c, revision = revision + 1, updated_at = :t "
                "WHERE memo_uid = :u AND name = :n AND revision = :r"
            ),
            {"c": content, "t": at.isoformat(), "u": memo_uid, "n": name, "r": expected},
        )
        if result.rowcount != 1:
            raise VersionConflict(
                "Das Dokument wurde inzwischen geändert", details={"name": name, "expected": expected}
            )
        return expected + 1

    def delete(self, tx: Transaction, memo_uid: str, name: str) -> None:
        _conn(tx).execute(
            text("DELETE FROM memos_documents WHERE memo_uid = :u AND name = :n"), {"u": memo_uid, "n": name}
        )


class SqlSettingsRepository:
    def load(self, tx: Transaction) -> MemosSettings:
        values = {row.key: row.value for row in _conn(tx).execute(text("SELECT key, value FROM memos_settings"))}
        return MemosSettings(
            int(values.get("max_topic_depth", DEFAULT_MAX_TOPIC_DEPTH)),
            int(values.get("review_days", DEFAULT_REVIEW_DAYS)),
        )

    def save(self, tx: Transaction, settings: MemosSettings) -> None:
        for key, value in (("max_topic_depth", settings.max_topic_depth), ("review_days", settings.review_days)):
            _conn(tx).execute(
                text(
                    "INSERT INTO memos_settings(key, value) VALUES (:k, :v) ON CONFLICT(key) DO UPDATE SET value = :v"
                ),
                {"k": key, "v": str(value)},
            )


def _trigger(row: object) -> Trigger:
    r = row
    return Trigger(
        r.uid,  # type: ignore[attr-defined]
        r.memo_uid,  # type: ignore[attr-defined]
        r.kind,  # type: ignore[attr-defined]
        r.target_uid,  # type: ignore[attr-defined]
        r.status,  # type: ignore[attr-defined]
        _moment(r.fired_at),  # type: ignore[attr-defined]
        bool(r.already_met),  # type: ignore[attr-defined]
        r.link_uid,  # type: ignore[attr-defined]
    )


class SqlTriggerRepository:
    def for_memos(self, tx: Transaction, memo_uids: Sequence[str]) -> dict[str, list[Trigger]]:
        if not memo_uids:
            return {}
        marks, names = _in_clause("n", memo_uids)
        rows = _conn(tx).execute(
            text(f"SELECT * FROM memos_triggers WHERE memo_uid IN ({marks}) ORDER BY memo_uid, rowid"), names
        )
        found: dict[str, list[Trigger]] = {}
        for row in rows:
            found.setdefault(row.memo_uid, []).append(_trigger(row))
        return found

    def get(self, tx: Transaction, uid: str) -> Trigger | None:
        row = _conn(tx).execute(text("SELECT * FROM memos_triggers WHERE uid = :u"), {"u": uid}).first()
        return _trigger(row) if row else None

    def insert(self, tx: Transaction, trigger: Trigger) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO memos_triggers(uid, memo_uid, kind, target_uid, status, fired_at, already_met, link_uid) "
                "VALUES (:uid, :memo, :kind, :target, :status, :fired, :met, :link)"
            ),
            self._params(trigger),
        )

    def update(self, tx: Transaction, trigger: Trigger) -> None:
        _conn(tx).execute(
            text("UPDATE memos_triggers SET fired_at = :fired, already_met = :met, link_uid = :link WHERE uid = :uid"),
            self._params(trigger),
        )

    @staticmethod
    def _params(trigger: Trigger) -> dict[str, object]:
        return {
            "uid": trigger.uid,
            "memo": trigger.memo_uid,
            "kind": trigger.kind,
            "target": trigger.target_uid,
            "status": trigger.status,
            "fired": _iso(trigger.fired_at),
            "met": int(trigger.already_met),
            "link": trigger.link_uid,
        }

    def delete(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM memos_triggers WHERE uid = :u"), {"u": uid})

    def waiting_on(self, tx: Transaction, target_uid: str, status: str) -> list[Trigger]:
        rows = _conn(tx).execute(
            text(
                "SELECT * FROM memos_triggers WHERE kind = 'event' AND target_uid = :t AND status = :s "
                "AND fired_at IS NULL ORDER BY rowid"
            ),
            {"t": target_uid, "s": status},
        )
        return [_trigger(row) for row in rows]


def _hint(row: object) -> Hint:
    r = row
    return Hint(
        r.uid,  # type: ignore[attr-defined]
        r.side,  # type: ignore[attr-defined]
        r.subject_uid,  # type: ignore[attr-defined]
        r.source_uid,  # type: ignore[attr-defined]
        r.kind,  # type: ignore[attr-defined]
        datetime.fromisoformat(r.created_at),  # type: ignore[attr-defined]
        _moment(r.decided_at),  # type: ignore[attr-defined]
        r.decision,  # type: ignore[attr-defined]
    )


class SqlHintRepository:
    def insert(self, tx: Transaction, hint: Hint) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO memos_hints(uid, side, subject_uid, source_uid, kind, created_at, decided_at, decision) "
                "VALUES (:uid, :side, :subject, :source, :kind, :created, :decided, :decision)"
            ),
            {
                "uid": hint.uid,
                "side": hint.side,
                "subject": hint.subject_uid,
                "source": hint.source_uid,
                "kind": hint.kind,
                "created": hint.created_at.isoformat(),
                "decided": _iso(hint.decided_at),
                "decision": hint.decision,
            },
        )

    def get(self, tx: Transaction, uid: str) -> Hint | None:
        row = _conn(tx).execute(text("SELECT * FROM memos_hints WHERE uid = :u"), {"u": uid}).first()
        return _hint(row) if row else None

    def decide(self, tx: Transaction, uid: str, decision: str, at: datetime) -> None:
        _conn(tx).execute(
            text("UPDATE memos_hints SET decided_at = :t, decision = :d WHERE uid = :u"),
            {"t": at.isoformat(), "d": decision, "u": uid},
        )

    def open_for(self, tx: Transaction, subject_uids: Sequence[str]) -> dict[str, list[Hint]]:
        if not subject_uids:
            return {}
        marks, names = _in_clause("s", subject_uids)
        rows = _conn(tx).execute(
            text(
                f"SELECT * FROM memos_hints WHERE subject_uid IN ({marks}) AND decided_at IS NULL "
                "ORDER BY created_at, rowid"
            ),
            names,
        )
        found: dict[str, list[Hint]] = {}
        for row in rows:
            found.setdefault(row.subject_uid, []).append(_hint(row))
        return found

    def find_open(self, tx: Transaction, subject_uid: str, source_uid: str, kind: str) -> Hint | None:
        row = (
            _conn(tx)
            .execute(
                text(
                    "SELECT * FROM memos_hints WHERE subject_uid = :s AND source_uid = :o AND kind = :k "
                    "AND decided_at IS NULL"
                ),
                {"s": subject_uid, "o": source_uid, "k": kind},
            )
            .first()
        )
        return _hint(row) if row else None

    def delete_for(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM memos_hints WHERE subject_uid = :u OR source_uid = :u"), {"u": uid})

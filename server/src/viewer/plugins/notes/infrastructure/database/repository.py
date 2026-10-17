from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.domain.errors import VersionConflict
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.notes.application.ports import Document
from viewer.plugins.notes.domain.documents import document_kind
from viewer.plugins.notes.domain.due import Trigger
from viewer.plugins.notes.domain.model import (
    DEFAULT_MAX_TOPIC_DEPTH,
    DEFAULT_REVIEW_DAYS,
    Note,
    NotesSettings,
    Topic,
)
from viewer.plugins.notes.domain.notices import Notice

_NOTE_SELECT = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at,
       n.summary, n.body, n.status, n.topic_uid, n.review_at, n.trigger_mode, n.archived
FROM notes_notes n JOIN workspace_elements e ON e.uid = n.uid
"""
_TOPIC_SELECT = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at,
       t.name, t.parent_uid, t.due_at, t.archived_at, t.system
FROM notes_topics t JOIN workspace_elements e ON e.uid = t.uid
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


class SqlNoteRepository:
    def insert(self, tx: Transaction, note: Note) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO notes_notes(uid, summary, body, status, topic_uid, review_at, trigger_mode, archived) "
                "VALUES (:uid, :summary, :body, :status, :topic, :review, :mode, :archived)"
            ),
            self._params(note),
        )

    def update(self, tx: Transaction, note: Note) -> None:
        _conn(tx).execute(
            text(
                "UPDATE notes_notes SET summary = :summary, body = :body, status = :status, topic_uid = :topic, "
                "review_at = :review, trigger_mode = :mode, archived = :archived WHERE uid = :uid"
            ),
            self._params(note),
        )

    @staticmethod
    def _params(note: Note) -> dict[str, object]:
        return {
            "uid": note.uid,
            "summary": note.summary,
            "body": note.body,
            "status": note.status,
            "topic": note.topic_uid,
            "review": _iso(note.review_at),
            "mode": note.trigger_mode,
            "archived": int(note.archived),
        }

    def get(self, tx: Transaction, uid: str) -> Note | None:
        rows = self._load(tx, _NOTE_SELECT + " WHERE n.uid = :u", {"u": uid})
        return rows[0] if rows else None

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Note]:
        query = _NOTE_SELECT + " WHERE 1 = 1"
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

    def in_topic(self, tx: Transaction, topic_uid: str) -> list[Note]:
        return self._load(tx, _NOTE_SELECT + " WHERE n.topic_uid = :t ORDER BY e.label", {"t": topic_uid})

    def delete(self, tx: Transaction, uid: str) -> None:
        connection = _conn(tx)
        connection.execute(text("DELETE FROM notes_documents WHERE note_uid = :u"), {"u": uid})
        connection.execute(text("DELETE FROM notes_triggers WHERE note_uid = :u"), {"u": uid})
        connection.execute(text("DELETE FROM notes_notices WHERE subject_uid = :u OR source_uid = :u"), {"u": uid})
        connection.execute(text("DELETE FROM notes_notes WHERE uid = :u"), {"u": uid})

    def _load(self, tx: Transaction, query: str, params: dict[str, object]) -> list[Note]:
        connection = _conn(tx)
        rows = connection.execute(text(query), params).all()
        if not rows:
            return []
        marks, names = _in_clause("d", [row.uid for row in rows])
        document_rows = connection.execute(
            text(f"SELECT note_uid, name FROM notes_documents WHERE note_uid IN ({marks}) ORDER BY note_uid, name"),
            names,
        ).all()
        documents: dict[str, list[str]] = {}
        for row in document_rows:
            documents.setdefault(row.note_uid, []).append(row.name)
        return [
            Note(
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
                "INSERT INTO notes_topics(uid, name, parent_uid, due_at, archived_at, system) "
                "VALUES (:uid, :name, :parent, :due, :archived, :system)"
            ),
            self._params(topic),
        )

    def update(self, tx: Transaction, topic: Topic) -> None:
        _conn(tx).execute(
            text(
                "UPDATE notes_topics SET name = :name, parent_uid = :parent, due_at = :due, archived_at = :archived, "
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
        _conn(tx).execute(text("DELETE FROM notes_topics WHERE uid = :u"), {"u": uid})

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
    def list_for(self, tx: Transaction, note_uid: str) -> list[Document]:
        rows = _conn(tx).execute(
            text(
                "SELECT d.*, e.label FROM notes_documents d JOIN workspace_elements e ON e.uid = d.note_uid "
                "WHERE d.note_uid = :u ORDER BY d.name"
            ),
            {"u": note_uid},
        )
        documents = [self._document(row) for row in rows]
        return sorted(documents, key=lambda d: (d.kind != "notes", d.name))

    def get(self, tx: Transaction, note_uid: str, name: str) -> Document | None:
        row = (
            _conn(tx)
            .execute(
                text(
                    "SELECT d.*, e.label FROM notes_documents d JOIN workspace_elements e ON e.uid = d.note_uid "
                    "WHERE d.note_uid = :u AND d.name = :n"
                ),
                {"u": note_uid, "n": name},
            )
            .first()
        )
        return self._document(row) if row else None

    @staticmethod
    def _document(row: object) -> Document:
        r = row
        kind = document_kind(r.label, r.name) or "spec"  # type: ignore[attr-defined]
        return Document(r.note_uid, r.name, kind, r.content, r.revision, datetime.fromisoformat(r.updated_at))  # type: ignore[attr-defined]

    def insert(self, tx: Transaction, document: Document) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO notes_documents(note_uid, name, content, revision, updated_at) VALUES (:u, :n, :c, :r, :t)"
            ),
            {
                "u": document.note_uid,
                "n": document.name,
                "c": document.content,
                "r": document.revision,
                "t": document.updated_at.isoformat(),
            },
        )

    def update(self, tx: Transaction, note_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        result = _conn(tx).execute(
            text(
                "UPDATE notes_documents SET content = :c, revision = revision + 1, updated_at = :t "
                "WHERE note_uid = :u AND name = :n AND revision = :r"
            ),
            {"c": content, "t": at.isoformat(), "u": note_uid, "n": name, "r": expected},
        )
        if result.rowcount != 1:
            raise VersionConflict(
                "Das Dokument wurde inzwischen geändert", details={"name": name, "expected": expected}
            )
        return expected + 1


class SqlSettingsRepository:
    def load(self, tx: Transaction) -> NotesSettings:
        values = {row.key: row.value for row in _conn(tx).execute(text("SELECT key, value FROM notes_settings"))}
        return NotesSettings(
            int(values.get("max_topic_depth", DEFAULT_MAX_TOPIC_DEPTH)),
            int(values.get("review_days", DEFAULT_REVIEW_DAYS)),
        )

    def save(self, tx: Transaction, settings: NotesSettings) -> None:
        for key, value in (("max_topic_depth", settings.max_topic_depth), ("review_days", settings.review_days)):
            _conn(tx).execute(
                text(
                    "INSERT INTO notes_settings(key, value) VALUES (:k, :v) ON CONFLICT(key) DO UPDATE SET value = :v"
                ),
                {"k": key, "v": str(value)},
            )


def _trigger(row: object) -> Trigger:
    r = row
    return Trigger(
        r.uid,  # type: ignore[attr-defined]
        r.note_uid,  # type: ignore[attr-defined]
        r.kind,  # type: ignore[attr-defined]
        r.target_uid,  # type: ignore[attr-defined]
        r.status,  # type: ignore[attr-defined]
        _moment(r.fired_at),  # type: ignore[attr-defined]
        bool(r.already_met),  # type: ignore[attr-defined]
        r.link_uid,  # type: ignore[attr-defined]
    )


class SqlTriggerRepository:
    def for_notes(self, tx: Transaction, note_uids: Sequence[str]) -> dict[str, list[Trigger]]:
        if not note_uids:
            return {}
        marks, names = _in_clause("n", note_uids)
        rows = _conn(tx).execute(
            text(f"SELECT * FROM notes_triggers WHERE note_uid IN ({marks}) ORDER BY note_uid, rowid"), names
        )
        found: dict[str, list[Trigger]] = {}
        for row in rows:
            found.setdefault(row.note_uid, []).append(_trigger(row))
        return found

    def get(self, tx: Transaction, uid: str) -> Trigger | None:
        row = _conn(tx).execute(text("SELECT * FROM notes_triggers WHERE uid = :u"), {"u": uid}).first()
        return _trigger(row) if row else None

    def insert(self, tx: Transaction, trigger: Trigger) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO notes_triggers(uid, note_uid, kind, target_uid, status, fired_at, already_met, link_uid) "
                "VALUES (:uid, :note, :kind, :target, :status, :fired, :met, :link)"
            ),
            self._params(trigger),
        )

    def update(self, tx: Transaction, trigger: Trigger) -> None:
        _conn(tx).execute(
            text("UPDATE notes_triggers SET fired_at = :fired, already_met = :met, link_uid = :link WHERE uid = :uid"),
            self._params(trigger),
        )

    @staticmethod
    def _params(trigger: Trigger) -> dict[str, object]:
        return {
            "uid": trigger.uid,
            "note": trigger.note_uid,
            "kind": trigger.kind,
            "target": trigger.target_uid,
            "status": trigger.status,
            "fired": _iso(trigger.fired_at),
            "met": int(trigger.already_met),
            "link": trigger.link_uid,
        }

    def delete(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM notes_triggers WHERE uid = :u"), {"u": uid})

    def waiting_on(self, tx: Transaction, target_uid: str, status: str) -> list[Trigger]:
        rows = _conn(tx).execute(
            text(
                "SELECT * FROM notes_triggers WHERE kind = 'event' AND target_uid = :t AND status = :s "
                "AND fired_at IS NULL ORDER BY rowid"
            ),
            {"t": target_uid, "s": status},
        )
        return [_trigger(row) for row in rows]


def _notice(row: object) -> Notice:
    r = row
    return Notice(
        r.uid,  # type: ignore[attr-defined]
        r.side,  # type: ignore[attr-defined]
        r.subject_uid,  # type: ignore[attr-defined]
        r.source_uid,  # type: ignore[attr-defined]
        r.kind,  # type: ignore[attr-defined]
        datetime.fromisoformat(r.created_at),  # type: ignore[attr-defined]
        _moment(r.decided_at),  # type: ignore[attr-defined]
        r.decision,  # type: ignore[attr-defined]
    )


class SqlNoticeRepository:
    def insert(self, tx: Transaction, notice: Notice) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO notes_notices(uid, side, subject_uid, source_uid, kind, created_at, decided_at, decision) "
                "VALUES (:uid, :side, :subject, :source, :kind, :created, :decided, :decision)"
            ),
            {
                "uid": notice.uid,
                "side": notice.side,
                "subject": notice.subject_uid,
                "source": notice.source_uid,
                "kind": notice.kind,
                "created": notice.created_at.isoformat(),
                "decided": _iso(notice.decided_at),
                "decision": notice.decision,
            },
        )

    def get(self, tx: Transaction, uid: str) -> Notice | None:
        row = _conn(tx).execute(text("SELECT * FROM notes_notices WHERE uid = :u"), {"u": uid}).first()
        return _notice(row) if row else None

    def decide(self, tx: Transaction, uid: str, decision: str, at: datetime) -> None:
        _conn(tx).execute(
            text("UPDATE notes_notices SET decided_at = :t, decision = :d WHERE uid = :u"),
            {"t": at.isoformat(), "d": decision, "u": uid},
        )

    def open_for(self, tx: Transaction, subject_uids: Sequence[str]) -> dict[str, list[Notice]]:
        if not subject_uids:
            return {}
        marks, names = _in_clause("s", subject_uids)
        rows = _conn(tx).execute(
            text(
                f"SELECT * FROM notes_notices WHERE subject_uid IN ({marks}) AND decided_at IS NULL "
                "ORDER BY created_at, rowid"
            ),
            names,
        )
        found: dict[str, list[Notice]] = {}
        for row in rows:
            found.setdefault(row.subject_uid, []).append(_notice(row))
        return found

    def find_open(self, tx: Transaction, subject_uid: str, source_uid: str, kind: str) -> Notice | None:
        row = (
            _conn(tx)
            .execute(
                text(
                    "SELECT * FROM notes_notices WHERE subject_uid = :s AND source_uid = :o AND kind = :k "
                    "AND decided_at IS NULL"
                ),
                {"s": subject_uid, "o": source_uid, "k": kind},
            )
            .first()
        )
        return _notice(row) if row else None

    def delete_for(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM notes_notices WHERE subject_uid = :u OR source_uid = :u"), {"u": uid})

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.alarms.domain.model import Alarm

_SELECT = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at,
       a.at, a.text, a.status, a.target_uid, a.target_text, a.snoozed_until
FROM alarms_alarms a JOIN workspace_elements e ON e.uid = a.uid
"""


def _conn(tx: Transaction) -> Connection:
    assert isinstance(tx, SqlTransaction)
    return tx.connection


def _moment(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class SqlAlarmRepository:
    def insert(self, tx: Transaction, alarm: Alarm) -> None:
        _conn(tx).execute(
            text(
                "INSERT INTO alarms_alarms(uid, at, text, target_uid, target_text, status, snoozed_until) "
                "VALUES (:uid, :at, :text, :target, :target_text, :status, :until)"
            ),
            self._params(alarm),
        )

    def update(self, tx: Transaction, alarm: Alarm) -> None:
        _conn(tx).execute(
            text(
                "UPDATE alarms_alarms SET at = :at, text = :text, target_uid = :target, target_text = :target_text, "
                "status = :status, snoozed_until = :until WHERE uid = :uid"
            ),
            self._params(alarm),
        )

    @staticmethod
    def _params(alarm: Alarm) -> dict[str, object]:
        return {
            "uid": alarm.uid,
            "at": alarm.at.isoformat(),
            "text": alarm.text,
            "target": alarm.target_uid,
            "target_text": alarm.target_text,
            "status": alarm.status,
            "until": alarm.snoozed_until.isoformat() if alarm.snoozed_until else None,
        }

    def get(self, tx: Transaction, uid: str) -> Alarm | None:
        rows = self._load(tx, _SELECT + " WHERE a.uid = :u", {"u": uid})
        return rows[0] if rows else None

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Alarm]:
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
        return self._load(tx, query + " ORDER BY a.at, e.label", params)

    def delete(self, tx: Transaction, uid: str) -> None:
        _conn(tx).execute(text("DELETE FROM alarms_alarms WHERE uid = :u"), {"u": uid})

    @staticmethod
    def _load(tx: Transaction, query: str, params: dict[str, object]) -> list[Alarm]:
        return [
            Alarm(
                uid=row.uid,
                project_uid=row.project_uid,
                label=row.label,
                text=row.text,
                at=datetime.fromisoformat(row.at),
                status=row.status,
                target_uid=row.target_uid,
                target_text=row.target_text,
                snoozed_until=_moment(row.snoozed_until),
                revision=row.revision,
                deleted_at=_moment(row.deleted_at),
            )
            for row in _conn(tx).execute(text(query), params).all()
        ]

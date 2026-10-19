from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Connection, text

from viewer.core.application.ports import Transaction
from viewer.core.infrastructure.database import SqlTransaction
from viewer.plugins.alarms.domain.model import Alarm

_SELECT = """
SELECT e.uid, e.project_uid, e.label, e.revision, e.deleted_at,
       a.at, a.text, a.status, a.target_text, a.snoozed_until, a.done_at,
       a.repeat, a.series_from
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
                "INSERT INTO alarms_alarms(uid, at, text, target_text, status, snoozed_until, done_at, repeat, "
                "series_from) VALUES (:uid, :at, :text, :target_text, :status, :until, :done, :repeat, :series_from)"
            ),
            self._params(alarm),
        )
        self._write_targets(tx, alarm)

    def update(self, tx: Transaction, alarm: Alarm) -> None:
        _conn(tx).execute(
            text(
                "UPDATE alarms_alarms SET at = :at, text = :text, target_text = :target_text, status = :status, "
                "snoozed_until = :until, done_at = :done, repeat = :repeat, series_from = :series_from "
                "WHERE uid = :uid"
            ),
            self._params(alarm),
        )
        self._write_targets(tx, alarm)

    @staticmethod
    def _write_targets(tx: Transaction, alarm: Alarm) -> None:
        connection = _conn(tx)
        connection.execute(text("DELETE FROM alarms_targets WHERE alarm_uid = :u"), {"u": alarm.uid})
        for position, element in enumerate(alarm.targets):
            connection.execute(
                text("INSERT INTO alarms_targets(alarm_uid, position, element_uid) VALUES (:a, :p, :e)"),
                {"a": alarm.uid, "p": position, "e": element},
            )

    @staticmethod
    def _params(alarm: Alarm) -> dict[str, object]:
        return {
            "uid": alarm.uid,
            "at": alarm.at.isoformat(),
            "text": alarm.text,
            "target_text": alarm.target_text,
            "status": alarm.status,
            "until": alarm.snoozed_until.isoformat() if alarm.snoozed_until else None,
            "done": alarm.done_at.isoformat() if alarm.done_at else None,
            "repeat": alarm.repeat,
            "series_from": alarm.series_from.isoformat() if alarm.series_from else None,
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
        _conn(tx).execute(text("DELETE FROM alarms_targets WHERE alarm_uid = :u"), {"u": uid})
        _conn(tx).execute(text("DELETE FROM alarms_alarms WHERE uid = :u"), {"u": uid})

    @staticmethod
    def _load(tx: Transaction, query: str, params: dict[str, object]) -> list[Alarm]:
        targets: dict[str, list[str]] = {}
        for row in _conn(tx).execute(
            text("SELECT alarm_uid, element_uid FROM alarms_targets ORDER BY alarm_uid, position")
        ):
            targets.setdefault(row.alarm_uid, []).append(row.element_uid)
        return [
            Alarm(
                uid=row.uid,
                project_uid=row.project_uid,
                label=row.label,
                text=row.text,
                at=datetime.fromisoformat(row.at),
                status=row.status,
                targets=tuple(targets.get(row.uid, ())),
                target_text=row.target_text,
                snoozed_until=_moment(row.snoozed_until),
                revision=row.revision,
                deleted_at=_moment(row.deleted_at),
                done_at=_moment(row.done_at),
                repeat=row.repeat,
                series_from=_moment(row.series_from),
            )
            for row in _conn(tx).execute(text(query), params).all()
        ]

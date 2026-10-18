"""Migrationen von `alarms`."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration


def _v1(connection: Any) -> None:
    for statement in (
        "CREATE TABLE alarms_statuses (code TEXT PRIMARY KEY)",
        """CREATE TABLE alarms_alarms (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            at TEXT NOT NULL,
            text TEXT NOT NULL,
            target_uid TEXT REFERENCES workspace_elements(uid),
            target_text TEXT,
            status TEXT NOT NULL REFERENCES alarms_statuses(code),
            snoozed_until TEXT
        )""",
        "CREATE INDEX alarms_alarms_status ON alarms_alarms(status)",
    ):
        connection.exec_driver_sql(statement)
    for code in ("Pending", "Due", "Done", "Snoozed"):  # Stand von v1; `Expired` kommt mit v2
        connection.execute(text("INSERT INTO alarms_statuses(code) VALUES (:c)"), {"c": code})


def _v2(connection: Any) -> None:
    """Mehrere Elemente je Wecker (`alarms_targets`, das alte `target_uid` wird übernommen), `done_at` für das
    Aufräumen nach 24 h und der Status `Expired`. Schon erledigte Wecker laufen ab jetzt 24 h weiter."""
    for statement in (
        "INSERT INTO alarms_statuses(code) VALUES ('Expired')",
        "DROP INDEX alarms_alarms_status",
        "ALTER TABLE alarms_alarms RENAME TO alarms_alarms_v1",
        """CREATE TABLE alarms_alarms (
            uid TEXT PRIMARY KEY REFERENCES workspace_elements(uid),
            at TEXT NOT NULL,
            text TEXT NOT NULL,
            target_text TEXT,
            status TEXT NOT NULL REFERENCES alarms_statuses(code),
            snoozed_until TEXT,
            done_at TEXT
        )""",
        """INSERT INTO alarms_alarms(uid, at, text, target_text, status, snoozed_until, done_at)
           SELECT uid, at, text, target_text, status, snoozed_until,
                  CASE WHEN status = 'Done' THEN strftime('%Y-%m-%dT%H:%M:%S+00:00', 'now') END
           FROM alarms_alarms_v1""",
        """CREATE TABLE alarms_targets (
            alarm_uid TEXT NOT NULL REFERENCES alarms_alarms(uid) ON DELETE CASCADE,
            position INTEGER NOT NULL,
            element_uid TEXT NOT NULL REFERENCES workspace_elements(uid) ON DELETE CASCADE,
            PRIMARY KEY (alarm_uid, position)
        )""",
        """INSERT INTO alarms_targets(alarm_uid, position, element_uid)
           SELECT uid, 0, target_uid FROM alarms_alarms_v1 WHERE target_uid IS NOT NULL""",
        "DROP TABLE alarms_alarms_v1",
        "CREATE INDEX alarms_alarms_status ON alarms_alarms(status)",
        "CREATE INDEX alarms_targets_element ON alarms_targets(element_uid)",
    ):
        connection.exec_driver_sql(statement)


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1), Migration(2, _v2))

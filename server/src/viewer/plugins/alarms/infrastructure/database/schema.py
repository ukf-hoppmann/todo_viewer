"""Migrationen von `alarms`."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from viewer.core.domain.plugin import Migration
from viewer.plugins.alarms.domain.model import STATUSES


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
    for code in STATUSES:
        connection.execute(text("INSERT INTO alarms_statuses(code) VALUES (:c)"), {"c": code})


MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1),)

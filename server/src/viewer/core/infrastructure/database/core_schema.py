"""Migrationen des Core: `core_ui_state` und `core_sync_state` (genutzt von `STORY-065`)."""

from __future__ import annotations

from typing import Any

from viewer.core.domain.plugin import Migration


def _v1(connection: Any) -> None:
    connection.exec_driver_sql(
        "CREATE TABLE core_ui_state ( owner TEXT PRIMARY KEY, document TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    connection.exec_driver_sql(
        "CREATE TABLE core_sync_state ("
        " project_uid TEXT NOT NULL,"
        " uid TEXT NOT NULL,"
        " hash TEXT NOT NULL,"
        " synced_at TEXT NOT NULL,"
        " PRIMARY KEY (project_uid, uid))"
    )


CORE_MIGRATIONS: tuple[Migration, ...] = (Migration(1, _v1),)

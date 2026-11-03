from __future__ import annotations

from sqlalchemy import text

from viewer.core.application.ports import Clock
from viewer.core.infrastructure.database.engine import SqliteDatabase


class SqlSettingsStore:
    """Einstellungen des Core als Schlüssel-Wert-Paare in `core_settings`."""

    def __init__(self, database: SqliteDatabase, clock: Clock) -> None:
        self._database = database
        self._clock = clock

    def get(self, key: str) -> str | None:
        with self._database.transaction() as tx:
            row = tx.connection.execute(text("SELECT value FROM core_settings WHERE key = :key"), {"key": key}).first()
        return None if row is None else str(row[0])

    def put(self, key: str, value: str) -> None:
        with self._database.transaction() as tx:
            tx.connection.execute(
                text(
                    "INSERT INTO core_settings(key, value, updated_at) VALUES (:key, :value, :at) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at"
                ),
                {"key": key, "value": value, "at": self._clock.now().isoformat()},
            )

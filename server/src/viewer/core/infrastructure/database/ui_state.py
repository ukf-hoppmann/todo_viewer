from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from viewer.core.application.ports import Clock
from viewer.core.infrastructure.database.engine import SqliteDatabase


class SqlUiStateStore:
    """Ein JSON-Dokument je Besitzer in `core_ui_state`."""

    def __init__(self, database: SqliteDatabase, clock: Clock) -> None:
        self._database = database
        self._clock = clock

    def get(self, owner: str) -> dict[str, Any] | None:
        with self._database.transaction() as tx:
            row = tx.connection.execute(
                text("SELECT document FROM core_ui_state WHERE owner = :owner"), {"owner": owner}
            ).first()
        if row is None:
            return None
        document: dict[str, Any] = json.loads(row[0])
        return document

    def put(self, owner: str, document: dict[str, Any]) -> None:
        with self._database.transaction() as tx:
            tx.connection.execute(
                text(
                    "INSERT INTO core_ui_state(owner, document, updated_at) VALUES (:owner, :document, :at) "
                    "ON CONFLICT(owner) DO UPDATE SET document = excluded.document, updated_at = excluded.updated_at"
                ),
                {
                    "owner": owner,
                    "document": json.dumps(document, ensure_ascii=False, separators=(",", ":")),
                    "at": self._clock.now().isoformat(),
                },
            )

"""UI state (filters, view, language) as one JSON object in the central database."""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import sqlalchemy as sa

from .engine import Database
from .schema import ui_state

ROW = 1


class DatabaseUiStateStore:
    """`before_access` runs before every access, e.g. to take over a leftover ui_state.json."""

    def __init__(self, db: Database, before_access: Callable[[], None] = lambda: None):
        self._db = db
        self._before_access = before_access

    def load(self) -> dict[str, Any]:
        self._before_access()
        with self._db.begin() as conn:
            data = conn.execute(sa.select(ui_state.c.data).where(ui_state.c.id == ROW)).scalar()
        state = json.loads(data) if data else {}
        return state if isinstance(state, dict) else {}

    def save(self, state: dict[str, Any]) -> None:
        self._before_access()
        with self._db.begin() as conn:
            save_ui_state(conn, state)


def save_ui_state(conn: sa.Connection, state: dict[str, Any]) -> None:
    data = json.dumps(state, ensure_ascii=False)
    if conn.execute(sa.update(ui_state).where(ui_state.c.id == ROW).values(data=data)).rowcount == 0:
        conn.execute(sa.insert(ui_state).values(id=ROW, data=data))

"""Logeinträge des Browsers: prüfen, begrenzen und an das Log des Servers weitergeben."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from viewer.core.application.ports import ClientLogWriter, Clock
from viewer.core.domain.errors import InvalidInput

LEVELS = ("debug", "info", "warn", "error")
MAX_TEXT_CHARS = 2000
MAX_PART_BYTES = 16 * 1024
RATE_LIMIT = 100
RATE_WINDOW = timedelta(seconds=60)


@dataclass(frozen=True)
class ClientLogIn:
    """Ein Eintrag des Loggings des Browsers (`client/src/core/logging`)."""

    level: str
    origin: str = "core"
    id: str | None = None
    time: str | None = None
    session_id: str | None = None
    route: str | None = None
    element: str | None = None
    action: str | None = None
    message: str | None = None
    user_message: str | None = None
    error: dict[str, Any] | None = None
    data: Any = None


@dataclass(frozen=True)
class ClientLogOut:
    """`accepted` ist `False`, wenn der Eintrag wegen der Mengenbegrenzung verworfen wurde."""

    accepted: bool


class ClientLogService:
    def __init__(self, writer: ClientLogWriter, clock: Clock) -> None:
        self._writer = writer
        self._clock = clock
        self._recent: deque[datetime] = deque()

    def write(self, entry: ClientLogIn) -> ClientLogOut:
        if entry.level not in LEVELS:
            raise InvalidInput(f"Ungültige Stufe '{entry.level}'", details={"level": entry.level})
        if not self._within_rate():
            return ClientLogOut(False)
        fields: dict[str, Any] = {
            "client_origin": entry.origin,
            "client_id": entry.id,
            "client_time": entry.time,
            "session_id": entry.session_id,
            "route": entry.route,
            "element": entry.element,
            "action": entry.action,
            "user_message": _text(entry.user_message),
            "error": _limited(entry.error),
            "data": _limited(entry.data),
        }
        self._writer.write(
            entry.level, _text(entry.message) or "client-log", {k: v for k, v in fields.items() if v is not None}
        )
        return ClientLogOut(True)

    def _within_rate(self) -> bool:
        now = self._clock.now()
        while self._recent and now - self._recent[0] >= RATE_WINDOW:
            self._recent.popleft()
        if len(self._recent) >= RATE_LIMIT:
            return False
        self._recent.append(now)
        return True


def _text(value: str | None) -> str | None:
    if value is None or len(value) <= MAX_TEXT_CHARS:
        return value
    return value[:MAX_TEXT_CHARS] + "…"


def _limited(value: Any) -> Any:
    """Zu große Teile werden durch einen Hinweis mit der Größe ersetzt."""
    if value is None:
        return None
    size = len(json.dumps(value, ensure_ascii=False, default=str).encode())
    return value if size <= MAX_PART_BYTES else {"truncated": True, "size": size}

"""Die Zeitzone des Rechners, auf dem der Server läuft (Architektur §4): aus `TZ`, sonst UTC."""

from __future__ import annotations

from datetime import UTC, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import structlog

log = structlog.get_logger("viewer.timezone")


def resolve_zone(name: str | None) -> tzinfo:
    """`name` ist ein IANA-Name (`Europe/Berlin`). Fehlt er oder ist er unbekannt, gilt UTC, und das Log meldet es."""
    cleaned = (name or "").strip()
    if not cleaned:
        log.warning("timezone_missing", used="UTC", hint="TZ setzen, z. B. Europe/Berlin")
        return UTC
    try:
        return ZoneInfo(cleaned)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        log.warning("timezone_unknown", name=cleaned, used="UTC")
        return UTC

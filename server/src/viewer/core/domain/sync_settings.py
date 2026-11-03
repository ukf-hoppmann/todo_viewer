"""Einstellung des Auto-Sync-Takts: erlaubte Werte als reine Funktion."""

from __future__ import annotations

import math

from viewer.core.domain.errors import DomainError, InvalidInput

#: Obergrenze in Sekunden (ein Tag); `0` schaltet den Takt ab.
MAX_AUTO_SYNC_INTERVAL_SECONDS = 86400.0
#: Kleinster Takt in Sekunden, wenn er nicht abgeschaltet ist.
MIN_AUTO_SYNC_INTERVAL_SECONDS = 1.0


class SettingLocked(DomainError):
    """Der Wert ist durch die Umgebung gesetzt und lässt sich nicht ändern."""

    code = "setting_locked"


def check_auto_sync_interval(seconds: float) -> float:
    """Gibt den Takt als Zahl zurück: `0` (aus) oder mindestens eine Sekunde, höchstens ein Tag."""
    value = float(seconds)
    valid = value == 0 or (
        math.isfinite(value) and MIN_AUTO_SYNC_INTERVAL_SECONDS <= value <= MAX_AUTO_SYNC_INTERVAL_SECONDS
    )
    if not valid:
        raise InvalidInput(
            f"Der Takt muss 0 (aus) oder zwischen {MIN_AUTO_SYNC_INTERVAL_SECONDS:g} und "
            f"{MAX_AUTO_SYNC_INTERVAL_SECONDS:g} Sekunden liegen",
            details={"min": MIN_AUTO_SYNC_INTERVAL_SECONDS, "max": MAX_AUTO_SYNC_INTERVAL_SECONDS},
        )
    return value

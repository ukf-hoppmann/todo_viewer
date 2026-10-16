from __future__ import annotations

import re
import sqlite3
from datetime import timedelta
from pathlib import Path

from viewer.core.application.ports import Clock
from viewer.core.infrastructure.database.engine import SqliteDatabase

_REASON = re.compile(r"^[a-z][a-z0-9-]*$")


class SqliteBackupMaker:
    """Sichert die Datenbank mit der SQLite-Backup-API nach `<ordner>/viewer-<UTC-Zeit>-<grund>.db`.

    Je Grund bleiben die letzten `keep` Sicherungen.
    """

    def __init__(self, database: SqliteDatabase, directory: Path | str, clock: Clock, keep: int = 10) -> None:
        self._database = database
        self._directory = Path(directory)
        self._clock = clock
        self._keep = keep

    def create(self, reason: str) -> Path:
        if not _REASON.match(reason):
            raise ValueError(f"Ungültiger Grund für ein Backup: {reason!r}")
        self._directory.mkdir(parents=True, exist_ok=True)
        moment = self._clock.now()
        target = self._target(moment, reason)
        while target.exists():  # zwei Sicherungen im selben Zeitpunkt
            moment += timedelta(microseconds=1)
            target = self._target(moment, reason)
        source = sqlite3.connect(self._database.path)
        try:
            destination = sqlite3.connect(target)
            try:
                source.backup(destination)
            finally:
                destination.close()
        finally:
            source.close()
        self._rotate(reason)
        return target

    def _target(self, moment, reason: str) -> Path:  # type: ignore[no-untyped-def]
        return self._directory / f"viewer-{moment.strftime('%Y%m%dT%H%M%S%f')}Z-{reason}.db"

    def _rotate(self, reason: str) -> None:
        backups = sorted(self._directory.glob(f"viewer-*Z-{reason}.db"))
        for old in backups[: -self._keep] if self._keep > 0 else backups:
            old.unlink()

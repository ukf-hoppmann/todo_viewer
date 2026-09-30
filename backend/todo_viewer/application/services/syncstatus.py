from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from todo_viewer.domain.errors import SyncSourceInvalidError
from todo_viewer.domain.source import Source, SyncBaseline
from todo_viewer.domain.sync import SyncDirection, SyncState, classify

from ..ports import SourceRepository
from .sync import SideFingerprints, SyncResult, SyncService


@dataclass(frozen=True)
class SyncStatus:
    state: SyncState
    last_sync_at: str | None  # when the project was last synced through `run`; None if it never was


class SyncStatusService:
    """Tells which side of a mirrored project changed since its last sync, and remembers when that sync was.

    Reading the status changes nothing and syncs nothing; only `run` records the state after a sync.
    """

    def __init__(self, sync: SyncService, sources: SourceRepository,
                 now: Callable[[], datetime] = lambda: datetime.now().astimezone()):
        self._sync = sync
        self._sources = sources
        self._now = now

    def status(self, source: Source) -> SyncStatus:
        """`source` must be as stored (with its baseline). A side that cannot be read gives UNREADABLE."""
        baseline = source.baseline
        try:
            sides = self._sync.fingerprints(source)
        except SyncSourceInvalidError:
            return SyncStatus(SyncState.UNREADABLE, baseline.at if baseline else None)
        if sides is None:
            return SyncStatus(SyncState.NONE, None)
        return SyncStatus(classify(sides.primary, sides.mirror, baseline), baseline.at or None if baseline else None)

    def run(self, source: Source, direction: SyncDirection, token: str | None, delete_missing: bool,
            language: str) -> SyncResult:
        """`SyncService.run`, then the state of both sides is stored as the state of the last sync."""
        result = self._sync.run(source, direction, token, delete_missing, language)
        if result.fingerprints is not None:
            self._record(source, result.fingerprints)
        return result

    def _record(self, source: Source, sides: SideFingerprints) -> None:
        baseline = SyncBaseline(at=self._now().isoformat(timespec="seconds"), primary=sides.primary,
                                mirror=sides.mirror)
        with self._sources.edit() as sources:
            for index, stored in enumerate(sources):
                if stored.id == source.id:
                    sources[index] = dataclasses.replace(stored, baseline=baseline)

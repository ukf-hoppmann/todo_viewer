from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import structlog

from todo_viewer.domain.errors import DomainError, SyncSourceInvalidError, SyncStaleError
from todo_viewer.domain.source import Source

from ..ports import SourceRepository
from .sync import SyncService
from .syncstatus import SyncStatusService

log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class AutoSyncInfo:
    """What the automatic sync did for one project (kept in memory; a restart forgets it)."""

    last_run_at: str | None = None  # when it last carried something over
    paused: str | None = None  # why the last check could not run (a `details.reason` or an error code); None: fine


class AutoSyncService:
    """Syncs the projects whose owner switched the automatic sync on, by itself.

    One check (`tick`) looks at every such project and carries over what only one side changed. It uses the same
    use case and the same lock per project as a manual sync, so it never writes at the same time as one, and it
    carries no decisions: conflicts stay open, nothing is deleted. A change is taken over only when the state of
    both sides was the same at two checks in a row, so a pull that still writes its files is waited out.

    The timer runs only while at least one project has the switch on (Architecture §3, exception for this sync);
    `interval` 0 means no timer at all (tests and callers call `tick` themselves).
    """

    def __init__(self, sync: SyncService, status: SyncStatusService, sources: SourceRepository, interval: float,
                 clock: Callable[[], datetime] = lambda: datetime.now().astimezone()):
        self._sync = sync
        self._status = status
        self._sources = sources
        self._interval = interval
        self._clock = clock
        self._seen: dict[str, str] = {}  # project id -> token of the previous check
        self._info: dict[str, AutoSyncInfo] = {}
        self._guard = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def info(self, source_id: str) -> AutoSyncInfo:
        with self._guard:
            return self._info.get(source_id, AutoSyncInfo())

    def active(self) -> bool:
        """Whether any project has the automatic sync on."""
        return any(s.auto_sync_active for s in self._sources.all())

    # --- one check ---

    def tick(self) -> None:
        """One check of every project with the switch on. A failure is logged and never raised."""
        try:
            sources = [s for s in self._sources.all() if s.auto_sync_active]
        except Exception:
            log.exception("auto_sync_failed")
            return
        with self._guard:
            self._seen = {k: v for k, v in self._seen.items() if k in {s.id for s in sources}}
        for source in sources:
            try:
                self._check(source)
            except Exception:
                log.exception("auto_sync_failed", project=source.project)

    def _check(self, source: Source) -> None:
        try:
            preview = self._sync.preview(source, auto=True)
        except SyncSourceInvalidError as error:
            self._pause(source, str(error.details.get("reason", error.code)), error.message)
            return
        except DomainError as error:
            self._pause(source, error.code, error.message)
            return
        self._update(source, paused=None)
        carries = preview.created or preview.changed or preview.created_documents or preview.changed_documents
        with self._guard:
            steady = self._seen.get(source.id) == preview.token
            self._seen[source.id] = preview.token
        if not carries or not steady:
            return
        try:
            result = self._status.run(source, preview.token, (), None, "en", auto=True)
        except SyncStaleError:
            return  # something moved since the check: the next one decides again
        except DomainError as error:
            self._pause(source, error.code, error.message)
            return
        with self._guard:
            self._seen.pop(source.id, None)
        self._update(source, last_run_at=self._clock().isoformat(timespec="seconds"))
        log.info("auto_sync_run", project=source.project, resolved=len(result.resolved),
                 conflicts=len(result.deferred))

    def _pause(self, source: Source, reason: str, message: str) -> None:
        self._update(source, paused=reason)
        with self._guard:
            self._seen.pop(source.id, None)
        log.warning("auto_sync_paused", project=source.project, reason=reason, message=message)

    def _update(self, source: Source, **changes: str | None) -> None:
        with self._guard:
            current = self._info.get(source.id, AutoSyncInfo())
            self._info[source.id] = AutoSyncInfo(last_run_at=changes.get("last_run_at", current.last_run_at),
                                                 paused=changes.get("paused", current.paused))

    # --- the timer ---

    @property
    def running(self) -> bool:
        with self._guard:
            return self._thread is not None

    def ensure_running(self) -> None:
        """Starts the timer if it is wanted: there is an interval and at least one project has the switch on."""
        if self._interval <= 0:
            return
        with self._guard:
            if self._thread is not None:
                return
        if not self.active():
            return
        with self._guard:
            if self._thread is not None:
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="auto-sync", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._guard:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5)

    def _loop(self) -> None:
        try:
            while not self._stop.is_set():
                self.tick()
                if self._stop.wait(self._interval):
                    return
                try:
                    wanted = self.active()
                except Exception:
                    wanted = True
                if not wanted:
                    return
        finally:
            with self._guard:
                self._thread = None


__all__ = ["AutoSyncInfo", "AutoSyncService"]

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from datetime import datetime

import structlog

from viewer.core.application.ports import Clock

log = structlog.get_logger(__name__)


class AsyncioScheduler:
    """Ein Termin je Besitzer, kein Polling: pro Termin ein `call_later` auf der Ereignisschleife.

    Vor `start(loop)` werden Termine nur gemerkt. Läuft nur, solange der Server läuft.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._pending: dict[str, tuple[datetime, Callable[[], None]]] = {}
        self._handles: dict[str, asyncio.TimerHandle] = {}

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        with self._lock:
            self._loop = loop
            pending = dict(self._pending)
        for owner, (at, callback) in pending.items():
            self._arm(owner, at, callback)

    def stop(self) -> None:
        with self._lock:
            loop, self._loop = self._loop, None
            handles, self._handles = self._handles, {}
        for handle in handles.values():
            if loop is not None and not loop.is_closed():
                loop.call_soon_threadsafe(handle.cancel)

    def schedule(self, owner: str, at: datetime | None, callback: Callable[[], None]) -> None:
        with self._lock:
            old = self._handles.pop(owner, None)
            loop = self._loop
            if at is None:
                self._pending.pop(owner, None)
            else:
                self._pending[owner] = (at, callback)
        if old is not None and loop is not None:
            loop.call_soon_threadsafe(old.cancel)
        if at is not None and loop is not None:
            self._arm(owner, at, callback)

    def pending_at(self, owner: str) -> datetime | None:
        with self._lock:
            entry = self._pending.get(owner)
        return entry[0] if entry else None

    def _arm(self, owner: str, at: datetime, callback: Callable[[], None]) -> None:
        delay = max(0.0, (at - self._clock.now()).total_seconds())

        def fire() -> None:
            with self._lock:
                current = self._pending.get(owner)
                if current is None or current[1] is not callback or current[0] != at:
                    return
                del self._pending[owner]
                self._handles.pop(owner, None)
            try:
                callback()
            except Exception:
                log.exception("scheduler_callback_failed", owner=owner)

        loop = self._loop
        assert loop is not None
        if _in_loop(loop):
            self._register(owner, loop.call_later(delay, fire))
        else:
            loop.call_soon_threadsafe(lambda: self._register(owner, loop.call_later(delay, fire)))

    def _register(self, owner: str, handle: asyncio.TimerHandle) -> None:
        with self._lock:
            previous = self._handles.get(owner)
            self._handles[owner] = handle
        if previous is not None:
            previous.cancel()


def _in_loop(loop: asyncio.AbstractEventLoop) -> bool:
    try:
        return asyncio.get_running_loop() is loop
    except RuntimeError:
        return False

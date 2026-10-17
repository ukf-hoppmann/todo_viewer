"""Server-Sent Events: leitet öffentliche Ereignisse an verbundene Clients weiter."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import AsyncIterator

import structlog

from viewer.core.application.ports import EventBus
from viewer.core.domain.events import Event

log = structlog.get_logger(__name__)

_CLOSE = object()


def format_event(event: Event) -> bytes:
    data = json.dumps(event.payload, ensure_ascii=False, separators=(",", ":"), default=str)
    return f"event: {event.topic}\ndata: {data}\n\n".encode()


class SseHub:
    """Hängt sich an den EventBus; je Client eine Warteschlange. Keine Zustellgarantie."""

    def __init__(self, bus: EventBus, keepalive_seconds: float = 15.0) -> None:
        self._keepalive = keepalive_seconds
        self._lock = threading.Lock()
        self._clients: set[tuple[asyncio.AbstractEventLoop, asyncio.Queue[object]]] = set()
        self._closed = False
        self._unsubscribe = bus.subscribe("*", self._on_event)

    @property
    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

    def close(self) -> None:
        """Beendet alle offenen Verbindungen (beim Herunterfahren)."""
        with self._lock:
            self._closed = True
            clients = list(self._clients)
        self._unsubscribe()
        for loop, queue in clients:
            _put(loop, queue, _CLOSE)

    async def stream(self) -> AsyncIterator[bytes]:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[object] = asyncio.Queue()
        entry = (loop, queue)
        with self._lock:
            if self._closed:
                return
            self._clients.add(entry)
        try:
            yield b"retry: 3000\n: connected\n\n"
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), self._keepalive)
                except TimeoutError:
                    yield b": keep-alive\n\n"
                    continue
                if item is _CLOSE:
                    return
                assert isinstance(item, Event)
                yield format_event(item)
        finally:
            with self._lock:
                self._clients.discard(entry)

    def _on_event(self, event: Event) -> None:
        if not event.public:
            return
        with self._lock:
            clients = list(self._clients)
        for loop, queue in clients:
            _put(loop, queue, event)


def _put(loop: asyncio.AbstractEventLoop, queue: asyncio.Queue[object], item: object) -> None:
    try:
        loop.call_soon_threadsafe(queue.put_nowait, item)
    except RuntimeError:  # Schleife schon geschlossen
        log.debug("sse_client_gone")

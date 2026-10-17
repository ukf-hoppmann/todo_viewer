from __future__ import annotations

import threading
from collections.abc import Callable

import structlog

from viewer.core.application.ports import EventHandler
from viewer.core.domain.events import Event

log = structlog.get_logger(__name__)


class InProcessEventBus:
    """Synchroner EventBus; ein fehlerhafter Abonnent stoppt die anderen nicht."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: list[tuple[str, EventHandler]] = []

    def subscribe(self, topic: str, handler: EventHandler) -> Callable[[], None]:
        entry = (topic, handler)
        with self._lock:
            self._subscribers.append(entry)

        def unsubscribe() -> None:
            with self._lock:
                if entry in self._subscribers:
                    self._subscribers.remove(entry)

        return unsubscribe

    def publish(self, event: Event) -> None:
        with self._lock:
            targets = [h for t, h in self._subscribers if _matches(t, event.topic)]
        for handler in targets:
            try:
                handler(event)
            except Exception:
                log.exception("event_handler_failed", topic=event.topic)


def _matches(pattern: str, topic: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith(".*"):
        return topic.startswith(pattern[:-1])
    return pattern == topic

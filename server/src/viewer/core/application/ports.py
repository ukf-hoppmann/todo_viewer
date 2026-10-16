"""Ports des Core: was die Anwendungsschicht von außen braucht."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol

from viewer.core.domain.events import Event

EventHandler = Callable[[Event], None]


class Clock(Protocol):
    def now(self) -> datetime:
        """Aktueller Zeitpunkt, timezone-aware in UTC."""
        ...


class EventBus(Protocol):
    def publish(self, event: Event) -> None:
        """Ruft alle passenden Abonnenten synchron im Prozess auf."""
        ...

    def subscribe(self, topic: str, handler: EventHandler) -> Callable[[], None]:
        """`topic` exakt, `*` = alle, `a.*` = alle Topics mit Präfix `a.`. Gibt die Abmeldefunktion zurück."""
        ...


class Scheduler(Protocol):
    def schedule(self, owner: str, at: datetime | None, callback: Callable[[], None]) -> None:
        """Genau ein Termin je Besitzer: ersetzt den vorigen; `None` löscht ihn."""
        ...

"""Ports des Core: was die Anwendungsschicht von außen braucht."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

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


class Transaction(Protocol):
    """Eine offene Datenbank-Transaktion. Für `application` opak; die Adapter in `infrastructure` kennen die Klasse."""


class Database(Protocol):
    def transaction(self) -> AbstractContextManager[Transaction]:
        """Öffnet eine Transaktion: Commit beim normalen Verlassen, Rollback bei einer Ausnahme."""
        ...


class BackupMaker(Protocol):
    def create(self, reason: str) -> Path:
        """Sichert die Datenbank; `reason` ist ein Kleinbuchstaben-Schlüssel wie `migration` oder `sync`."""
        ...


class UiStateStore(Protocol):
    def get(self, owner: str) -> dict[str, Any] | None: ...

    def put(self, owner: str, document: dict[str, Any]) -> None: ...

"""Ports des Core: was die Anwendungsschicht von außen braucht."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from viewer.core.domain.events import Event
from viewer.core.domain.files import Change, FileSet, FolderListing, FolderState

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


class FileStore(Protocol):
    """Liest und schreibt einen Ordner als Menge von Textdateien; kennt keine Formate."""

    def read(self, folder: Path, patterns: Sequence[str]) -> FileSet:
        """Liest alle Dateien, die auf eines der Muster (relativ zum Ordner, `**` erlaubt) passen.

        Meldet mit `MirrorBlocked`, statt zu lesen, wenn der Ordner fehlt, eine Datei unlesbar ist, Merge-Marker
        enthält oder eine Git-Operation läuft (`.git/*.lock`).
        """
        ...

    def write(
        self,
        folder: Path,
        changes: Sequence[Change],
        expected: Mapping[str, str | None],
        *,
        create_folder: bool = False,
    ) -> dict[str, str | None]:
        """Wendet Änderungen an, nachdem alle `expected`-Versionen geprüft sind (`None` = Datei darf nicht existieren).

        Jeder berührte Pfad muss in `expected` stehen. Bei einer Abweichung `MirrorConflict`, ohne etwas zu ändern.
        Gibt die neuen Versionen der berührten Pfade zurück (`None` = gelöscht).
        """
        ...

    def inspect(self, folder: Path, patterns: Sequence[str] = ("**/*.md",)) -> FolderState:
        """Zustand des Ordners, ohne Daten zu ändern oder zu liefern."""
        ...

    def list_folders(self, start: Path) -> FolderListing:
        """Unterordner ohne versteckte, für den Ordner-Browser. Ein Pfad, der kein Ordner ist, fällt auf den nächsten
        vorhandenen Elternordner zurück."""
        ...

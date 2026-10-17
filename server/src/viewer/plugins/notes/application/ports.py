"""Ports des Plugins `notes`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from viewer.core.application.ports import Transaction
from viewer.plugins.notes.domain.model import Note, NotesSettings, Topic


class NoteRepository(Protocol):
    def insert(self, tx: Transaction, note: Note) -> None: ...

    def update(self, tx: Transaction, note: Note) -> None:
        """Schreibt alle änderbaren Felder; die Revision hat das Register."""
        ...

    def get(self, tx: Transaction, uid: str) -> Note | None: ...

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Note]:
        """Notes der Projekte (alle, wenn `None`) nach Projekt und Label."""
        ...

    def in_topic(self, tx: Transaction, topic_uid: str) -> list[Note]:
        """Alle Notes des Topics, gelöschte eingeschlossen."""
        ...

    def delete(self, tx: Transaction, uid: str) -> None:
        """Entfernt die Zeilen der Note und ihre Dokumente."""
        ...


class TopicRepository(Protocol):
    def insert(self, tx: Transaction, topic: Topic) -> None: ...

    def update(self, tx: Transaction, topic: Topic) -> None: ...

    def get(self, tx: Transaction, uid: str) -> Topic | None: ...

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Topic]: ...

    def children(self, tx: Transaction, uid: str) -> list[Topic]:
        """Direkte Unter-Topics, gelöschte eingeschlossen."""
        ...

    def archive_topic_of(self, tx: Transaction, project_uid: str) -> Topic | None:
        """Das neutrale Topic „Archiviert“ des Projekts (auch im Papierkorb)."""
        ...

    def delete(self, tx: Transaction, uid: str) -> None: ...


@dataclass(frozen=True)
class Document:
    """Ein Dokument einer Note; `revision` ist seine Version."""

    note_uid: str
    name: str
    kind: str
    content: str
    revision: int
    updated_at: datetime


class DocumentRepository(Protocol):
    def list_for(self, tx: Transaction, note_uid: str) -> list[Document]: ...

    def get(self, tx: Transaction, note_uid: str, name: str) -> Document | None: ...

    def insert(self, tx: Transaction, document: Document) -> None: ...

    def update(self, tx: Transaction, note_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        """Ersetzt den Inhalt, wenn die Revision `expected` ist (sonst `version_conflict`); gibt die neue zurück."""
        ...


class SettingsRepository(Protocol):
    def load(self, tx: Transaction) -> NotesSettings: ...

    def save(self, tx: Transaction, settings: NotesSettings) -> None: ...

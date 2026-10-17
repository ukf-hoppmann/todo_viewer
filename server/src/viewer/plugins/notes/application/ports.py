"""Ports des Plugins `notes`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from viewer.core.application.ports import Transaction
from viewer.plugins.notes.domain.due import Trigger
from viewer.plugins.notes.domain.model import Note, NotesSettings, Topic
from viewer.plugins.notes.domain.notices import Notice


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


class TriggerRepository(Protocol):
    def for_notes(self, tx: Transaction, note_uids: Sequence[str]) -> dict[str, list[Trigger]]:
        """Die Auslöser der Notes nach Note (Notes ohne Auslöser fehlen)."""
        ...

    def get(self, tx: Transaction, uid: str) -> Trigger | None: ...

    def insert(self, tx: Transaction, trigger: Trigger) -> None: ...

    def update(self, tx: Transaction, trigger: Trigger) -> None:
        """Schreibt `fired_at`, `already_met` und `link_uid`."""
        ...

    def delete(self, tx: Transaction, uid: str) -> None: ...

    def waiting_on(self, tx: Transaction, target_uid: str, status: str) -> list[Trigger]:
        """Die noch nicht gefeuerten Ereignis-Auslöser auf das Item, die auf `status` warten."""
        ...


class NoticeRepository(Protocol):
    def insert(self, tx: Transaction, notice: Notice) -> None: ...

    def get(self, tx: Transaction, uid: str) -> Notice | None: ...

    def decide(self, tx: Transaction, uid: str, decision: str, at: datetime) -> None: ...

    def open_for(self, tx: Transaction, subject_uids: Sequence[str]) -> dict[str, list[Notice]]:
        """Die offenen Hinweise je Empfänger, älteste zuerst (Empfänger ohne Hinweis fehlen)."""
        ...

    def find_open(self, tx: Transaction, subject_uid: str, source_uid: str, kind: str) -> Notice | None: ...

    def delete_for(self, tx: Transaction, uid: str) -> None:
        """Entfernt die Hinweise, die `uid` als Empfänger oder als anderes Ende haben."""
        ...


@dataclass(frozen=True)
class ItemInfo:
    """Was `notes` über ein Item des Backlogs wissen muss (der Port kennt `backlog` nicht)."""

    uid: str
    project_uid: str
    label: str
    title: str
    type: str
    status: str
    summary: str | None
    revision: int
    deleted: bool
    #: Die `uid`s der Kinder und der Items, die von ihm abhängen (nicht gelöschte).
    children: tuple[str, ...]
    dependents: tuple[str, ...]
    #: Namen der Notiz- und Spec-Dokumente.
    documents: tuple[str, ...]


@dataclass(frozen=True)
class GatewayDocument:
    content: str
    revision: int


class BacklogGateway(Protocol):
    """Der Zugang von `notes` zum Backlog: Items lesen, anlegen und ablehnen, Dokumente lesen und schreiben."""

    def get_item(self, uid: str) -> ItemInfo | None: ...

    def create_item(self, project_uid: str, type_: str, fields: dict[str, object]) -> str:
        """Legt das Item an (mit allen Regeln des Backlogs) und gibt seine `uid` zurück."""
        ...

    def reject_item(self, uid: str, version: int, resolution: str) -> None:
        """Setzt das Item auf `Rejected` mit der Entscheidung `resolution`."""
        ...

    def read_document(self, item_uid: str, name: str) -> GatewayDocument | None: ...

    def write_document(self, item_uid: str, name: str, content: str, version: int | None, summary: str | None) -> None:
        """Ersetzt das Dokument in `version` oder legt es an (`version` leer)."""
        ...

"""Ports des Plugins `backlog`."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from viewer.core.application.ports import Transaction
from viewer.plugins.backlog.domain.model import Item
from viewer.plugins.backlog.domain.notes import NotesParts


class ItemRepository(Protocol):
    def insert(self, tx: Transaction, item: Item) -> None:
        """Legt die Zeilen von Item, Bereich (falls neu) und Abhängigkeiten an; das Register-Element gibt es schon."""
        ...

    def get(self, tx: Transaction, uid: str) -> Item | None: ...

    def list_in(
        self, tx: Transaction, project_uids: Sequence[str] | None, *, include_deleted: bool = False
    ) -> list[Item]:
        """Items der Projekte (alle, wenn `None`) in der Reihenfolge Projekt, Label."""
        ...

    def children(self, tx: Transaction, uid: str) -> list[Item]:
        """Direkte Kinder, gelöschte eingeschlossen, nach Position und Label."""
        ...

    def delete(self, tx: Transaction, uid: str) -> None:
        """Entfernt die Zeilen des Items und seine Abhängigkeiten (in beide Richtungen)."""
        ...

    def update(self, tx: Transaction, item: Item) -> None:
        """Schreibt alle änderbaren Felder (Typ, Bereich, Parent, Abhängigkeiten …); die Revision hat das Register."""
        ...

    def area_names(self, tx: Transaction, project_uid: str) -> list[str]: ...

    def siblings(self, tx: Transaction, project_uid: str, parent_uid: str | None) -> list[Item]:
        """Nicht gelöschte Items unter einem Parent (oder die Wurzeln), nach Position und Label."""
        ...

    def set_positions(self, tx: Transaction, uids: Sequence[str]) -> None: ...


@dataclass(frozen=True)
class Document:
    """Ein Dokument eines Items; `revision` ist seine Version."""

    item_uid: str
    name: str
    kind: str
    content: str
    revision: int
    updated_at: datetime


class DocumentRepository(Protocol):
    def list_for(self, tx: Transaction, item_uid: str) -> list[Document]:
        """Die Dokumente des Items nach Art (Notizen zuerst) und Name, ohne Inhalt zu laden ist nicht nötig."""
        ...

    def get(self, tx: Transaction, item_uid: str, name: str) -> Document | None: ...

    def insert(self, tx: Transaction, document: Document) -> None: ...

    def update(self, tx: Transaction, item_uid: str, name: str, content: str, expected: int, at: datetime) -> int:
        """Ersetzt den Inhalt, wenn die Revision `expected` ist (sonst `version_conflict`); gibt die neue zurück."""
        ...

    def rename(self, tx: Transaction, item_uid: str, old: str, new: str) -> None: ...

    def delete(self, tx: Transaction, item_uid: str, name: str) -> None: ...


@dataclass(frozen=True)
class Notes:
    """Die Notes eines Items in Teilen; `revision` ist die Version der zusammengesetzten Datei, `state_revision` die
    des Kopfs mit Stempel."""

    item_uid: str
    name: str
    parts: NotesParts
    state_revision: int
    revision: int
    updated_at: datetime


class NotesRepository(Protocol):
    def get(self, tx: Transaction, item_uid: str) -> Notes | None: ...

    def names(self, tx: Transaction, item_uids: Sequence[str]) -> dict[str, str]:
        """Item-uid → Name der Notes, nur für Items mit Notes."""
        ...

    def insert(self, tx: Transaction, notes: Notes) -> None: ...

    def parts_for(self, tx: Transaction, item_uids: Sequence[str]) -> dict[str, NotesParts]:
        """Item-uid → Teile der Notes, nur für Items mit Notes (für Übersichten über viele Items)."""
        ...

    def save(
        self,
        tx: Transaction,
        item_uid: str,
        parts: NotesParts,
        *,
        expected: int,
        state_changed: bool,
        at: datetime,
        expected_state: int | None = None,
    ) -> int:
        """Ersetzt die Teile, wenn die Revision `expected` ist (und, falls angegeben, die des Kopfs
        `expected_state`; sonst `version_conflict`); gibt die neue Revision zurück. `state_changed` zählt auch die
        Version des Kopfs hoch."""
        ...

    def rename(self, tx: Transaction, item_uid: str, new: str) -> None: ...

    def delete(self, tx: Transaction, item_uid: str) -> None: ...


@dataclass(frozen=True)
class TrashedDocument:
    """Ein gelöschtes Dokument als Schnappschuss. `content` ist der ganze Text (eine Notiz mit Titelzeile und Kopf),
    `summary` die kurz davor gültige Kurzfassung des Items (nur bei Notizen)."""

    uid: str
    item_uid: str
    name: str
    kind: str
    content: str
    summary: str | None
    deleted_at: datetime


@dataclass(frozen=True)
class TrashedListing:
    """Ein Schnappschuss mit dem, was der Papierkorb zur Anzeige braucht."""

    document: TrashedDocument
    item_label: str
    project_uid: str


class TrashedDocumentRepository(Protocol):
    def insert(self, tx: Transaction, document: TrashedDocument) -> None: ...

    def get(self, tx: Transaction, uid: str) -> TrashedDocument | None: ...

    def list_deleted(self, tx: Transaction, project_uids: Sequence[str] | None, query: str) -> list[TrashedListing]:
        """Die gelöschten Dokumente, neueste zuerst; optional nach Projekten und Text in Label oder Name gefiltert."""
        ...

    def delete(self, tx: Transaction, uid: str) -> None: ...

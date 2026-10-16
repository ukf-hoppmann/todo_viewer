"""Projekte, Elemente und ihre Regeln (reine Datentypen und Funktionen)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from viewer.core.domain.errors import DomainError, InvalidInput

BUILTIN_PROJECT = "Allgemein"
SYNC_DIRECTIONS = ("both", "to_files", "to_database")
SyncDirection = Literal["both", "to_files", "to_database"]

_LABEL = re.compile(r"^([A-Z]+)-(\d+)$")


class ProjectNameTaken(DomainError):
    code = "project_name_taken"


class BuiltinProject(DomainError):
    code = "builtin_project"


class ProjectNotEmpty(DomainError):
    code = "project_not_empty"


class UnknownElementKind(DomainError):
    code = "unknown_element_kind"


class UnknownReference(DomainError):
    code = "unknown_reference"


@dataclass(frozen=True)
class Project:
    uid: str
    name: str
    mirror_folder: str | None
    mirror_enabled: bool
    auto_sync: bool
    sync_direction: SyncDirection
    position: int
    revision: int
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def builtin(self) -> bool:
        return self.name == BUILTIN_PROJECT


@dataclass(frozen=True)
class Element:
    """Ein Eintrag des Element-Registers: `uid` ist die Identität, `label` nur die Anzeige."""

    uid: str
    project_uid: str
    kind: str
    label: str
    revision: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


def format_label(prefix: str, number: int) -> str:
    """`STORY` und 12 → `STORY-012`."""
    return f"{prefix}-{number:03d}"


def parse_label(label: str) -> tuple[str, int] | None:
    match = _LABEL.match(label.strip())
    return (match.group(1), int(match.group(2))) if match else None


def validate_project_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or len(cleaned) > 100 or any(ord(char) < 32 for char in cleaned):
        raise InvalidInput("Der Projektname muss 1 bis 100 Zeichen ohne Steuerzeichen haben", details={"field": "name"})
    return cleaned


def validate_mirror(folder: str | None, enabled: bool) -> str | None:
    """Der Spiegel-Ordner ist ein absoluter Pfad; ein eingeschalteter Spiegel braucht einen."""
    cleaned = folder.strip() if folder else None
    if cleaned == "":
        cleaned = None
    if enabled and cleaned is None:
        raise InvalidInput("Ein eingeschalteter Spiegel braucht einen Ordner", details={"field": "mirror_folder"})
    if cleaned is not None and not (cleaned.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", cleaned)):
        raise InvalidInput("Der Spiegel-Ordner muss ein absoluter Pfad sein", details={"field": "mirror_folder"})
    return cleaned


def validate_sync_direction(direction: str) -> SyncDirection:
    if direction not in SYNC_DIRECTIONS:
        raise InvalidInput(f"Unbekannte Sync-Richtung '{direction}'", details={"field": "sync_direction"})
    return direction  # type: ignore[return-value]


def reorder(uids: Sequence[str], uid: str, position: int) -> list[str]:
    """Die Reihenfolge, nachdem `uid` an die Stelle `position` (ab 0, auf die Länge begrenzt) gerückt ist."""
    rest = [entry for entry in uids if entry != uid]
    index = max(0, min(position, len(rest)))
    return [*rest[:index], uid, *rest[index:]]

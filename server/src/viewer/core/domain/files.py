"""Datei-Datentypen und reine Funktionen für den Spiegel-Ordner (kein Dateisystem)."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Literal

from viewer.core.domain.errors import DomainError, InvalidInput


class MirrorConflict(DomainError):
    """Eine Datei hat sich seit dem Lesen geändert; nichts wurde geschrieben."""

    code = "mirror_conflict"


class MirrorBlocked(DomainError):
    """Der Ordner darf gerade nicht gelesen oder geschrieben werden (siehe `FolderState`)."""

    code = "mirror_blocked"


FolderStatus = Literal["ok", "missing", "unreadable", "merge_markers", "git_operation"]


@dataclass(frozen=True)
class FolderState:
    """Zustand eines Spiegel-Ordners; `files` nennt die betroffenen Dateien (relativ, POSIX)."""

    status: FolderStatus
    files: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.status == "ok"


@dataclass(frozen=True)
class FileEntry:
    """Eine gelesene Datei: Text mit LF, ihr ursprüngliches Zeilenende, Version (SHA-256 der Bytes)."""

    path: str
    text: str
    version: str
    newline: Literal["\n", "\r\n"] = "\n"


@dataclass(frozen=True)
class FileSet:
    files: Mapping[str, FileEntry] = field(default_factory=dict)

    def versions(self) -> dict[str, str]:
        return {path: entry.version for path, entry in self.files.items()}


@dataclass(frozen=True)
class WriteFile:
    path: str
    text: str


@dataclass(frozen=True)
class RenameFile:
    path: str
    new_path: str


@dataclass(frozen=True)
class DeleteFile:
    path: str


Change = WriteFile | RenameFile | DeleteFile

_MARKER_START = re.compile(r"^<{7}(\s|$)", re.MULTILINE)
_MARKER_END = re.compile(r"^>{7}(\s|$)", re.MULTILINE)
_TEMP_NAME = re.compile(r"^\..*\.tmp$")


def file_version(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_text(data: bytes) -> tuple[str, Literal["\n", "\r\n"]]:
    """Bytes → (Text mit LF, Zeilenende der Datei). Streng UTF-8; `UnicodeDecodeError` bei anderem Inhalt."""
    raw = data.decode("utf-8")
    crlf = raw.count("\r\n")
    lf = raw.count("\n") - crlf
    newline: Literal["\n", "\r\n"] = "\r\n" if crlf > lf else "\n"
    return raw.replace("\r\n", "\n"), newline


def encode_text(text: str, existing: bytes | None) -> bytes:
    """Text (LF) → Bytes im Zeilenende der bestehenden Datei; neue Dateien bekommen LF."""
    normalized = text.replace("\r\n", "\n")
    if existing is not None:
        try:
            _, newline = decode_text(existing)
        except UnicodeDecodeError:
            newline = "\n"
        if newline == "\r\n":
            normalized = normalized.replace("\n", "\r\n")
    return normalized.encode("utf-8")


def has_merge_markers(text: str) -> bool:
    """Ein Anfangs- und ein Endmarker eines Git-Merge-Konflikts am Zeilenanfang."""
    return bool(_MARKER_START.search(text) and _MARKER_END.search(text))


def is_temp_name(name: str) -> bool:
    """Temporäre Dateien des atomaren Schreibens (`.<name>.<zufall>.tmp`) gehören nicht zum Spiegel."""
    return bool(_TEMP_NAME.match(name))


def check_relative_path(path: str) -> str:
    """Pfad im Ordner: relativ, POSIX, ohne `..`, nicht in `.git`. Gibt den Pfad zurück."""
    pure = PurePosixPath(path)
    if (
        not path
        or pure.is_absolute()
        or "\\" in path
        or any(part in ("", ".", "..") for part in path.split("/"))
        or pure.parts[0] == ".git"
    ):
        raise InvalidInput(f"Ungültiger Pfad im Spiegel-Ordner: {path!r}", details={"path": path})
    return path

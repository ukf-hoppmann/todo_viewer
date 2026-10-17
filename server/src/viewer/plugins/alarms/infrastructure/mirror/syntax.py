"""Syntax von `alarms.md` (Format Version 2): Einträge, Felder, Kennung, Zeitpunkte. Reine Funktionen auf Zeilen."""

from __future__ import annotations

import re
from datetime import UTC, datetime

ALARMS_FILE = "alarms.md"
KIND_ALARM = "alarms.alarm"

HEADER = re.compile(r"^- `([A-Za-z0-9_.\-]+)`\s+\*\*(.+?)\*\*\s*$")
FIELD = re.compile(r"^ {2}- ([A-Za-z][A-Za-z ]*?):\s?(.*)$")
SECTION = re.compile(r"^## Alarms\s*$")
FORMAT_VERSION = re.compile(r"backlog[\s-]*format\s+version\s+(\d+)", re.IGNORECASE)
LABEL = re.compile(r"^ALARM-\d+$")
PLACEHOLDER = re.compile(r"^NEW-[a-z0-9]+(-[a-z0-9]+)*$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BACKTICK = re.compile(r"^`(.+)`$")
NO_ENTRIES = "No entries."

#: Felder in der Reihenfolge, in der der Codec sie schreibt (gelesen werden sie in jeder).
FIELD_ORDER = ("Uid", "At", "Target", "Status", "Snoozed until", "Created", "Deleted")

TEMPLATE = (
    "# Alarms\n\nFormat: Claude_Harness backlog format version 2. The rules are defined in\n"
    "`docs/techdocs/interfaces.md` of the ToDo Viewer.\n\n## Alarms\n"
)


def format_time(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    value = moment.astimezone(UTC)
    text = value.strftime("%Y-%m-%dT%H:%M:%S")
    if value.microsecond:
        text += f".{value.microsecond:06d}".rstrip("0")
    return text + "Z"


def parse_time(text: str) -> str:
    """Prüft einen Zeitpunkt der Datei und gibt ihn in der Schreibweise des Formats zurück (`ValueError` sonst)."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", text):
        raise ValueError(text)
    return format_time(to_datetime(text)) or ""


def to_datetime(text: str) -> datetime:
    return datetime.fromisoformat(text[:-1] + "+00:00")


def format_day(moment: datetime | None) -> str | None:
    return moment.astimezone(UTC).date().isoformat() if moment is not None else None


def clean(value: str) -> str:
    """Entfernt den Punkt am Ende, den jeder Feldwert im Format trägt."""
    value = value.strip()
    return value[:-1].rstrip() if value.endswith(".") else value


def target_token(value: str, project: str) -> str | None:
    """`None` → kein Ziel; sonst der Verweis des Eintrags: blankes Label im eigenen Projekt, sonst `Projekt:LABEL`."""
    text = clean(value)
    if not text or text == "None":
        return None
    match = BACKTICK.match(text)
    raw = match.group(1) if match else text
    qualifier, separator, label = raw.rpartition(":")
    return label if separator and qualifier == project else raw


def format_line(lines: list[str]) -> tuple[int, int | None]:
    """`(Zeile, Version)` der Kennung (der Absatz, der mit `Format:` beginnt); Zeile 1 und `None`, wenn sie fehlt."""
    for index, line in enumerate(lines):
        if line.startswith("Format:"):
            paragraph = [line]
            for follow in lines[index + 1 :]:
                if not follow.strip():
                    break
                paragraph.append(follow)
            match = FORMAT_VERSION.search(" ".join(paragraph))
            return index + 1, int(match.group(1)) if match else None
    return 1, None

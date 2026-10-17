"""Syntax der Notes-Dateien (Format Version 2): Dateinamen, Zeitpunkte, Verweise, Topic-Zeilen. Reine Funktionen."""

from __future__ import annotations

import re
from datetime import UTC, datetime

NOTES_DIR = "notes"
TOPICS_FILE = "notes/topics.md"
COUNTERS_FILE = "notes/counters.md"

KIND_TOPIC = "notes.topic"
KIND_NOTE = "notes.note"
KIND_DOCUMENT = "notes.document"

#: `NOTE-001.md` und `new-<kurzname>.md`.
NOTE_FILE = re.compile(r"^(?P<stem>NOTE-\d+|new-[A-Za-z0-9-]+)\.md$")
#: `NOTE-001_notes.md`, `NOTE-001_spec.md`, `new-<kurzname>_spec_<thema>.md`.
DOCUMENT_FILE = re.compile(r"^(?P<stem>NOTE-\d+|new-[A-Za-z0-9-]+)_(?P<suffix>notes|spec(?:_[A-Za-z0-9-]+)?)\.md$")
NOTE_LABEL = re.compile(r"^NOTE-\d+$")
TOPIC_LABEL = re.compile(r"^TOPIC-\d+$")
NOTE_PLACEHOLDER = re.compile(r"^new-[a-z0-9]+(-[a-z0-9]+)*$")

#: Kopfzeilen einer Note in der Reihenfolge, in der sie geschrieben werden.
HEADER_KEYS = ("Uid", "Summary", "Status", "Topic", "Review", "Mode", "Created", "Updated", "Archived", "Deleted")
SECTIONS = ("Triggers", "Links")
#: Die Status, die in einer Datei stehen dürfen (`due` ist abgeleitet).
FILE_STATUSES = ("waiting", "snoozed", "done", "dropped", "promoted")
ITEM_STATUSES = ("In progress", "Awaiting confirmation", "Completed", "Rejected")

TRIGGER = re.compile(
    r"^- event (?P<target>.+?) (?P<status>" + "|".join(ITEM_STATUSES) + r")(?P<flags>(?: \[[^\]]*\])*)$"
)
LINK = re.compile(r"^- (?P<role>reference|origin) (?P<target>.+)$")
TOPIC_ROW = re.compile(r"^(?P<indent> *)- (?P<ident>TOPIC-\d+|NEW) \| (?P<rest>.*)$")
TOPIC_KEYS = ("uid", "due", "created", "archived", "deleted")


def format_time(moment: datetime | None) -> str:
    """UTC mit `Z`; Bruchteile von Sekunden nur, wo es welche gibt."""
    if moment is None:
        return ""
    value = moment.astimezone(UTC)
    text = value.strftime("%Y-%m-%dT%H:%M:%S")
    if value.microsecond:
        text += f".{value.microsecond:06d}".rstrip("0")
    return text + "Z"


def parse_time(text: str) -> str:
    """Prüft einen Zeitpunkt der Datei und gibt ihn in der Schreibweise des Formats zurück (`ValueError` sonst)."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", text):
        raise ValueError(text)
    return format_time(datetime.fromisoformat(text[:-1] + "+00:00"))


def to_datetime(text: str) -> datetime:
    return datetime.fromisoformat(text[:-1] + "+00:00")


def normalize_target(raw: str, project: str) -> str:
    """Ein Ziel der Datei als Verweis des Eintrags: `<Projekt>:LABEL` des eigenen Projekts, `topic:X` und `note:X`
    werden zum blanken Label (oder Platzhalter); ein Ziel mit anderem Projektnamen bleibt, wie es steht."""
    raw = raw.strip()
    for prefix in ("topic:", "note:"):
        if raw.startswith(prefix):
            return raw[len(prefix) :]
    qualifier, separator, label = raw.rpartition(":")
    if separator and qualifier == project:
        return label
    return raw


def display_target(token: str, project: str) -> str:
    """Der Verweis des Eintrags, wie er in der Datei steht."""
    if token.startswith("new:"):
        return f"topic:{token}"
    if ":" in token:
        return token  # ein anderes Projekt
    if TOPIC_LABEL.match(token):
        return f"topic:{token}"
    if NOTE_LABEL.match(token) or token.startswith("new-"):
        return f"note:{token}"
    return f"{project}:{token}"


def escape(name: str) -> str:
    return name.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "\\n")


def unescape(text: str) -> str:
    out: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            nxt = text[index + 1]
            out.append({"n": "\n", "|": "|", "\\": "\\"}.get(nxt, "\\" + nxt))
            index += 2
        else:
            out.append(char)
            index += 1
    return "".join(out)


def split_row(rest: str) -> list[str]:
    """Teilt eine Topic-Zeile an den `|`, die nicht mit `\\` maskiert sind (die Teile sind getrimmt)."""
    parts: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(rest):
        char = rest[index]
        if char == "\\" and index + 1 < len(rest):
            current.append(rest[index : index + 2])
            index += 2
            continue
        if char == "|":
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    parts.append("".join(current).strip())
    return parts

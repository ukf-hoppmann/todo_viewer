"""Syntax der Mindmap-Dateien (Format Version 1): Dateinamen, Kopfzeilen, Zeitpunkte, Verweise. Reine Funktionen."""

from __future__ import annotations

import re
from datetime import UTC, datetime

MINDMAP_DIR = "mindmap"
PROJECT_FILE = "mindmap/project.md"
MAPS_DIR = "mindmap/maps"

KIND_NODE = "mindmap.node"
KIND_TREE = "mindmap.tree"
KIND_DOCUMENT = "mindmap.document"

FORMAT_LINE = "mindmap format version 1"

#: `NODE-001.md` und `new-<kurzname>.md`.
NODE_FILE = re.compile(r"^(?P<stem>NODE-\d+|new-[A-Za-z0-9-]+)\.md$")
#: `NODE-001_notes.md`, `NODE-001_spec.md`, `new-<kurzname>_spec_<thema>.md`.
DOCUMENT_FILE = re.compile(r"^(?P<stem>NODE-\d+|new-[A-Za-z0-9-]+)_(?P<suffix>notes|spec(?:_[A-Za-z0-9-]+)?)\.md$")
NODE_LABEL = re.compile(r"^NODE-\d+$")
PLACEHOLDER = re.compile(r"^new-[a-z0-9]+(-[a-z0-9]+)*$")
#: Ein Knoten in einer Baumliste: Label oder Platzhalter.
NODE_TOKEN = re.compile(r"^(NODE-\d+|new-[a-z0-9]+(-[a-z0-9]+)*)$")

NODE_KEYS = ("Uid", "Title", "Mark", "Deleted")
NODE_SECTIONS = ("Items", "Memos")
TREE_KEYS = ("Format", "Uid", "Kind", "Name", "Deleted")

TREE_ROW = re.compile(r"^(?P<indent> *)- (?P<token>\S.*)$")
REMOVED_ROW = re.compile(r"^- (?P<node>\S+) parent (?P<parent>\S+) position (?P<position>\d+) group (?P<group>\S+)$")
UID_LINE = re.compile(r"^Uid: (?P<uid>\S+)$", re.MULTILINE)


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


def normalize_target(raw: str, project: str) -> str:
    """Ein Ziel der Datei als Verweis des Eintrags: `<Projekt>:LABEL` des eigenen Projekts wird zum blanken Label, ein
    Ziel mit anderem Projektnamen bleibt, wie es steht."""
    raw = raw.strip()
    qualifier, separator, label = raw.rpartition(":")
    if separator and qualifier == project:
        return label
    return raw


def display_target(token: str, project: str) -> str:
    """Der Verweis des Eintrags, wie er in der Datei steht."""
    return token if ":" in token else f"{project}:{token}"


def slug(name: str) -> str:
    """Der Dateiname einer freien Map: `a-z0-9-`, ohne Rand und Doppelungen; Umlaute werden umschrieben."""
    folded = name.casefold().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-") or "map"


def map_path(slug_name: str) -> str:
    return f"{MAPS_DIR}/{slug_name}.md"

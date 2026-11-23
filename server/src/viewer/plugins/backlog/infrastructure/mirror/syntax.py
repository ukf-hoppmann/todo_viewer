"""Syntax der Backlog-Dateien (Format Version 3): Einträge, Felder, Kennung. Reine Funktionen auf Zeilen."""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass

TODO_FILE = "TODO.md"
ARCHIVE_FILE = "archive.md"

HEADER = re.compile(r"^- `([A-Za-z0-9_.\-]+)`\s+\*\*(.+?)\*\*\s*$")
FIELD = re.compile(r"^ {2}- ([A-Za-z][A-Za-z ]*?):\s?(.*)$")
WORK_ITEMS = re.compile(r"^## Work items\s*$")
FORMAT_VERSION = re.compile(r"backlog[\s-]*format\s+version\s+(\d+)", re.IGNORECASE)
LABEL = re.compile(r"^(EPIC|STORY|TASK)-\d{3,}$")
PLACEHOLDER = re.compile(r"^NEW-[a-z0-9]+(-[a-z0-9]+)*$")
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BACKTICK_ID = re.compile(r"`([A-Za-z0-9_.\-]+)`")
NO_ENTRIES = "No entries."
LINE_WIDTH = 76
#: Eine Folgezeile, die so beginnt, ist ein harter Umbruch (Listenpunkt); jede andere setzt die Zeile davor nur fort.
LIST_MARKER = re.compile(r"^(\d+[.)]|[-*])\s")

#: Felder und ihre Reihenfolge (der Codec schreibt in dieser Reihenfolge und liest in jeder).
FIELD_ORDER = (
    "Uid",
    "Type",
    "Parent",
    "Required for parent",
    "Status",
    "Created",
    "Priority",
    "Dependencies",
    "Goal",
    "Completion criteria",
    "Summary",
    "Resolution",
    "Deleted",
)
#: Gelesene Versionen der Kennung; geschrieben wird immer `WRITE_VERSION`.
READ_VERSIONS = (2, 3)
WRITE_VERSION = 3
#: Felder, die frühere Versionen kannten: beim Lesen ignoriert (kein Fehler), beim Schreiben eines Eintrags entfernt.
IGNORED_FIELDS = frozenset({"Area"})
#: Texte, die so stehen, wie sie sind (kein Punkt am Ende gehört zum Format).
FREE_TEXT = frozenset({"Goal", "Completion criteria", "Summary", "Resolution"})
#: Verweisfelder: Labels in Backticks, `None` ohne Verweis.
REFERENCE_FIELDS = frozenset({"Parent", "Dependencies"})


@dataclass
class RawField:
    label: str
    value: str
    line: int  # 1-basiert, erste Zeile des Feldes
    first: int  # Index der ersten Zeile
    end: int  # Index nach der letzten Zeile (Fortsetzungszeilen eingeschlossen)


@dataclass
class Block:
    """Ein Eintrag: Kopfzeile und Felder."""

    ident: str
    title: str
    line: int  # 1-basiert, Kopfzeile
    first: int
    end: int  # Index nach der letzten Zeile des Eintrags
    fields: list[RawField]

    def field(self, label: str) -> RawField | None:
        return next((f for f in self.fields if f.label == label), None)


def clean(value: str) -> str:
    """Entfernt den Punkt am Ende, den jeder Feldwert im Format trägt."""
    value = value.strip()
    return value[:-1].rstrip() if value.endswith(".") else value


def references(value: str) -> tuple[str, ...]:
    return tuple(BACKTICK_ID.findall(value))


def work_items_start(lines: list[str]) -> int:
    """Index der Überschrift `## Work items`; ohne sie beginnen die Einträge bei 0."""
    return next((i for i, line in enumerate(lines) if WORK_ITEMS.match(line)), -1) + 1


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


def upgrade_format_line(lines: list[str]) -> None:
    """Setzt die Version in der Kennung auf `WRITE_VERSION` (an Ort und Stelle); ohne Kennung bleibt alles."""
    for index, line in enumerate(lines):
        if line.startswith("Format:"):
            while index < len(lines) and lines[index].strip():
                lines[index] = FORMAT_VERSION.sub(
                    lambda m: re.sub(r"\d+$", str(WRITE_VERSION), m.group(0)), lines[index]
                )
                index += 1
            return


def parse_blocks(lines: list[str]) -> list[Block]:
    """Die Einträge unter `## Work items` mit ihren Feldern (Fortsetzungszeilen gehören zum letzten Feld)."""
    blocks: list[Block] = []
    current: Block | None = None
    for index in range(work_items_start(lines), len(lines)):
        raw = lines[index]
        header = HEADER.match(raw)
        if header:
            if current is not None:
                current.end = _last_used(current)
            current = Block(header.group(1), header.group(2), index + 1, index, index + 1, [])
            blocks.append(current)
            continue
        if current is None:
            continue
        field = FIELD.match(raw)
        if field:
            current.fields.append(RawField(field.group(1).strip(), field.group(2).strip(), index + 1, index, index + 1))
            continue
        if not raw.strip():
            continue
        if not raw.startswith(" "):
            # Text ohne Einrückung (z. B. eine neue Überschrift) beendet den Eintrag.
            current.end = _last_used(current)
            current = None
            continue
        if current.fields:
            last = current.fields[-1]
            text = raw.strip()
            last.value += ("\n" if LIST_MARKER.match(text) else " ") + text
            last.end = index + 1
    if current is not None:
        current.end = _last_used(current)
    return blocks


def _last_used(block: Block) -> int:
    return block.fields[-1].end if block.fields else block.first + 1


def with_period(value: str) -> str:
    return value if value.endswith(".") else value + "."


def logical_lines(value: str) -> list[str]:
    """Der Text als logische Zeilen: nur vor einem Listenpunkt bleibt ein Umbruch, sonst gilt Fließtext."""
    lines: list[str] = []
    for raw in value.splitlines():
        text = " ".join(raw.split())
        if not text:
            continue
        if lines and not LIST_MARKER.match(text):
            lines[-1] += " " + text
        else:
            lines.append(text)
    return lines


def field_lines(label: str, value: str) -> list[str]:
    """Die Zeilen eines Feldes; lange Werte umbrechen, Fortsetzungszeilen sind vier Leerzeichen eingerückt.

    Jeder Listenpunkt beginnt eine eigene Zeile; ein weicher Umbruch setzt nie mit einem Listenpunkt an.
    """
    lines: list[str] = []
    for index, logical in enumerate(logical_lines(value) or [""]):
        wrapped = textwrap.wrap(
            logical,
            width=LINE_WIDTH,
            initial_indent=f"  - {label}: " if index == 0 and not lines else "    ",
            subsequent_indent="    ",
            break_long_words=False,
            break_on_hyphens=False,
        )
        for line in wrapped[:1]:
            lines.append(line)
        for line in wrapped[1:]:
            if LIST_MARKER.match(line.strip()):
                lines[-1] += " " + line.strip()
            else:
                lines.append(line)
    return lines or [f"  - {label}: "]


def reference_text(labels: tuple[str, ...]) -> str:
    return ", ".join(f"`{label}`" for label in labels) if labels else "None"


def same_text(a: str, b: str) -> bool:
    """Gleicher Text, unabhängig vom Umbruch."""
    return logical_lines(a) == logical_lines(b)

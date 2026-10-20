"""Aufbau der Item-Notes: Titelzeile, Vorspann, Kopf (`## Stand`) mit Stempel und Protokoll aus datierten Einträgen.

Zerlegen und Zusammensetzen sind verlustfrei für Notes ohne Kopf (bis auf die Titelzeile, die immer aus dem Item
kommt); Notes mit Kopf werden auf ein festes Layout gebracht. Der Aufbau ist mit dem Harness abgestimmt (dort
`format.md`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from viewer.plugins.backlog.domain.model import Item

ENTRY_HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2}) — (.*)$")
STATE_HEADING = "## Stand"
STAMP_LINE = re.compile(r"^Stand bestätigt nach Eintrag (\d{4}-\d{2}-\d{2}) — (.+) \(([0-9a-f]{12})\)$")


@dataclass(frozen=True)
class Stamp:
    """Gegen welchen Eintrag und welche Prüfsumme des Protokolls der Kopf zuletzt bestätigt wurde."""

    day: str
    topic: str
    checksum: str


@dataclass(frozen=True)
class Entry:
    """Ein Protokolleintrag; `body` ist der Text nach der Überschriftszeile, unverändert."""

    day: str
    topic: str
    body: str


@dataclass(frozen=True)
class NotesParts:
    """Die Teile einer Notes-Datei ohne Titelzeile; `state` ist leer, wenn es keinen Kopf gibt."""

    preamble: str
    state: str
    stamp: Stamp | None
    entries: tuple[Entry, ...]


def title_of(item: Item) -> str:
    return f"{item.label} — {item.title}"


def stamp_line(stamp: Stamp) -> str:
    return f"Stand bestätigt nach Eintrag {stamp.day} — {stamp.topic} ({stamp.checksum})"


def entry_text(entry: Entry) -> str:
    return f"## {entry.day} — {entry.topic}\n{entry.body}"


def _bare(line: str) -> str:
    return line.rstrip("\r\n")


def split(text: str) -> NotesParts:
    """Zerlegt eine Notes-Datei; eine Titelzeile (erste Zeile, beginnt mit `# `) wird verworfen."""
    lines = text.splitlines(keepends=True)
    start = 1 if lines and lines[0].startswith("# ") else 0
    first = next((i for i in range(start, len(lines)) if ENTRY_HEADING.match(_bare(lines[i]))), len(lines))
    before = lines[start:first]
    heading = next((i for i, line in enumerate(before) if _bare(line).rstrip() == STATE_HEADING), None)
    if heading is None:
        preamble, state, stamp = "".join(before), "", None
    else:
        preamble = "".join(before[:heading])
        state, stamp = _state(before[heading + 1 :])
    return NotesParts(preamble, state, stamp, _entries(lines[first:]))


def _state(lines: list[str]) -> tuple[str, Stamp | None]:
    content = [_bare(line) for line in lines]
    while content and not content[-1].strip():
        content.pop()
    stamp = None
    if content and (match := STAMP_LINE.match(content[-1])):
        stamp = Stamp(match.group(1), match.group(2), match.group(3))
        content.pop()
        while content and not content[-1].strip():
            content.pop()
    while content and not content[0].strip():
        content.pop(0)
    return "\n".join(content), stamp


def _entries(lines: list[str]) -> tuple[Entry, ...]:
    entries: list[Entry] = []
    for line in lines:
        match = ENTRY_HEADING.match(_bare(line))
        if match:
            entries.append(Entry(match.group(1), match.group(2), ""))
        else:
            last = entries[-1]
            entries[-1] = Entry(last.day, last.topic, last.body + line)
    return tuple(entries)


def assemble(title: str, parts: NotesParts) -> str:
    """Setzt die Datei zusammen: Titelzeile, Vorspann, falls vorhanden Kopf mit Stempel, dann die Einträge."""
    text = f"# {title}\n"
    if parts.state:
        preamble = parts.preamble
        if not preamble.strip():
            preamble = "\n"
        elif not preamble.endswith("\n\n"):
            preamble = preamble.rstrip("\n") + "\n\n"
        text += f"{preamble}{STATE_HEADING}\n\n{parts.state}\n\n"
        if parts.stamp is not None:
            text += f"{stamp_line(parts.stamp)}\n\n"
    else:
        text += parts.preamble
    return text + "".join(entry_text(entry) for entry in parts.entries)


def without_title(text: str) -> str:
    """Der Text ohne eine Titelzeile (erste Zeile, beginnt mit `# `); die Titelzeile ist abgeleitet."""
    return text.partition("\n")[2] if text.startswith("# ") else text


def split_lossless(text: str) -> NotesParts:
    """Wie `split`, aber ergibt das Zusammensetzen von Notes ohne Kopf nicht wieder den Text (bis auf die
    Titelzeile), wird der ganze Text nach der Titelzeile Vorspann. So geht beim Überführen nie Text verloren."""
    parts = split(text)
    if parts.state or without_title(assemble("", parts)) == without_title(text):
        return parts
    return NotesParts(without_title(text), "", None, ())


def has_state_section(text: str) -> bool:
    """Steht vor dem ersten Eintrag ein Abschnitt `## Stand`?"""
    for line in text.splitlines():
        if ENTRY_HEADING.match(line):
            return False
        if line.rstrip() == STATE_HEADING:
            return True
    return False


def replaced_by_text(old: NotesParts, text: str) -> NotesParts:
    """Neue Teile, wenn ein Client die ganze Datei über die API ersetzt: Vorspann und Protokoll kommen aus dem Text,
    der Kopf nur, wenn der Text `## Stand` enthält (ältere Clients kennen ihn nicht). Den Stempel setzt über die API
    nur der Server, eine Stempelzeile im Text zählt nicht."""
    new = split(text)
    return NotesParts(new.preamble, new.state if has_state_section(text) else old.state, old.stamp, new.entries)

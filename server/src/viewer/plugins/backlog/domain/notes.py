"""Aufbau der Item-Notes: Titelzeile, Vorspann, Kopf (`## Stand`) mit Stempel und Protokoll aus datierten Einträgen.

Zerlegen und Zusammensetzen sind verlustfrei für Notes ohne Kopf (bis auf die Titelzeile, die immer aus dem Item
kommt); Notes mit Kopf werden auf ein festes Layout gebracht. Der Aufbau ist mit dem Harness abgestimmt (dort
`format.md`).
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass, replace

from viewer.core.domain.errors import DomainError
from viewer.plugins.backlog.domain.model import Item

ENTRY_HEADING = re.compile(r"^## (\d{4}-\d{2}-\d{2}) — (.*)$")
STATE_HEADING = "## Stand"
STAMP_LINE = re.compile(r"^Stand bestätigt nach Eintrag (\d{4}-\d{2}-\d{2}) — (.+) \(([0-9a-f]{12})\)$")
DECIDED_HEADING = "- Beschlossen:"
#: Ab so vielen Punkten unter `- Beschlossen:` gibt es einen Hinweis (Spec schreiben oder Item teilen?), nie eine
#: Ablehnung (STORY-051).
LONG_STATE = 15
CURRENT, STALE, MISSING = "current", "stale", "missing"


class NotesNotFound(DomainError):
    code = "notes_not_found"


class NotesStateMissing(DomainError):
    code = "notes_state_missing"


class NotesWithoutEntries(DomainError):
    code = "notes_without_entries"


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


# --- Prüfsumme, Zustand und Hinweise ------------------------------------------------------------------------------


def canonical(entries: Sequence[Entry]) -> str:
    """Kanonische Form des Protokolls (gemeinsamer Vertrag mit dem Harness, dort `format.md`): alle Einträge ab der
    ersten Eintragszeile, LF als Zeilenende, Leerzeichen und Tabs am Zeilenende entfernt, genau ein Zeilenumbruch am
    Ende."""
    text = "".join(entry_text(entry) for entry in entries).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip(" \t") for line in text.split("\n")).rstrip("\n") + "\n"


def checksum(entries: Sequence[Entry]) -> str:
    """Die ersten 12 Hex-Zeichen von SHA-256 über die kanonische Form (UTF-8)."""
    return hashlib.sha256(canonical(entries).encode("utf-8")).hexdigest()[:12]


def state_of(parts: NotesParts) -> str:
    """`missing` ohne Kopf, `stale` ohne Stempel oder mit abweichender Prüfsumme, sonst `current`."""
    if not parts.state.strip():
        return MISSING
    if parts.stamp is None or parts.stamp.checksum != checksum(parts.entries):
        return STALE
    return CURRENT


def state_text(content: str) -> str:
    """Der Text eines neuen Kopfs ohne umgebende Leerzeilen; eine Stempelzeile am Ende zählt nicht (den Stempel setzt
    der Server)."""
    return _state(content.splitlines(keepends=True))[0]


def stamped(parts: NotesParts) -> NotesParts:
    """Setzt den Stempel auf den letzten Eintrag und die aktuelle Prüfsumme; das Protokoll bleibt unverändert."""
    if not parts.entries:
        raise NotesWithoutEntries("Ohne Protokolleintrag lässt sich der Kopf nicht bestätigen; zuerst einen anhängen")
    last = parts.entries[-1]
    return replace(parts, stamp=Stamp(last.day, last.topic, checksum(parts.entries)))


def history_rewritten(before: NotesParts, after: NotesParts) -> bool:
    """Wurde ein bisheriger Eintrag geändert oder entfernt? Neue Einträge am Ende zählen nicht."""
    return any(i >= len(after.entries) or after.entries[i] != entry for i, entry in enumerate(before.entries))


def decided_count(state: str) -> int:
    """Die Unterpunkte unter `- Beschlossen:` bis zum nächsten Punkt der obersten Ebene."""
    count, inside = 0, False
    for line in state.splitlines():
        if line.rstrip() == DECIDED_HEADING:
            inside = True
        elif line.startswith("- "):
            inside = False
        elif inside and line.lstrip().startswith("- "):
            count += 1
    return count


@dataclass(frozen=True)
class Hint:
    """Etwas, das der Aufrufer nach dem Schreiben wissen sollte; nie eine Ablehnung. `code` ist stabil."""

    code: str
    message: str


def hints(before: NotesParts | None, after: NotesParts, *, rewritten: bool) -> tuple[Hint, ...]:
    """Hinweise nach einer Änderung der Notes; `rewritten`: die ganze Datei wurde ersetzt."""
    found: list[Hint] = []
    if state_of(after) != CURRENT:
        found.append(Hint("notes_state_stale", "Der Kopf der Notes ist nicht aktuell: anpassen oder bestätigen"))
    if decided_count(after.state) > LONG_STATE:
        found.append(
            Hint("notes_state_long", f"Mehr als {LONG_STATE} Beschlüsse im Kopf: Spec schreiben oder Item teilen?")
        )
    if rewritten and before is not None and history_rewritten(before, after):
        found.append(Hint("notes_history_rewritten", "Ein älterer Protokolleintrag wurde geändert oder entfernt"))
    return tuple(found)

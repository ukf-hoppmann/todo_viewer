"""Head (`## State`) of item notes: split a notes file, checksum of its log, state, and confirming the head.

The format is defined in skills/todo/format.md (section Notes) and shared with the ToDo-Viewer.
"""

from __future__ import annotations

import hashlib
import re
from typing import NamedTuple

STATE_HEADING = "## State"
DECIDED_MARKER = "- Decided:"
#: More points than this under `- Decided:` give a hint, never a rejection.
LONG_STATE = 15
CURRENT, STALE, MISSING = "current", "stale", "missing"

_ENTRY = re.compile(r"^## (\d{4}-\d{2}-\d{2}) — (.*)$")
_STAMP = re.compile(r"^State confirmed after entry (\d{4}-\d{2}-\d{2}) — (.+) \(([0-9a-f]{12})\)$")


class NotesHeadError(Exception):
    pass


class Stamp(NamedTuple):
    day: str
    topic: str
    checksum: str


class NotesParts(NamedTuple):
    title: str
    preamble: str
    state: str  # head content without heading and stamp line; empty without a head
    stamp: Stamp | None
    entries: str  # the log, from the first entry line to the end, unchanged


class _Layout(NamedTuple):
    lines: list[str]
    heading: int | None  # index of the `## State` line
    first_entry: int  # index of the first entry line (len(lines) without entries)


def _bare(line: str) -> str:
    return line.rstrip("\r\n")


def _layout(text: str) -> _Layout:
    lines = text.splitlines(keepends=True)
    start = 1 if lines and lines[0].startswith("# ") else 0
    first = next((i for i in range(start, len(lines)) if _ENTRY.match(_bare(lines[i]))), len(lines))
    heading = next((i for i in range(start, first) if _bare(lines[i]).rstrip() == STATE_HEADING), None)
    return _Layout(lines, heading, first)


def _last_content(lines: list[str], begin: int, end: int) -> int | None:
    return next((i for i in range(end - 1, begin - 1, -1) if lines[i].strip()), None)


def split(text: str) -> NotesParts:
    layout = _layout(text)
    lines, heading, first = layout
    title = _bare(lines[0]) if lines and lines[0].startswith("# ") else ""
    start = 1 if title else 0
    entries = "".join(lines[first:])
    if heading is None:
        return NotesParts(title, "".join(lines[start:first]), "", None, entries)
    end = first
    stamp = None
    last = _last_content(lines, heading + 1, first)
    if last is not None and (match := _STAMP.match(_bare(lines[last]))):
        stamp = Stamp(*match.groups())
        end = last
    state = "".join(lines[heading + 1 : end]).strip("\r\n")
    return NotesParts(title, "".join(lines[start:heading]), state, stamp, entries)


def canonical(log: str) -> str:
    """LF line endings, spaces and tabs stripped at line ends, exactly one line break at the end."""
    text = log.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip(" \t") for line in text.split("\n")).rstrip("\n") + "\n"


def checksum(log: str) -> str:
    """The first 12 hex characters of SHA-256 over the canonical log (UTF-8)."""
    return hashlib.sha256(canonical(log).encode("utf-8")).hexdigest()[:12]


def state_of(text: str) -> str:
    parts = split(text)
    if not parts.state.strip():
        return MISSING
    if parts.stamp is None or parts.stamp.checksum != checksum(parts.entries):
        return STALE
    return CURRENT


def _entries(log: str) -> list[tuple[str, str]]:
    """(heading line, body) per entry, unchanged."""
    found: list[tuple[str, str]] = []
    for line in log.splitlines(keepends=True):
        if _ENTRY.match(_bare(line)):
            found.append((line, ""))
        elif found:
            found[-1] = (found[-1][0], found[-1][1] + line)
    return found


def last_entry(text: str) -> tuple[str, str] | None:
    entries = _entries(split(text).entries)
    if not entries:
        return None
    match = _ENTRY.match(_bare(entries[-1][0]))
    return (match.group(1), match.group(2)) if match else None


def confirmed(text: str) -> str:
    """The text with the stamp line set to the last entry and the current checksum; nothing else changes."""
    parts = split(text)
    if not parts.state.strip():
        raise NotesHeadError("the notes have no head (## State); write it first")
    entry = last_entry(text)
    if entry is None:
        raise NotesHeadError("the notes have no log entry yet; append one first")
    newline = "\r\n" if "\r\n" in text else "\n"
    stamp = f"State confirmed after entry {entry[0]} — {entry[1]} ({checksum(parts.entries)})"
    lines, heading, first = _layout(text)
    last = _last_content(lines, heading + 1, first)
    if parts.stamp is not None and last is not None:
        ending = lines[last][len(_bare(lines[last])) :] or newline
        lines[last] = stamp + ending
    else:
        insert = [newline, stamp + newline]
        if last + 1 >= len(lines) or lines[last + 1].strip():
            insert.append(newline)
        if not lines[last].endswith(("\n", "\r")):
            lines[last] += newline
        lines[last + 1 : last + 1] = insert
    return "".join(lines)


def decided_count(text: str) -> int:
    """Bullets below `- Decided:` up to the next top-level point, nested ones included (like the ToDo-Viewer)."""
    count, inside = 0, False
    for line in split(text).state.splitlines():
        if line.rstrip() == DECIDED_MARKER:
            inside = True
        elif line.startswith("- "):
            inside = False
        elif inside and line.lstrip().startswith("- "):
            count += 1
    return count


def history_rewritten(old_text: str, new_text: str) -> bool:
    """Was an earlier entry changed or removed? New entries at the end do not count, and neither do line endings,
    spaces at line ends, or blank lines at the end of an entry (appending usually adds one)."""

    def normalized(log: str) -> list[str]:
        return [canonical(heading + body).rstrip("\n") for heading, body in _entries(log)]

    before, after = normalized(split(old_text).entries), normalized(split(new_text).entries)
    return any(i >= len(after) or after[i] != entry for i, entry in enumerate(before))

"""Notes, topics, and the label counters as text files (the format of the notes mirror, STORY-047).

Pure functions on the standard library. A note is one file `NOTE-001.md`: a header with one `Key: value` per line, one
line per trigger and link (so Git merges them cleanly), a blank line, and the body unchanged. Topics are one indented
list in `topics.md`, the counters one line per kind in `counters.md`. Points in time are UTC with a `Z`.
Notices between notes and items are not part of the format.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypeVar

from .errors import NoteFormatError
from .item import Status
from .notes import (
    EVENT_STATUSES,
    Link,
    LinkRole,
    Note,
    NoteStatus,
    TargetKind,
    Topic,
    Trigger,
    TriggerKind,
    TriggerMode,
)

NO_LABEL = "NEW"  # first line of a note (and label of a topic) created in the files, before the database names it
NEW_TOPIC = "new:"  # `Topic: new:<Name>`: a topic without a label yet
_HEADER_KEYS = ("Summary", "Status", "Topic", "Review", "Mode", "Created", "Updated", "Archived", "Deleted")
_LABEL = re.compile(r"[A-Za-z][A-Za-z0-9]*-\d+")


@dataclass(frozen=True)
class ParsedTarget:
    """What a link or an event trigger points at; `project` is None for topics and notes (the same project)."""

    kind: TargetKind
    label: str
    project: str | None = None

    def __str__(self) -> str:
        if self.kind is TargetKind.ITEM:
            return f"{self.project}:{self.label}"
        return f"{self.kind.value}:{self.label}"


@dataclass(frozen=True)
class ParsedLink:
    role: LinkRole  # reference or origin; links with the role trigger are shown by the event triggers
    target: ParsedTarget


@dataclass(frozen=True)
class ParsedTrigger:
    kind: TriggerKind
    at: datetime | None = None
    target: ParsedTarget | None = None
    status: str | None = None
    fired_at: datetime | None = None
    already_met: bool = False


@dataclass(frozen=True)
class ParsedNote:
    label: str | None  # None: a note created in the files, not yet labelled
    summary: str
    status: NoteStatus = NoteStatus.WAITING
    topic: str | None = None  # a topic label, or `new:<Name>`
    review_at: datetime | None = None
    mode: TriggerMode = TriggerMode.ANY
    created: datetime | None = None
    updated: datetime | None = None
    archived: bool = False
    deleted: datetime | None = None
    triggers: tuple[ParsedTrigger, ...] = ()
    links: tuple[ParsedLink, ...] = ()
    body: str | None = None
    newline: str = "\n"  # the line ending of the text it was read from


@dataclass(frozen=True)
class TopicLine:
    """One topic of `topics.md`. `parent` is a topic label or `new:<Name>`; None for a top-level topic."""

    label: str | None
    name: str
    parent: str | None = None
    due_at: datetime | None = None
    created: datetime | None = None
    deleted: datetime | None = None

    @property
    def key(self) -> str:
        """How others refer to it: its label, or `new:<Name>` while it has none."""
        return self.label or f"{NEW_TOPIC}{self.name}"


# --- points in time ---

def format_moment(moment: datetime) -> str:
    """UTC with a `Z`; fractions of a second only where there are some, so nothing is lost."""
    utc = moment.astimezone(UTC)
    text = utc.strftime("%Y-%m-%dT%H:%M:%S")
    if utc.microsecond:
        text += f".{utc.microsecond:06d}".rstrip("0")
    return text + "Z"


def moment_text(value: datetime | None) -> str:
    """A point in time as text, empty if there is none."""
    return "" if value is None else format_moment(value)


def _moment(text: str, line: int, file: str | None) -> datetime:
    value = text.strip()
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        raise NoteFormatError(f"not a point in time: {value!r}", line, file) from None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _optional_moment(text: str, line: int, file: str | None) -> datetime | None:
    return _moment(text, line, file) if text.strip() else None


# --- notes ---

def render_note(note: Note, triggers: Sequence[Trigger], links: Sequence[Link], newline: str = "\n") -> str:
    """The file of a stored note; links with the role `trigger` are left out (the event triggers show them)."""
    return render_parsed(to_parsed(note, triggers, links), newline)


def to_parsed(note: Note, triggers: Sequence[Trigger], links: Sequence[Link]) -> ParsedNote:
    return ParsedNote(
        label=note.label, summary=note.summary, status=note.status, topic=note.topic, review_at=note.review_at,
        mode=note.trigger_mode, created=note.created, updated=note.updated, archived=note.archived,
        deleted=note.deleted, body=note.body or None,
        triggers=tuple(ParsedTrigger(
            kind=t.kind, at=t.at, status=t.target_status, fired_at=t.fired_at, already_met=t.already_met,
            target=None if t.target is None else ParsedTarget(t.target.kind, t.target.label, t.target.project))
            for t in triggers),
        links=tuple(ParsedLink(link.role, ParsedTarget(
            link.target.kind, link.target.label, link.target.project if link.target.kind is TargetKind.ITEM else None))
            for link in links if link.role is not LinkRole.TRIGGER))


def render_parsed(note: ParsedNote, newline: str | None = None) -> str:
    eol = newline or note.newline
    moment = moment_text
    lines = [f"# {note.label or NO_LABEL}", f"Summary: {note.summary}", f"Status: {note.status.value}",
             f"Topic: {note.topic or ''}", f"Review: {moment(note.review_at)}", f"Mode: {note.mode.value}",
             f"Created: {moment(note.created)}", f"Updated: {moment(note.updated)}",
             f"Archived: {'true' if note.archived else 'false'}", f"Deleted: {moment(note.deleted)}"]
    lines = [line.rstrip() for line in lines]
    if note.triggers:
        lines += ["Triggers:", *(trigger_line(t) for t in note.triggers)]
    if note.links:
        lines += ["Links:", *(f"- {link.role.value} {link.target}" for link in note.links)]
    text = eol.join(lines) + eol
    return text + eol + note.body if note.body else text


def trigger_line(trigger: ParsedTrigger) -> str:
    if trigger.kind is TriggerKind.TOPIC_DUE:
        text = "- topic_due"
    elif trigger.kind is TriggerKind.TIME:
        text = f"- time {format_moment(trigger.at) if trigger.at else ''}".rstrip()
    else:
        text = f"- event {trigger.target} {trigger.status or ''}".rstrip()
    if trigger.fired_at:
        text += f" [fired {format_moment(trigger.fired_at)}]"
    if trigger.already_met:
        text += " [already_met]"
    return text


def parse_note(text: str, file: str | None = None) -> ParsedNote:
    """Reads a note file; anything that does not belong to the format is an error with its line number."""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    header, body = _split(lines, newline)
    if not header or not header[0].startswith("# "):
        raise NoteFormatError("a note starts with '# <label>'", 1, file)
    name = header[0][2:].strip()
    label = None if name == NO_LABEL else name
    if label is not None and not _LABEL.fullmatch(label) and not name.startswith("new-"):
        raise NoteFormatError(f"not a label: {name!r}", 1, file)
    fields: dict[str, tuple[str, int]] = {}
    triggers: list[ParsedTrigger] = []
    links: list[ParsedLink] = []
    block: str | None = None
    for number, line in enumerate(header[1:], start=2):
        if line.startswith("- "):
            if block == "Triggers":
                triggers.append(_parse_trigger(line[2:], number, file))
            elif block == "Links":
                links.append(_parse_link(line[2:], number, file))
            else:
                raise NoteFormatError("a list entry outside Triggers: or Links:", number, file)
            continue
        key, colon, value = line.partition(":")
        if not colon or key not in (*_HEADER_KEYS, "Triggers", "Links"):
            raise NoteFormatError(f"unknown header line: {line!r}", number, file)
        if key in ("Triggers", "Links"):
            block = key
        else:
            block = None
            if key in fields:
                raise NoteFormatError(f"{key} twice", number, file)
            fields[key] = (value.strip(), number)
    if "Summary" not in fields:
        raise NoteFormatError("Summary is missing", 0, file)
    return ParsedNote(
        label=label, summary=fields["Summary"][0], status=_enum(NoteStatus, fields, "Status", NoteStatus.WAITING, file),
        topic=fields.get("Topic", ("", 0))[0] or None, review_at=_field_moment(fields, "Review", file),
        mode=_enum(TriggerMode, fields, "Mode", TriggerMode.ANY, file), created=_field_moment(fields, "Created", file),
        updated=_field_moment(fields, "Updated", file), archived=_flag(fields, file),
        deleted=_field_moment(fields, "Deleted", file), triggers=tuple(triggers), links=tuple(links),
        body=body or None, newline=newline)


def _split(lines: list[str], newline: str) -> tuple[list[str], str]:
    """The header lines and the body (everything after the first blank line, exactly as it was)."""
    for index, line in enumerate(lines):
        if line == "":
            return lines[:index], newline.join(lines[index + 1:])
    return lines, ""


E = TypeVar("E")


def _enum(kind: type[E], fields: Mapping[str, tuple[str, int]], key: str, default: E, file: str | None) -> E:
    if key not in fields or not fields[key][0]:
        return default
    value, line = fields[key]
    try:
        return kind(value)  # type: ignore[call-arg]
    except ValueError:
        raise NoteFormatError(f"invalid {key}: {value!r}", line, file) from None


def _field_moment(fields: Mapping[str, tuple[str, int]], key: str, file: str | None) -> datetime | None:
    if key not in fields:
        return None
    value, line = fields[key]
    return _optional_moment(value, line, file)


def _flag(fields: Mapping[str, tuple[str, int]], file: str | None) -> bool:
    if "Archived" not in fields or not fields["Archived"][0]:
        return False
    value, line = fields["Archived"]
    if value not in ("true", "false"):
        raise NoteFormatError(f"Archived is true or false, not {value!r}", line, file)
    return value == "true"


_FIRED = re.compile(r" \[fired ([^\]]+)\]")


def _parse_trigger(text: str, line: int, file: str | None) -> ParsedTrigger:
    already_met = text.endswith(" [already_met]")
    text = text.removesuffix(" [already_met]")
    fired_at = None
    found = _FIRED.search(text)
    if found:
        fired_at = _moment(found.group(1), line, file)
        text = text[:found.start()] + text[found.end():]
    kind, _, rest = text.partition(" ")
    if kind == "topic_due" and not rest:
        return ParsedTrigger(TriggerKind.TOPIC_DUE, fired_at=fired_at, already_met=already_met)
    if kind == "time":
        return ParsedTrigger(TriggerKind.TIME, at=_moment(rest, line, file), fired_at=fired_at, already_met=already_met)
    if kind == "event":
        for status in sorted({*EVENT_STATUSES, Status.OPEN}, key=len, reverse=True):
            if rest.endswith(f" {status}"):
                target = rest[: -len(status) - 1]
                return ParsedTrigger(TriggerKind.EVENT, target=_parse_target(target, line, file, item_only=True),
                                     status=status, fired_at=fired_at, already_met=already_met)
        raise NoteFormatError(f"an event names a status: {rest!r}", line, file)
    raise NoteFormatError(f"unknown trigger: {text!r}", line, file)


def _parse_link(text: str, line: int, file: str | None) -> ParsedLink:
    role, _, target = text.partition(" ")
    try:
        link_role = LinkRole(role)
    except ValueError:
        raise NoteFormatError(f"unknown link role: {role!r}", line, file) from None
    if link_role is LinkRole.TRIGGER:
        raise NoteFormatError("links of the role trigger are given by the event triggers", line, file)
    return ParsedLink(link_role, _parse_target(target, line, file))


def _parse_target(text: str, line: int, file: str | None, item_only: bool = False) -> ParsedTarget:
    head, colon, label = text.rpartition(":")
    if not colon or not head or not label or " " in label:
        raise NoteFormatError(f"a target is 'project:label', 'topic:label' or 'note:label': {text!r}", line, file)
    if not item_only and head in (TargetKind.TOPIC.value, TargetKind.NOTE.value):
        return ParsedTarget(TargetKind(head), label)
    return ParsedTarget(TargetKind.ITEM, label, head)


# --- topics ---

def _escape(name: str) -> str:
    return name.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "\\n")


def _unescape(text: str) -> str:
    out, index = [], 0
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            out.append({"n": "\n"}.get(text[index + 1], text[index + 1]))
            index += 2
        else:
            out.append(text[index])
            index += 1
    return "".join(out)


def _cells(text: str) -> list[str]:
    cells, current, index = [], [], 0
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text):
            current.append(text[index:index + 2])
            index += 2
        elif text[index] == "|":
            cells.append("".join(current).strip())
            current = []
            index += 1
        else:
            current.append(text[index])
            index += 1
    cells.append("".join(current).strip())
    return cells


def to_lines(topics: Sequence[Topic]) -> list[TopicLine]:
    return [TopicLine(t.label, t.name, t.parent, t.due_at, t.created, t.deleted) for t in topics]


def render_topics(topics: Sequence[TopicLine], newline: str = "\n") -> str:
    """The topics as an indented list, children under their parent, in the order given otherwise."""
    children: dict[str | None, list[TopicLine]] = {}
    known = {t.key for t in topics}
    for topic in topics:
        children.setdefault(topic.parent if topic.parent in known else None, []).append(topic)
    out: list[str] = []

    def walk(parent: str | None, depth: int) -> None:
        for topic in children.get(parent, []):
            parts = [topic.label or NO_LABEL, _escape(topic.name),
                     f"due={format_moment(topic.due_at) if topic.due_at else ''}"]
            if topic.label is not None or topic.created or topic.deleted:
                parts.append(f"created={format_moment(topic.created) if topic.created else ''}")
                parts.append(f"deleted={format_moment(topic.deleted) if topic.deleted else ''}")
            out.append("  " * depth + "- " + " | ".join(parts))
            walk(topic.key, depth + 1)

    walk(None, 0)
    return "".join(line + newline for line in out)


def parse_topics(text: str, file: str | None = "topics.md") -> list[TopicLine]:
    newline = "\r\n" if "\r\n" in text else "\n"
    result: list[TopicLine] = []
    stack: list[str] = []  # keys of the open ancestors
    for number, raw in enumerate(text.split(newline), start=1):
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        body = raw.lstrip(" ")
        if indent % 2 or not body.startswith("- "):
            raise NoteFormatError("a topic is '- LABEL | name | due=…', indented by two spaces per level", number, file)
        depth = indent // 2
        if depth > len(stack):
            raise NoteFormatError("a topic is indented deeper than its parent allows", number, file)
        del stack[depth:]
        cells = _cells(body[2:])
        if len(cells) < 2:
            raise NoteFormatError("a topic has a label and a name", number, file)
        label = None if cells[0] == NO_LABEL else cells[0]
        if label is not None and not _LABEL.fullmatch(label):
            raise NoteFormatError(f"not a label: {cells[0]!r}", number, file)
        options = {}
        for cell in cells[2:]:
            key, eq, value = cell.partition("=")
            if not eq or key not in ("due", "created", "deleted"):
                raise NoteFormatError(f"unknown topic field: {cell!r}", number, file)
            options[key] = _optional_moment(value, number, file)
        topic = TopicLine(label, _unescape(cells[1]), stack[-1] if stack else None, options.get("due"),
                          options.get("created"), options.get("deleted"))
        result.append(topic)
        stack.append(topic.key)
    return result


# --- counters ---

_COUNTER_KINDS = ("NOTE", "TOPIC")


def render_counters(counters: Mapping[str, int], newline: str = "\n") -> str:
    """`NOTE: 15` and `TOPIC: 7`: the highest number ever given per kind (lower case kinds as the store names them)."""
    return "".join(f"{kind}: {counters[kind.lower()]}{newline}" for kind in _COUNTER_KINDS if kind.lower() in counters)


def parse_counters(text: str, file: str | None = "counters.md") -> dict[str, int]:
    counters: dict[str, int] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        kind, colon, value = line.partition(":")
        if not colon or kind.strip() not in _COUNTER_KINDS or not value.strip().isdigit():
            raise NoteFormatError(f"a counter is 'NOTE: <number>' or 'TOPIC: <number>': {line!r}", number, file)
        counters[kind.strip().lower()] = int(value)
    return counters


__all__ = [
    "NEW_TOPIC",
    "NO_LABEL",
    "ParsedLink",
    "ParsedNote",
    "ParsedTarget",
    "ParsedTrigger",
    "TopicLine",
    "format_moment",
    "moment_text",
    "parse_counters",
    "parse_note",
    "parse_topics",
    "render_counters",
    "render_note",
    "render_parsed",
    "render_topics",
    "to_lines",
    "trigger_line",
    "to_parsed",
]

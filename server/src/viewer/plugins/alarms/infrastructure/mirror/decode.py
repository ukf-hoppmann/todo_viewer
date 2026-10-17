"""`alarms.md` → Einträge."""

from __future__ import annotations

from typing import NoReturn

from viewer.core.domain.files import FileSet
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.alarms.domain.model import STATUSES
from viewer.plugins.alarms.infrastructure.mirror.syntax import (
    ALARMS_FILE,
    DAY,
    FIELD,
    FIELD_ORDER,
    HEADER,
    KIND_ALARM,
    LABEL,
    PLACEHOLDER,
    SECTION,
    clean,
    format_line,
    parse_time,
    target_token,
)


def _fail(code: str, message: str, line: int) -> NoReturn:
    raise MirrorFormatError(code, message, file=ALARMS_FILE, line=line)


def decode(files: FileSet, project: str) -> list[MirrorEntry]:
    file = files.files.get(ALARMS_FILE)
    if file is None:
        return []
    lines = file.text.split("\n")
    line, version = format_line(lines)
    if version != 2:
        _fail(
            "format_version",
            "Die Kennung fehlt" if version is None else f"Die Kennung nennt Version {version}, gebraucht wird 2",
            line,
        )
    entries: list[MirrorEntry] = []
    uids: set[str] = set()
    idents: set[str] = set()
    start = next((i for i, text in enumerate(lines) if SECTION.match(text)), -1) + 1
    current: tuple[str, str, int, dict[str, tuple[str, int]]] | None = None
    blocks: list[tuple[str, str, int, dict[str, tuple[str, int]]]] = []
    for index in range(start, len(lines)):
        raw = lines[index]
        header = HEADER.match(raw)
        if header:
            current = (header.group(1), header.group(2).strip(), index + 1, {})
            blocks.append(current)
            continue
        field = FIELD.match(raw)
        if field and current is not None:
            current[3][field.group(1).strip()] = (field.group(2).strip(), index + 1)
            continue
        if raw.strip() and not raw.startswith(" ") and current is not None and not raw.startswith("- "):
            current = None
    for ident, text, line, fields in blocks:
        entry = _entry(ident, text, line, fields, project)
        if entry.uid is not None:
            if entry.uid in uids:
                _fail("duplicate_uid", f"`{ident}` trägt eine Uid, die es schon gibt", line)
            uids.add(entry.uid)
        if ident in idents:
            _fail("duplicate_label", f"`{ident}` kommt zweimal vor", line)
        idents.add(ident)
        entries.append(entry)
    return entries


def _entry(ident: str, text: str, line: int, fields: dict[str, tuple[str, int]], project: str) -> MirrorEntry:
    is_new = ident.startswith("NEW-")
    if is_new and not PLACEHOLDER.match(ident):
        _fail("invalid_placeholder", "Der Kurzname besteht aus `a-z`, `0-9` und `-`", line)
    if not is_new and not LABEL.match(ident):
        _fail("invalid_value", f"`{ident}` ist kein Label eines Weckers (`ALARM-001`) und kein Platzhalter", line)
    for name, (_, field_line) in fields.items():
        if name not in FIELD_ORDER:
            _fail("unknown_field", f"Unbekanntes Feld `{name}`", field_line)

    def value(name: str) -> str:
        return clean(fields[name][0]) if name in fields else ""

    def line_of(name: str) -> int:
        return fields[name][1] if name in fields else line

    for name in ("At", "Status"):
        if not value(name):
            _fail("missing_field", f"`{ident}` ohne `{name}`", line)
    uid = value("Uid") or None
    if not is_new and uid is None:
        _fail("missing_field", f"`{ident}` ohne `Uid`", line)
    if is_new and uid is not None:
        _fail("invalid_value", "Ein neuer Wecker hat keine `Uid`", line_of("Uid"))
    status = value("Status")
    if status not in STATUSES:
        _fail("invalid_value", f"Status `{status}` gibt es nicht", line_of("Status"))

    def moment(name: str) -> str | None:
        if not value(name):
            return None
        try:
            return parse_time(value(name))
        except ValueError:
            _fail("invalid_value", f"{name} `{value(name)}` ist kein Zeitpunkt", line_of(name))

    snoozed = moment("Snoozed until")
    if status == "Snoozed" and snoozed is None:
        _fail("missing_field", f"`{ident}` ist zurückgestellt, aber ohne `Snoozed until`", line)
    if status != "Snoozed" and snoozed is not None:
        _fail("invalid_value", "`Snoozed until` gehört nur zu `Snoozed`", line_of("Snoozed until"))
    days: dict[str, str | None] = {}
    for name in ("Created", "Deleted"):
        day = value(name) or None
        if day is not None and not DAY.match(day):
            _fail("invalid_value", f"{name} `{day}` ist kein Tag (JJJJ-MM-TT)", line_of(name))
        days[name] = day
    refs: dict[str, tuple[str, ...]] = {}
    source_lines: dict[str, int] = {}
    token = target_token(fields["Target"][0], project) if "Target" in fields else None
    if token is not None:
        refs["target"] = (token,)
        source_lines["target"] = line_of("Target")
    return MirrorEntry(
        KIND_ALARM,
        None if is_new else ident,
        {
            "text": text,
            "at": moment("At"),
            "status": status,
            "snoozed_until": snoozed,
            "deleted": days["Deleted"],
        },
        refs,
        uid,
        ident if is_new else None,
        source=(ALARMS_FILE, line),
        source_lines=source_lines,
        extra={"created": days["Created"]},
    )

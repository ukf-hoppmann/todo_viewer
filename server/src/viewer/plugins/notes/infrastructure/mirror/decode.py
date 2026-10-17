"""Dateien → Einträge für `notes/`: Notes, Dokumente und `topics.md` (Format Version 2)."""

from __future__ import annotations

from typing import Any, NoReturn

from viewer.core.domain.files import FileSet
from viewer.core.domain.sync import MirrorEntry, MirrorFormatError
from viewer.plugins.notes.infrastructure.mirror.syntax import (
    DOCUMENT_FILE,
    FILE_STATUSES,
    HEADER_KEYS,
    KIND_DOCUMENT,
    KIND_NOTE,
    KIND_TOPIC,
    LINK,
    NOTE_FILE,
    NOTE_PLACEHOLDER,
    SECTIONS,
    TOPIC_KEYS,
    TOPIC_ROW,
    TOPICS_FILE,
    TRIGGER,
    normalize_target,
    parse_time,
    split_row,
    unescape,
)


def _fail(code: str, message: str, path: str, line: int) -> NoReturn:
    raise MirrorFormatError(code, message, file=path, line=line)


def decode(files: FileSet, project: str) -> list[MirrorEntry]:
    """Alle Einträge: erst die Topics, dann die Notes, dann ihre Dokumente."""
    topics = _topics(files)
    notes = _notes(files, project)
    documents = _documents(files, notes)
    _check_unique(topics, notes)
    return [*topics, *notes, *documents]


# --- topics.md -----------------------------------------------------------------------------------------------------


def parse_topics(text: str, path: str = TOPICS_FILE) -> list[MirrorEntry]:
    entries: list[MirrorEntry] = []
    stack: list[str] = []  # Verweis (Label oder Platzhalter) des Topics je Ebene
    for index, raw in enumerate(text.split("\n")):
        if not raw.strip():
            continue
        line = index + 1
        match = TOPIC_ROW.match(raw)
        if match is None:
            _fail("invalid_value", "Keine Topic-Zeile (`- TOPIC-001 | Name | …`)", path, line)
        indent = len(match.group("indent"))
        if indent % 2:
            _fail("invalid_value", "Die Einrückung ist ein Vielfaches von zwei Leerzeichen", path, line)
        level = indent // 2
        if level > len(stack):
            _fail("invalid_value", "Die Einrückung springt über eine Ebene", path, line)
        parts = split_row(match.group("rest"))
        name = unescape(parts[0])
        if not name.strip():
            _fail("missing_field", "Das Topic hat keinen Namen", path, line)
        values: dict[str, str] = {}
        for part in parts[1:]:
            key, separator, value = part.partition("=")
            if not separator or key not in TOPIC_KEYS:
                _fail("unknown_field", f"Unbekannte Angabe `{part}`", path, line)
            values[key] = value
        ident = match.group("ident")
        is_new = ident == "NEW"
        if not is_new and not values.get("uid"):
            _fail("missing_field", f"`{ident}` ohne `uid`", path, line)
        times: dict[str, str | None] = {}
        for key in ("due", "created", "archived", "deleted"):
            try:
                times[key] = parse_time(values[key]) if values.get(key) else None
            except ValueError:
                _fail("invalid_value", f"`{key}={values[key]}` ist kein Zeitpunkt", path, line)
        token = f"new:{name}" if is_new else ident
        refs = {"parent": (stack[level - 1],)} if level > 0 else {}
        fields = {
            "name": name,
            "due_at": times["due"],
            "archived_at": times["archived"],
            "deleted_at": times["deleted"],
        }
        entries.append(
            MirrorEntry(
                KIND_TOPIC,
                None if is_new else ident,
                fields,
                refs,
                None if is_new else values["uid"],
                token if is_new else None,
                source=(path, line),
                extra={"created": times["created"]},
            )
        )
        del stack[level:]
        stack.append(token)
    return entries


def _topics(files: FileSet) -> list[MirrorEntry]:
    entry = files.files.get(TOPICS_FILE)
    return parse_topics(entry.text) if entry is not None else []


# --- Notes ---------------------------------------------------------------------------------------------------------


def _notes(files: FileSet, project: str) -> list[MirrorEntry]:
    notes: list[MirrorEntry] = []
    for path in sorted(files.files):
        name = path.rsplit("/", 1)[-1]
        match = NOTE_FILE.match(name)
        if match is None or path != f"notes/{name}":
            continue
        notes.append(_note(path, files.files[path].text, match.group("stem"), project))
    return notes


def _note(path: str, text: str, stem: str, project: str) -> MirrorEntry:
    lines = text.split("\n")
    is_new = stem.startswith("new-")
    expected = "# NEW" if is_new else f"# {stem}"
    if lines[0].rstrip() != expected:
        shown = lines[0].strip() or "(leer)"
        _fail("file_label_mismatch", f"Datei `{path.rsplit('/', 1)[-1]}` enthält `{shown.removeprefix('# ')}`", path, 1)
    if is_new and not NOTE_PLACEHOLDER.match(stem):
        _fail("invalid_placeholder", "Der Kurzname besteht aus `a-z`, `0-9` und `-`", path, 1)

    values: dict[str, tuple[str, int]] = {}
    triggers: list[dict[str, Any]] = []
    trigger_targets: list[str] = []
    links: dict[str, list[str]] = {"reference": [], "origin": []}
    source_lines: dict[str, int] = {}
    section: str | None = None
    index = 1
    while index < len(lines) and lines[index].strip():
        raw, line = lines[index], index + 1
        index += 1
        if raw.startswith("- "):
            if section == "Triggers":
                _trigger(raw, path, line, project, triggers, trigger_targets, source_lines)
            elif section == "Links":
                link = LINK.match(raw)
                if link is None:
                    _fail("invalid_value", f"Keine gültige Verknüpfung: `{raw}`", path, line)
                token = normalize_target(link.group("target"), project)
                links[link.group("role")].append(token)
                source_lines[f"{link.group('role')}:{token}"] = line
            else:
                _fail("invalid_value", f"Zeile ohne Abschnitt: `{raw}`", path, line)
            continue
        key, separator, value = raw.partition(":")
        key = key.strip()
        if not separator:
            _fail("invalid_value", f"Keine Kopfzeile: `{raw}`", path, line)
        if key in SECTIONS:
            if value.strip():
                _fail("invalid_value", f"`{key}:` steht allein in der Zeile", path, line)
            section = key
            continue
        if key not in HEADER_KEYS:
            _fail("unknown_field", f"Unbekannte Kopfzeile `{key}`", path, line)
        if key in values:
            _fail("invalid_value", f"`{key}` steht zweimal im Kopf", path, line)
        section = None
        values[key] = (value.strip(), line)

    def get(key: str) -> str:
        return values.get(key, ("", 1))[0]

    def line_of(key: str) -> int:
        return values.get(key, ("", 1))[1]

    for key in ("Summary", "Status"):
        if not get(key):
            _fail("missing_field", f"`{stem}` ohne `{key}`", path, 1)
    uid = get("Uid") or None
    if not is_new and uid is None:
        _fail("missing_field", f"`{stem}` ohne `Uid`", path, 1)
    if is_new and uid is not None:
        _fail("invalid_value", "Eine neue Note hat keine `Uid`", path, line_of("Uid"))
    status = get("Status")
    if status not in FILE_STATUSES:
        reason = "abgeleitet und steht nie in einer Datei" if status == "due" else "gibt es nicht"
        _fail("invalid_value", f"Status `{status}` {reason}", path, line_of("Status"))
    mode = get("Mode") or "any"
    if mode not in ("any", "all"):
        _fail("invalid_value", f"Mode `{mode}` ist `any` oder `all`", path, line_of("Mode"))
    archived = get("Archived") or "false"
    if archived not in ("true", "false"):
        _fail("invalid_value", f"Archived `{archived}` ist `true` oder `false`", path, line_of("Archived"))

    def moment(key: str) -> str | None:
        if not get(key):
            return None
        try:
            return parse_time(get(key))
        except ValueError:
            _fail("invalid_value", f"{key} `{get(key)}` ist kein Zeitpunkt", path, line_of(key))

    refs: dict[str, tuple[str, ...]] = {}
    if get("Topic"):
        refs["topic"] = (get("Topic"),)
        source_lines["topic"] = line_of("Topic")
    for role in ("reference", "origin"):
        if links[role]:
            refs[role] = tuple(sorted(links[role]))
    if trigger_targets:
        refs["trigger_targets"] = tuple(trigger_targets)
    body = "\n".join(lines[index + 1 :]).rstrip("\n") if index < len(lines) else ""
    fields = {
        "summary": get("Summary"),
        "status": status,
        "review_at": moment("Review"),
        "mode": mode,
        "archived": archived == "true",
        "deleted_at": moment("Deleted"),
        "body": body,
        "triggers": triggers,
    }
    return MirrorEntry(
        KIND_NOTE,
        None if is_new else stem,
        fields,
        refs,
        uid,
        stem if is_new else None,
        source=(path, 1),
        source_lines=source_lines,
        extra={"created": moment("Created"), "updated": moment("Updated")},
    )


def _trigger(
    raw: str,
    path: str,
    line: int,
    project: str,
    triggers: list[dict[str, Any]],
    targets: list[str],
    source_lines: dict[str, int],
) -> None:
    if raw.strip() == "- topic_due":
        triggers.append({"kind": "topic_date", "status": None, "fired_at": None, "already_met": False})
        return
    match = TRIGGER.match(raw)
    if match is None:
        kind = raw[2:].split(" ", 1)[0]
        if kind in ("time", "event", "topic_due") or not kind:
            if kind == "time":
                _fail("unknown_trigger", "Zeit-Auslöser gibt es nicht mehr (sie sind Wecker)", path, line)
            _fail("invalid_value", f"Kein gültiger Auslöser: `{raw}`", path, line)
        _fail("unknown_trigger", f"Auslöser `{kind}` gibt es nicht (`event`, `topic_due`)", path, line)
    fired: str | None = None
    already_met = False
    for flag in match.group("flags").split("["):
        flag = flag.strip().rstrip("]")
        if not flag:
            continue
        if flag == "already_met":
            already_met = True
        elif flag.startswith("fired "):
            try:
                fired = parse_time(flag[len("fired ") :].strip())
            except ValueError:
                _fail("invalid_value", f"`[{flag}]` ist kein Zeitpunkt", path, line)
        else:
            _fail("invalid_value", f"Unbekanntes Zeichen `[{flag}]`", path, line)
    token = normalize_target(match.group("target"), project)
    targets.append(token)
    source_lines[f"trigger_targets:{token}"] = line
    triggers.append({"kind": "event", "status": match.group("status"), "fired_at": fired, "already_met": already_met})


# --- Dokumente -----------------------------------------------------------------------------------------------------


def _documents(files: FileSet, notes: list[MirrorEntry]) -> list[MirrorEntry]:
    by_stem = {str(n.label or n.placeholder): n for n in notes}
    documents: list[MirrorEntry] = []
    for path in sorted(files.files):
        name = path.rsplit("/", 1)[-1]
        match = DOCUMENT_FILE.match(name)
        if match is None or path != f"notes/{name}":
            continue
        note = by_stem.get(match.group("stem"))
        if note is None:
            continue  # ein Dokument ohne Note: nichts zuzuordnen
        suffix = match.group("suffix")
        fields = {"content": files.files[path].text, "kind": "notes" if suffix == "notes" else "spec"}
        refs = {"note": (match.group("stem"),)}
        if note.uid is not None:
            documents.append(MirrorEntry(KIND_DOCUMENT, name, fields, refs, f"{note.uid}/{suffix}", source=(path, 1)))
        else:
            documents.append(
                MirrorEntry(
                    KIND_DOCUMENT, None, fields, refs, None, f"{match.group('stem')}/{suffix}", source=(path, 1)
                )
            )
    return documents


# --- Eindeutigkeit -------------------------------------------------------------------------------------------------


def _check_unique(topics: list[MirrorEntry], notes: list[MirrorEntry]) -> None:
    uids: dict[str, MirrorEntry] = {}
    labels: dict[str, MirrorEntry] = {}
    placeholders: dict[str, MirrorEntry] = {}
    for entry in [*topics, *notes]:
        path, line = entry.source or (TOPICS_FILE, 1)
        shown = str(entry.label or entry.placeholder)
        if entry.uid is not None:
            if entry.uid in uids:
                other = uids[entry.uid]
                _fail("duplicate_uid", f"`{shown}` trägt die Uid von `{other.label}`", path, line)
            uids[entry.uid] = entry
        if entry.label is not None:
            if entry.label in labels:
                _fail("duplicate_label", f"`{entry.label}` kommt zweimal vor", path, line)
            labels[entry.label] = entry
        else:
            key = f"{entry.kind}:{entry.placeholder}"
            if key in placeholders:
                _fail("invalid_placeholder", f"Der Platzhalter `{entry.placeholder}` kommt zweimal vor", path, line)
            placeholders[key] = entry

"""Format check of the notes folder kept as files (todo module, backend files).

The format is the ToDo-Viewer's file format version 2; the rules and the error codes follow the viewer's decoder
(`plugins/notes/infrastructure/mirror/decode.py` and `syntax.py`), which aborts the whole sync on the first error. This
reports the first error of each file plus the errors across files, so a typo is found when it is written. The examples
the two sides share are in tests/fixtures/notes-format. Pure functions; nothing is written.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

NOTES_DIR = "notes"
TOPICS_FILE = "topics.md"
COUNTERS_FILE = "counters.md"

# NOTE-001.md and new-<name>.md; documents are NOTE-001_notes.md, NOTE-001_spec.md, new-<name>_spec_<topic>.md.
_NOTE_FILE = re.compile(r"^(?P<stem>NOTE-[0-9]+|new-[A-Za-z0-9-]+)\.md$")
_DOCUMENT_FILE = re.compile(r"^(?P<stem>NOTE-[0-9]+|new-[A-Za-z0-9-]+)_(?P<suffix>notes|spec(?:_[A-Za-z0-9-]+)?)\.md$")
_PLACEHOLDER = re.compile(r"^new-[a-z0-9]+(-[a-z0-9]+)*$")
HEADER_KEYS = ("Uid", "Summary", "Status", "Topic", "Review", "Mode", "Created", "Updated", "Archived", "Deleted")
SECTIONS = ("Triggers", "Links")
# `due` is derived and never stored in a file.
FILE_STATUSES = ("waiting", "snoozed", "done", "dropped", "promoted")
ITEM_STATUSES = ("In progress", "Awaiting confirmation", "Completed", "Rejected")
_TRIGGER = re.compile(
    r"^- event (?P<target>.+?) (?P<status>" + "|".join(ITEM_STATUSES) + r")(?P<flags>(?: \[[^\]]*\])*)$"
)
_LINK = re.compile(r"^- (?P<role>reference|origin) (?P<target>.+)$")
_TOPIC_ROW = re.compile(r"^(?P<indent> *)- (?P<ident>TOPIC-[0-9]+|NEW) \| (?P<rest>.*)$")
TOPIC_KEYS = ("uid", "due", "created", "archived", "deleted")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z")
_MARKER_START = re.compile(r"^<{7}(\s|$)", re.MULTILINE)
_MARKER_END = re.compile(r"^>{7}(\s|$)", re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    """An error (the viewer would refuse the sync) or a notice. `file` is relative to the backlog folder."""

    file: str
    line: int
    code: str
    message: str
    error: bool = True

    def __str__(self) -> str:
        return f"{self.file}:{self.line}: {self.code}: {self.message}"


class _Invalid(Exception):
    def __init__(self, code: str, message: str, line: int) -> None:
        super().__init__(message)
        self.code, self.message, self.line = code, message, line


@dataclass
class _Entry:
    """What the cross-file checks need of a note or a topic."""

    kind: str
    label: str | None
    placeholder: str | None
    uid: str | None
    file: str
    line: int


def check_notes_folder(notes_dir: Path) -> list[Finding]:
    """Errors (sorted by file) followed by notices (sorted by file). A missing folder has no findings."""
    if not notes_dir.is_dir():
        return []
    findings: list[Finding] = []
    texts: dict[str, str] = {}
    for path in sorted(notes_dir.glob("*.md")):
        if path.is_file():
            _read(path, texts, findings)
    for name, text in texts.items():
        marker = _MARKER_START.search(text)
        if marker and _MARKER_END.search(text):
            line = text.count("\n", 0, marker.start()) + 1
            findings.append(Finding(_shown(name), line, "merge_markers", "conflict markers from a Git merge"))
    marked = {f.file for f in findings if f.code == "merge_markers"}
    entries: list[_Entry] = []
    if TOPICS_FILE in texts and _shown(TOPICS_FILE) not in marked:
        entries += _guard(findings, TOPICS_FILE, lambda: _topics(texts[TOPICS_FILE]))
    notes = sorted(n for n in texts if _NOTE_FILE.match(n) and _shown(n) not in marked)
    for name in notes:
        entries += _guard(findings, name, lambda name=name: [_note(name, texts[name])])
    findings += _duplicates(entries)
    findings += _notices(texts, notes)
    return sorted(findings, key=lambda f: (not f.error, f.file, f.line))


def _shown(name: str) -> str:
    return f"{NOTES_DIR}/{name}"


def _read(path: Path, texts: dict[str, str], findings: list[Finding]) -> None:
    try:
        # Strict UTF-8 and LF, like the viewer reads the folder.
        texts[path.name] = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeDecodeError):
        findings.append(Finding(_shown(path.name), 1, "unreadable", "the file cannot be read as UTF-8 text"))


def _guard(findings: list[Finding], name: str, parse) -> list[_Entry]:
    try:
        return parse()
    except _Invalid as error:
        findings.append(Finding(_shown(name), error.line, error.code, error.message))
        return []


def _valid_time(text: str) -> bool:
    if not _TIME.fullmatch(text):
        return False
    try:
        datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError:
        return False
    return True


# --- topics.md -----------------------------------------------------------------------------------------------------


def _split_row(rest: str) -> list[str]:
    """Splits at the `|` that are not escaped with a backslash; the parts are trimmed."""
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


def _topics(text: str) -> list[_Entry]:
    entries: list[_Entry] = []
    depth = 0  # number of topics on the path to the previous row
    for index, raw in enumerate(text.split("\n")):
        if not raw.strip():
            continue
        line = index + 1
        match = _TOPIC_ROW.match(raw)
        if match is None:
            raise _Invalid("invalid_value", "not a topic row (`- TOPIC-001 | Name | …`)", line)
        indent = len(match["indent"])
        if indent % 2:
            raise _Invalid("invalid_value", "the indentation is a multiple of two spaces", line)
        level = indent // 2
        if level > depth:
            raise _Invalid("invalid_value", "the indentation jumps over a level", line)
        name, *parts = _split_row(match["rest"])
        if not name.strip():
            raise _Invalid("missing_field", "the topic has no name", line)
        values: dict[str, str] = {}
        for part in parts:
            key, separator, value = part.partition("=")
            if not separator or key not in TOPIC_KEYS:
                raise _Invalid("unknown_field", f"unknown specification `{part}`", line)
            values[key] = value
        ident = match["ident"]
        is_new = ident == "NEW"
        if not is_new and not values.get("uid"):
            raise _Invalid("missing_field", f"`{ident}` has no `uid`", line)
        for key in ("due", "created", "archived", "deleted"):
            if values.get(key) and not _valid_time(values[key]):
                raise _Invalid("invalid_value", f"`{key}={values[key]}` is not a time (UTC with Z)", line)
        depth = level + 1
        entries.append(
            _Entry("topic", None if is_new else ident, f"new:{name}" if is_new else None, values.get("uid") or None, _shown(TOPICS_FILE), line)
        )
    return entries


# --- notes ---------------------------------------------------------------------------------------------------------


def _note(name: str, text: str) -> _Entry:
    stem = _NOTE_FILE.match(name)["stem"]
    lines = text.split("\n")
    is_new = stem.startswith("new-")
    expected = "# NEW" if is_new else f"# {stem}"
    if lines[0].rstrip() != expected:
        shown = lines[0].strip().removeprefix("# ") or "(empty)"
        raise _Invalid("file_label_mismatch", f"file `{name}` contains `{shown}`", 1)
    if is_new and not _PLACEHOLDER.match(stem):
        raise _Invalid("invalid_placeholder", "the short name consists of `a-z`, `0-9` and `-`", 1)
    values: dict[str, tuple[str, int]] = {}
    section: str | None = None
    index = 1
    while index < len(lines) and lines[index].strip():
        raw, line = lines[index], index + 1
        index += 1
        if raw.startswith("- "):
            if section == "Triggers":
                _trigger(raw, line)
            elif section == "Links":
                if _LINK.match(raw) is None:
                    raise _Invalid("invalid_value", f"not a valid link: `{raw}`", line)
            else:
                raise _Invalid("invalid_value", f"list line without a section (`Triggers:`, `Links:`): `{raw}`", line)
            continue
        key, separator, value = raw.partition(":")
        key = key.strip()
        if not separator:
            raise _Invalid("invalid_value", f"not a header line: `{raw}`", line)
        if key in SECTIONS:
            if value.strip():
                raise _Invalid("invalid_value", f"`{key}:` stands alone on its line", line)
            section = key
            continue
        if key not in HEADER_KEYS:
            raise _Invalid("unknown_field", f"unknown header line `{key}`", line)
        if key in values:
            raise _Invalid("invalid_value", f"`{key}` appears twice in the head", line)
        section = None
        values[key] = (value.strip(), line)

    def get(key: str) -> str:
        return values.get(key, ("", 1))[0]

    def line_of(key: str) -> int:
        return values.get(key, ("", 1))[1]

    for key in ("Summary", "Status"):
        if not get(key):
            raise _Invalid("missing_field", f"`{stem}` has no `{key}`", 1)
    uid = get("Uid") or None
    if not is_new and uid is None:
        raise _Invalid("missing_field", f"`{stem}` has no `Uid`", 1)
    if is_new and uid is not None:
        raise _Invalid("invalid_value", "a new note has no `Uid`", line_of("Uid"))
    status = get("Status")
    if status not in FILE_STATUSES:
        reason = "is derived and never stored in a file" if status == "due" else "does not exist"
        raise _Invalid("invalid_value", f"Status `{status}` {reason}", line_of("Status"))
    if (get("Mode") or "any") not in ("any", "all"):
        raise _Invalid("invalid_value", f"Mode `{get('Mode')}` is `any` or `all`", line_of("Mode"))
    if (get("Archived") or "false") not in ("true", "false"):
        raise _Invalid("invalid_value", f"Archived `{get('Archived')}` is `true` or `false`", line_of("Archived"))
    for key in ("Review", "Deleted", "Created", "Updated"):
        if get(key) and not _valid_time(get(key)):
            raise _Invalid("invalid_value", f"{key} `{get(key)}` is not a time (UTC with Z)", line_of(key))
    return _Entry("note", None if is_new else stem, stem if is_new else None, uid, _shown(name), 1)


def _trigger(raw: str, line: int) -> None:
    if raw.strip() == "- topic_due":
        return
    match = _TRIGGER.match(raw)
    if match is None:
        kind = raw[2:].split(" ", 1)[0]
        if kind == "time":
            raise _Invalid("unknown_trigger", "time triggers do not exist any more (they are alarms)", line)
        if kind in ("event", "topic_due") or not kind:
            raise _Invalid("invalid_value", f"not a valid trigger: `{raw}`", line)
        raise _Invalid("unknown_trigger", f"trigger `{kind}` does not exist (`event`, `topic_due`)", line)
    for flag in match["flags"].split("["):
        flag = flag.strip().rstrip("]")
        if not flag or flag == "already_met":
            continue
        if not flag.startswith("fired "):
            raise _Invalid("invalid_value", f"unknown mark `[{flag}]`", line)
        if not _valid_time(flag[len("fired ") :].strip()):
            raise _Invalid("invalid_value", f"`[{flag}]` is not a time (UTC with Z)", line)


# --- across files --------------------------------------------------------------------------------------------------


def _duplicates(entries: list[_Entry]) -> list[Finding]:
    findings: list[Finding] = []
    uids: dict[str, _Entry] = {}
    labels: set[str] = set()
    placeholders: set[str] = set()
    # Topics come first, like in the viewer: the later entry is the one reported.
    for entry in sorted(entries, key=lambda e: e.kind != "topic"):
        shown = entry.label or entry.placeholder or "?"
        file = entry.file
        if entry.uid is not None:
            if entry.uid in uids:
                other = uids[entry.uid].label or uids[entry.uid].placeholder
                findings.append(Finding(file, entry.line, "duplicate_uid", f"`{shown}` carries the uid of `{other}`"))
            else:
                uids[entry.uid] = entry
        if entry.label is not None:
            if entry.label in labels:
                findings.append(Finding(file, entry.line, "duplicate_label", f"`{entry.label}` appears twice"))
            labels.add(entry.label)
        else:
            key = f"{entry.kind}:{entry.placeholder}"
            if key in placeholders:
                findings.append(
                    Finding(file, entry.line, "invalid_placeholder", f"the placeholder `{entry.placeholder}` appears twice")
                )
            placeholders.add(key)
    return findings


def _notices(texts: dict[str, str], notes: list[str]) -> list[Finding]:
    """Files the viewer does not read, and documents that belong to no note. The viewer ignores both silently."""
    stems = {_NOTE_FILE.match(n)["stem"] for n in texts if _NOTE_FILE.match(n)}
    findings: list[Finding] = []
    for name in sorted(texts):
        if name in (TOPICS_FILE, COUNTERS_FILE) or name.startswith(".") or _NOTE_FILE.match(name):
            continue
        document = _DOCUMENT_FILE.match(name)
        if document is None:
            findings.append(
                Finding(_shown(name), 1, "ignored_file", "the viewer does not read this file (NOTE-<n>.md, new-<name>.md, documents, topics.md)", False)
            )
        elif document["stem"] not in stems:
            findings.append(
                Finding(_shown(name), 1, "document_without_note", f"no note `{document['stem']}.md`; the viewer ignores the document", False)
            )
    return findings

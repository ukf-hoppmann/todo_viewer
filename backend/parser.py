"""Parser for TODO.md / backlog files.

Supports two formats:
1. Structured backlog format ("backlog format version N", e.g.
   "Claude_Harness backlog format version 1") - entries like:
     - `STORY-001` **Title**
       - Type: Story.
       - Parent: `EPIC-001`.
       - Required for parent: Yes.
       - Status: Open.
       - Created: 2026-09-23.
       - Area: ...
       - Priority: Important.
       - Dependencies: `TASK-001`, `TASK-002`.
       - Goal: ... (continuation lines indented by four spaces)
       - Completion criteria: ...
       - Summary / Notes / Spec / Resolution: optional
       - <any other field>: ...
   A backlog folder holds `TODO.md` (active items) and `archive.md`
   (Completed/Rejected items); both use this syntax.
2. Fallback: plain nested markdown checklists ("- [ ] Task", "- [x] Done"),
   using indentation to build a parent/child tree.
"""
from __future__ import annotations

import re
from pathlib import Path

from todo_viewer.domain.editing import EditPlanner, Field
from todo_viewer.domain.errors import EntryMovedError, UnknownFormatError
from todo_viewer.domain.item import Item, ItemFormat, Location

ENTRY_HEADER_RE = re.compile(r"^- `([A-Za-z0-9_.\-]+)`\s+\*\*(.+?)\*\*\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^ {2}- ([A-Za-z][A-Za-z ]*?):\s?(.*)$")
BACKTICK_ID_RE = re.compile(r"`([A-Za-z0-9_.\-]+)`")
BACKTICK_ANY_RE = re.compile(r"`([^`]+)`")
CHECKBOX_RE = re.compile(r"^(\s*)-\s\[( |x|X)\]\s+(.*)$")
WORK_ITEMS_HEADER_RE = re.compile(r"^## Work items\s*$", re.MULTILINE)
NO_ENTRIES_LINE = "No entries."
# Matches any structured backlog format version ("... backlog format version 2",
# "Claude_Harness backlog format version 1", ...); the entry syntax is identical.
BACKLOG_V2_MARKER_RE = re.compile(r"backlog\s+format\s+version\s+\d+", re.IGNORECASE)

# Older backlogs used German priority names; the keys are English now.
LEGACY_PRIORITIES = {"dringend": "Urgent", "wichtig": "Important", "perspektivisch": "Prospective"}

TODO_FILE = "TODO.md"
ARCHIVE_FILE = "archive.md"


def _slug(key: str) -> str:
    return key.strip().lower().replace(" ", "_")


def _clean(value: str) -> str:
    """Strips the trailing period every field value carries in the format."""
    value = value.strip()
    return value[:-1].rstrip() if value.endswith(".") else value


def _extract_ids(value: str) -> list[str]:
    return BACKTICK_ID_RE.findall(value)


def _extract_paths(value: str) -> list[str]:
    paths = BACKTICK_ANY_RE.findall(value)
    if paths:
        return paths
    return [p.strip() for p in _clean(value).split(",") if p.strip() and p.strip() != "None"]


def normalize_priority(value: str | None) -> str | None:
    if not value:
        return value
    return LEGACY_PRIORITIES.get(value.lower(), value)


def _yes_no(value: str) -> bool | None:
    v = _clean(value).lower()
    if v == "yes":
        return True
    if v == "no":
        return False
    return None


def item_to_dict(item: Item) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "source_file": item.source_file,
        "project": item.project,
        "line": item.line,
        "format": item.format.value,
        "type": item.item_type,
        "status": item.status,
        "parent": item.parent,
        "required_for_parent": item.required_for_parent,
        "dependencies": item.dependencies,
        "created": item.created,
        "area": item.area,
        "priority": item.priority,
        "goal": item.goal,
        "completion_criteria": item.completion_criteria,
        "summary": item.summary,
        "resolution": item.resolution,
        "notes": item.notes,
        "spec": item.spec,
        "extra_fields": item.extra_fields,
    }


def _apply_fields(item: Item, fields: list[tuple[str, str]]) -> None:
    for key_raw, value in fields:
        key = _slug(key_raw)
        if key == "type":
            item.item_type = _clean(value)
        elif key == "status":
            item.status = _clean(value)
        elif key == "parent":
            ids = _extract_ids(value)
            item.parent = ids[0] if ids else None
        elif key == "required_for_parent":
            item.required_for_parent = _yes_no(value)
        elif key == "dependencies":
            item.dependencies = _extract_ids(value)
        elif key == "created":
            item.created = _clean(value)
        elif key == "area":
            item.area = _clean(value)
        elif key == "priority":
            item.priority = normalize_priority(_clean(value))
        elif key == "goal":
            item.goal = value.strip()
        elif key == "completion_criteria":
            item.completion_criteria = value.strip()
        elif key == "summary":
            item.summary = value.strip()
        elif key == "resolution":
            item.resolution = value.strip()
        elif key == "notes":
            item.notes = _extract_paths(value)
        elif key == "spec":
            item.spec = _extract_paths(value)
        else:
            item.extra_fields[key_raw.strip()] = value.strip()


def parse_backlog_v2(text: str, source_file: str, project: str) -> list[Item]:
    header_match = WORK_ITEMS_HEADER_RE.search(text)
    start_offset = 0
    if header_match:
        start_offset = text.count("\n", 0, header_match.end())
    lines = text.splitlines()[start_offset:]
    items: list[Item] = []
    current: Item | None = None
    fields: list[list[str]] = []  # [key_raw, value] in file order

    def flush():
        if current is not None:
            _apply_fields(current, [(k, v) for k, v in fields])
            items.append(current)

    for lineno, raw_line in enumerate(lines, start=start_offset + 1):
        entry_match = ENTRY_HEADER_RE.match(raw_line)
        if entry_match:
            flush()
            entry_id, title = entry_match.groups()
            current = Item(id=entry_id, title=title, source_file=source_file, project=project, line=lineno)
            fields = []
            continue

        if current is None:
            continue

        field_match = FIELD_RE.match(raw_line)
        if field_match:
            key_raw, value = field_match.groups()
            fields.append([key_raw, value])
            continue

        stripped = raw_line.strip()
        if not stripped:
            continue
        if not raw_line.startswith(" "):
            # Unindented text (e.g. a new heading) ends the current entry.
            flush()
            current = None
            fields = []
            continue
        if fields:
            # Continuation line (wrapped text) for the most recent field.
            fields[-1][1] += " " + stripped

    flush()
    return items


def looks_like_backlog_v2(text: str) -> bool:
    return bool(ENTRY_HEADER_RE.search(text)) and bool(BACKLOG_V2_MARKER_RE.search(text))


def parse_checkbox_tree(text: str, source_file: str, project: str) -> list[Item]:
    lines = text.splitlines()
    items: list[Item] = []
    stack: list[tuple[int, str]] = []  # (indent_width, item_id)

    for lineno, raw_line in enumerate(lines, start=1):
        m = CHECKBOX_RE.match(raw_line)
        if not m:
            continue
        indent, mark, text_content = m.groups()
        indent_width = len(indent)
        item_id = f"{Path(source_file).stem}:{lineno}"

        while stack and stack[-1][0] >= indent_width:
            stack.pop()
        parent_id = stack[-1][1] if stack else None

        status = "Completed" if mark.lower() == "x" else "Open"
        items.append(
            Item(
                id=item_id,
                title=text_content.strip(),
                source_file=source_file,
                project=project,
                line=lineno,
                format=ItemFormat.CHECKBOX,
                item_type="Task",
                status=status,
                parent=parent_id,
                dependencies=[],
            )
        )
        stack.append((indent_width, item_id))

    return items


def parse_file(path: Path, project: str) -> list[Item]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if looks_like_backlog_v2(text):
        items = parse_backlog_v2(text, str(path), project)
        if path.name == ARCHIVE_FILE:
            for item in items:
                item.location = Location.ARCHIVE
        return items
    if path.name == ARCHIVE_FILE:
        # An archive never falls back to checkbox parsing ("No entries." etc.).
        return []
    return parse_checkbox_tree(text, str(path), project)


EDITABLE_FIELDS = Field.EDITABLE
FIELD_LABELS = {"status": "Status", "priority": "Priority", "resolution": "Resolution"}


# ---------- editing ----------

def _read_lines(path: Path) -> tuple[list[str], str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    newline = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n").split("\n"), newline


def _write_lines(path: Path, lines: list[str], newline: str) -> None:
    path.write_text(newline.join(lines), encoding="utf-8")


def _block_end(lines: list[str], idx: int) -> int:
    """Index after the last line of the entry whose header is at `idx`."""
    end = idx + 1
    while end < len(lines):
        line = lines[end]
        if ENTRY_HEADER_RE.match(line) or not line.strip() or not line.startswith("  "):
            break
        end += 1
    return end


def _find_field(lines: list[str], start: int, end: int, key: str) -> tuple[int, int] | None:
    """(first line, end line exclusive) of a field incl. its continuation lines."""
    for i in range(start, end):
        m = FIELD_RE.match(lines[i])
        if m and _slug(m.group(1)) == key:
            j = i + 1
            while j < end and not FIELD_RE.match(lines[j]):
                j += 1
            return i, j
    return None


def _set_field(lines: list[str], idx: int, key: str, value: str) -> None:
    """Sets a field of the entry at `idx` (replacing continuation lines too)."""
    end = _block_end(lines, idx)
    found = _find_field(lines, idx + 1, end, key)
    value = value.strip()
    if found is not None:
        first, stop = found
        label_raw = FIELD_RE.match(lines[first]).group(1)
        trailing = "" if value.endswith(".") else "."
        lines[first:stop] = [f"  - {label_raw}: {value}{trailing}"]
    else:
        trailing = "" if value.endswith(".") else "."
        lines.insert(end, f"  - {FIELD_LABELS[key]}: {value}{trailing}")


def _remove_field(lines: list[str], idx: int, key: str) -> None:
    end = _block_end(lines, idx)
    found = _find_field(lines, idx + 1, end, key)
    if found is not None:
        del lines[found[0]:found[1]]


def _work_items_start(lines: list[str]) -> int | None:
    for i, line in enumerate(lines):
        if WORK_ITEMS_HEADER_RE.match(line):
            return i
    return None


def _cut_block(lines: list[str], idx: int) -> list[str]:
    """Removes the entry at `idx` (and one separating blank line) and returns it."""
    end = _block_end(lines, idx)
    block = lines[idx:end]
    stop = end + 1 if end < len(lines) and not lines[end].strip() else end
    start = idx
    if stop == end and idx > 0 and not lines[idx - 1].strip():
        start = idx - 1  # last entry: drop the blank line before it instead
    del lines[start:stop]

    section = _work_items_start(lines)
    if section is not None and not any(ENTRY_HEADER_RE.match(l) for l in lines[section:]):
        rest = [l for l in lines[section + 1:] if l.strip()]
        if not rest:
            del lines[section + 1:]
            lines.extend(["", NO_ENTRIES_LINE, ""])
    return block


def _append_block(lines: list[str], block: list[str]) -> None:
    section = _work_items_start(lines)
    if section is not None:
        for i in range(section + 1, len(lines)):
            if lines[i].strip() == NO_ENTRIES_LINE:
                del lines[i]
                break
    while lines and not lines[-1].strip():
        lines.pop()
    lines.extend([""] + block + [""])


def archive_supported(path: Path, fmt: ItemFormat) -> bool:
    return (
        fmt is ItemFormat.BACKLOG_V2
        and path.name in (TODO_FILE, ARCHIVE_FILE)
        and (path.parent / TODO_FILE).exists()
        and (path.parent / ARCHIVE_FILE).exists()
    )


def update_item_field(
    path: Path,
    line: int,
    item_id: str,
    fmt: str,
    field_key: str,
    value: str,
    resolution: str | None = None,
) -> Path:
    """Rewrites a single field of one entry in its source markdown file.

    The edit rules (resolution + archiving for Completed/Rejected) come from
    the domain's EditPlanner; this function only applies the resulting changes.

    Returns the file the entry lives in afterwards. Raises a DomainError if the
    entry at `line` no longer matches `item_id` or the edit is not allowed.
    """
    try:
        item_format = ItemFormat(fmt)
    except ValueError:
        raise UnknownFormatError(fmt) from None

    lines, newline = _read_lines(path)
    idx = line - 1
    if idx < 0 or idx >= len(lines):
        raise EntryMovedError("Line not found (file was probably changed externally).")

    if item_format is ItemFormat.CHECKBOX:
        checkbox_match = CHECKBOX_RE.match(lines[idx])
        if item_id != f"{path.stem}:{line}" or not checkbox_match:
            raise EntryMovedError()
    else:
        header_match = ENTRY_HEADER_RE.match(lines[idx])
        if not header_match or header_match.group(1) != item_id:
            raise EntryMovedError()

    location = Location.ARCHIVE if path.name == ARCHIVE_FILE else Location.ACTIVE
    item = Item(id=item_id, title="", source_file=str(path), project="", line=line,
                format=item_format, location=location)
    changes = EditPlanner().plan(item, field_key, value, resolution, archive_supported(path, item_format))

    if item_format is ItemFormat.CHECKBOX:
        mark = "x" if value == "Completed" else " "
        indent, _old_mark, content = checkbox_match.groups()
        lines[idx] = f"{indent}- [{mark}] {content}"
        _write_lines(path, lines, newline)
        return path

    for key, new_value in changes.set_fields:
        _set_field(lines, idx, key, new_value)
    for key in changes.remove_fields:
        _remove_field(lines, idx, key)

    if changes.move_to is None:
        _write_lines(path, lines, newline)
        return path

    target = path.parent / (ARCHIVE_FILE if changes.move_to is Location.ARCHIVE else TODO_FILE)
    target_lines, target_newline = _read_lines(target)
    block = _cut_block(lines, idx)
    _append_block(target_lines, block)
    # Write the destination first so the entry is never lost.
    _write_lines(target, target_lines, target_newline)
    _write_lines(path, lines, newline)
    return target

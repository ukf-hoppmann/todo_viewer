from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import notes_head

TODO_FILE = "TODO.md"
ARCHIVE_FILE = "archive.md"

ITEM_TYPES = {"Epic", "Story", "Task"}
STATUSES = {"Open", "In progress", "Awaiting confirmation", "Completed", "Rejected"}
CLOSED_STATUSES = {"Completed", "Rejected"}
READY_CHILD_STATUSES = {"Awaiting confirmation", "Completed"}
# A rejected required child is a gap in the parent's goal that only the owner can resolve.
REJECTED_REQUIRED_HINT = (
    "for a Rejected required child, ask the owner whether to set Required for parent: No "
    "(and adjust the parent's Goal and Completion criteria if they name the child's content) "
    "or to reject the parent as well"
)
PRIORITIES = {"Urgent", "Important", "Normal", "Prospective"}
REQUIRED_FIELDS = {
    "Type",
    "Status",
    "Created",
    "Priority",
    "Dependencies",
    "Goal",
    "Completion criteria",
}
KNOWN_FIELDS = REQUIRED_FIELDS | {
    "Uid",
    "Parent",
    "Required for parent",
    "Resolution",
    "Summary",
    # Items in the ToDo-Viewer's trash; they belong in archive.md with any status.
    "Deleted",
    # Version 2 had an Area field; version 3 dropped it. It is read and ignored, never written.
    "Area",
}
# New entries written without the ToDo-Viewer: no Uid yet, and the import sets Created.
PLACEHOLDER_OPTIONAL_FIELDS = {"Created"}

FORMAT_PREFIX = "Format:"
FORMAT_VERSION = 3
# Read: versions 2 and 3. Written: only the current version (FORMAT_VERSION).
FORMAT_MARKER = f"backlog format version {FORMAT_VERSION}"
_FORMAT_READ = re.compile(r"backlog format version (?:2|3)(?![0-9])")

_ID = r"[A-Z][A-Z0-9_-]*-[0-9]{3,}"
# A placeholder stands for an entry the ToDo-Viewer has not given a label yet.
_PLACEHOLDER_PREFIX = "NEW-"
_PLACEHOLDER = r"NEW-[a-z0-9][a-z0-9-]*"
_ANY_ID = rf"{_PLACEHOLDER}|{_ID}"
_ITEM_HEADER = re.compile(
    rf"^- `(?P<identifier>{_ID}|{_PLACEHOLDER_PREFIX}[^`\s]*)` \*\*(?P<title>[^*\r\n].*?)\*\*$"
)
_FIELD = re.compile(r"^  - (?P<name>[^:\r\n]+):(?P<value>.*)$")
_REFERENCE = re.compile(rf"`({_ANY_ID})`")
_UID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_EMPTY_MARKER = "No entries."


@dataclass(frozen=True)
class BacklogItem:
    identifier: str
    title: str
    source: str
    uid: str | None
    item_type: str
    status: str
    created: date | None
    priority: str
    dependencies: tuple[str, ...]
    parent: str | None
    required_for_parent: bool | None
    resolution: str | None
    deleted: date | None = None


@dataclass
class BacklogReport:
    items: list[BacklogItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_backlog(todo_dir: Path) -> BacklogReport:
    """Validate TODO.md and archive.md in todo_dir as one backlog."""
    report = BacklogReport()
    todo_file = todo_dir / TODO_FILE
    if not todo_file.is_file():
        report.errors.append(f"{TODO_FILE} not found in {todo_dir}")
        return report

    seen_ids: dict[str, str] = {}
    seen_uids: dict[str, str] = {}
    files = [todo_file]
    archive_file = todo_dir / ARCHIVE_FILE
    if archive_file.is_file():
        files.append(archive_file)

    for path in files:
        for identifier, title, fields, line in _parse_file(path, report):
            location = f"{path.name}:{line}"
            if identifier in seen_ids:
                report.errors.append(
                    f"{identifier} is defined twice ({seen_ids[identifier]} and {location})"
                )
                continue
            seen_ids[identifier] = location
            item = _build_item(identifier, title, path.name, fields, report)
            if item is None:
                continue
            if item.uid is not None:
                if item.uid in seen_uids:
                    report.errors.append(f"{identifier} uses the Uid of {seen_uids[item.uid]}")
                    continue
                seen_uids[item.uid] = identifier
            report.items.append(item)

    _validate_placement(report)
    _validate_relationships(report, set(seen_ids))
    _validate_lifecycle(report)
    return report


def _parse_file(path: Path, report: BacklogReport) -> list[tuple[str, str, dict[str, str], int]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    sections = [i for i, line in enumerate(lines) if line == "## Work items"]
    if len(sections) != 1:
        report.errors.append(f"{path.name} requires exactly one '## Work items' section")
        return []
    _check_format(path.name, lines[: sections[0]], report)

    raw: list[tuple[str, str, dict[str, str], int]] = []
    current: tuple[str, str, dict[str, str], int] | None = None
    field_name: str | None = None

    for index in range(sections[0] + 1, len(lines)):
        line = lines[index]
        number = index + 1
        header = _ITEM_HEADER.fullmatch(line)
        if header:
            current = (header.group("identifier"), header.group("title").strip(), {}, number)
            raw.append(current)
            field_name = None
            continue
        if not line.strip():
            continue
        if current is None and line.strip() == _EMPTY_MARKER:
            continue
        match = _FIELD.fullmatch(line)
        if match:
            if current is None:
                report.errors.append(f"{path.name}:{number} field outside an item")
                continue
            fields = current[2]
            field_name = match.group("name").strip()
            value = match.group("value").strip()
            if field_name in fields:
                report.errors.append(f"{current[0]} contains duplicate field: {field_name}")
            elif not value:
                report.errors.append(f"{current[0]} has an empty field: {field_name}")
            else:
                fields[field_name] = value
            continue
        if line.startswith("    ") and current is not None and field_name in current[2]:
            current[2][field_name] = f"{current[2][field_name]} {line.strip()}"
            continue
        report.errors.append(f"{path.name}:{number} invalid backlog content: {line}")
    return raw


def _check_format(name: str, head: list[str], report: BacklogReport) -> None:
    # The format line is a paragraph starting with "Format:"; it may wrap over several lines.
    paragraphs = " ".join(line.strip() if line.strip() else "\n" for line in head).split("\n")
    formats = [p.strip() for p in paragraphs if p.strip().startswith(FORMAT_PREFIX)]
    if not formats:
        report.errors.append(
            f"{name} has no format line; expected a paragraph "
            f"'{FORMAT_PREFIX} Claude_Harness {FORMAT_MARKER}' before '## Work items'"
        )
    elif not any(_FORMAT_READ.search(" ".join(f.split())) for f in formats):
        report.errors.append(
            f"{name} uses an unsupported backlog format (versions 2 and 3 are read, {FORMAT_MARKER} is written; "
            f"convert older backlogs): {formats[0]}"
        )


def _build_item(
    identifier: str,
    title: str,
    source: str,
    fields: dict[str, str],
    report: BacklogReport,
) -> BacklogItem | None:
    errors: list[str] = []
    placeholder = identifier.startswith(_PLACEHOLDER_PREFIX)
    if placeholder and not re.fullmatch(_PLACEHOLDER, identifier):
        report.errors.append(
            f"invalid placeholder: {identifier} (use NEW- and a short name of a-z, 0-9, -)"
        )
        return None

    required = REQUIRED_FIELDS - PLACEHOLDER_OPTIONAL_FIELDS if placeholder else REQUIRED_FIELDS
    missing = sorted(required - fields.keys())
    if missing:
        report.errors.append(f"{identifier} is missing required fields: {', '.join(missing)}")
        return None

    unknown = sorted(fields.keys() - KNOWN_FIELDS)
    if unknown:
        errors.append(f"{identifier} has unknown fields: {', '.join(unknown)}")

    uid: str | None = None
    if placeholder:
        if "Uid" in fields:
            errors.append(f"{identifier} is a new entry and must not contain Uid")
    elif "Uid" not in fields:
        errors.append(f"{identifier} is missing required field: Uid")
    else:
        uid = _scalar(fields["Uid"]).lower()
        if not _UID.fullmatch(uid):
            errors.append(f"{identifier} Uid must be a UUID")

    item_type = _scalar(fields["Type"])
    if item_type not in ITEM_TYPES:
        errors.append(f"{identifier} Type must be Epic, Story, or Task: {item_type}")
    status = _scalar(fields["Status"])
    if status not in STATUSES:
        errors.append(f"{identifier} has unsupported Status: {status}")
    priority = _scalar(fields["Priority"])
    if priority not in PRIORITIES:
        errors.append(
            f"{identifier} Priority must be one of {', '.join(sorted(PRIORITIES))}: {priority}"
        )
    created: date | None = None
    if "Created" in fields:
        try:
            created = date.fromisoformat(_scalar(fields["Created"]))
        except ValueError:
            errors.append(f"{identifier} Created must use YYYY-MM-DD")

    deleted: date | None = None
    if "Deleted" in fields:
        try:
            deleted = date.fromisoformat(_scalar(fields["Deleted"]))
        except ValueError:
            errors.append(f"{identifier} Deleted must use YYYY-MM-DD")

    dependencies = _references(identifier, "Dependencies", fields["Dependencies"], errors)

    parent: str | None = None
    required_for_parent: bool | None = None
    if item_type == "Epic":
        for name in ("Parent", "Required for parent"):
            if name in fields:
                errors.append(f"{identifier} Epic must not contain {name}")
    elif item_type in ITEM_TYPES:
        if "Parent" not in fields:
            errors.append(f"{identifier} is missing required field: Parent")
        else:
            parents = _references(identifier, "Parent", fields["Parent"], errors)
            if len(parents) > 1:
                errors.append(f"{identifier} Parent must be one identifier or None")
            parent = parents[0] if parents else None
        required_value = fields.get("Required for parent")
        if parent is not None:
            if required_value is None:
                errors.append(f"{identifier} is missing required field: Required for parent")
            elif _scalar(required_value) not in {"Yes", "No"}:
                errors.append(f"{identifier} Required for parent must be Yes or No")
            else:
                required_for_parent = _scalar(required_value) == "Yes"
        elif required_value is not None:
            errors.append(f"{identifier} without a Parent must not contain Required for parent")

    resolution = fields.get("Resolution")
    if status in CLOSED_STATUSES and resolution is None:
        errors.append(f"{identifier} with Status {status} requires Resolution")
    if status not in CLOSED_STATUSES and resolution is not None:
        errors.append(f"{identifier} with active Status {status} must not contain Resolution")

    if errors:
        report.errors.extend(errors)
        return None
    return BacklogItem(
        identifier=identifier,
        title=title,
        source=source,
        uid=uid,
        item_type=item_type,
        status=status,
        created=created,
        priority=priority,
        dependencies=dependencies,
        parent=parent,
        required_for_parent=required_for_parent,
        resolution=resolution,
        deleted=deleted,
    )


def _validate_placement(report: BacklogReport) -> None:
    # In format 2 the file carries no information (the ToDo-Viewer moves entries), so misplaced
    # entries are notices, not errors.
    for item in report.items:
        if item.deleted is not None:
            if item.source != ARCHIVE_FILE:
                report.notices.append(f"{item.identifier} is Deleted; move it to {ARCHIVE_FILE}")
            continue
        if item.source == ARCHIVE_FILE and item.status not in CLOSED_STATUSES:
            report.notices.append(f"{item.identifier} is {item.status}; move it to {TODO_FILE}")
        if item.source == TODO_FILE and item.status in CLOSED_STATUSES:
            report.notices.append(
                f"{item.identifier} is {item.status}; move it to {ARCHIVE_FILE}"
            )


def _validate_relationships(report: BacklogReport, known_ids: set[str]) -> None:
    by_id = {item.identifier: item for item in report.items}
    for item in report.items:
        if item.parent is not None:
            if item.parent not in known_ids:
                report.errors.append(f"{item.identifier} references missing parent: {item.parent}")
            elif item.parent in by_id:
                parent = by_id[item.parent]
                allowed = {"Epic"} if item.item_type == "Story" else {"Epic", "Story"}
                if parent.item_type not in allowed:
                    report.errors.append(
                        f"{item.identifier} {item.item_type} cannot use "
                        f"{parent.item_type} {parent.identifier} as Parent"
                    )
        for dependency in item.dependencies:
            if dependency == item.identifier:
                report.errors.append(f"{item.identifier} must not depend on itself")
            elif dependency not in known_ids:
                report.errors.append(
                    f"{item.identifier} references missing dependency: {dependency}"
                )

    parent_edges = {
        item.identifier: (item.parent,) if item.parent in by_id else ()
        for item in report.items
    }
    dependency_edges = {
        item.identifier: tuple(d for d in item.dependencies if d in by_id and d != item.identifier)
        for item in report.items
    }
    _reject_cycles(parent_edges, "parent", report)
    _reject_cycles(dependency_edges, "dependency", report)


def _validate_lifecycle(report: BacklogReport) -> None:
    # Deleted items are in the trash; like the ToDo-Viewer, the parent rules ignore them.
    live = [item for item in report.items if item.deleted is None]
    children: dict[str, list[BacklogItem]] = {item.identifier: [] for item in live}
    for item in live:
        if item.parent in children:
            children[item.parent].append(item)

    for item in live:
        kids = children[item.identifier]
        required = [child for child in kids if child.required_for_parent]
        if item.item_type == "Epic" and item.status not in {"Open", "Rejected"} and not required:
            report.errors.append(
                f"{item.identifier} Epic with Status {item.status} requires at least one required child"
            )
        if item.status == "Awaiting confirmation":
            unready = [c for c in required if c.status not in READY_CHILD_STATUSES]
            if unready:
                report.errors.append(
                    f"{item.identifier} cannot be Awaiting confirmation while required "
                    f"children are not done: {_with_status(unready)}{_rejected_hint(unready)}"
                )
        if item.status == "Completed":
            incomplete = [c for c in required if c.status != "Completed"]
            if incomplete:
                report.errors.append(
                    f"{item.identifier} cannot be Completed while required children "
                    f"are incomplete: {_with_status(incomplete)}{_rejected_hint(incomplete)}"
                )
            active = [
                c.identifier for c in kids
                if not c.required_for_parent and c.status not in CLOSED_STATUSES
            ]
            if active:
                report.errors.append(
                    f"{item.identifier} cannot be Completed while children are still "
                    f"active: {', '.join(active)} (close or reparent them first)"
                )
        if (
            item.status in {"Open", "In progress"}
            and required
            and all(c.status == "Completed" for c in required)
        ):
            notice = (
                f"{item.identifier}: all required children are Completed; check its own "
                "completion criteria, then set Awaiting confirmation and tell the owner, "
                "or report what is missing"
            )
            open_optional = [c.identifier for c in kids if c.status not in CLOSED_STATUSES]
            if open_optional:
                notice += (
                    f" (children still active: {', '.join(open_optional)}; close or "
                    "reparent them before completion)"
                )
            report.notices.append(notice)
        elif (
            item.status in {"Open", "In progress"}
            and required
            and all(c.status in CLOSED_STATUSES for c in required)
        ):
            rejected = [c for c in required if c.status == "Rejected"]
            report.notices.append(
                f"{item.identifier}: all required children are closed, but "
                f"{_with_status(rejected)} can never be completed; {REJECTED_REQUIRED_HINT}"
            )
        if item.status == "Rejected":
            active = [c.identifier for c in kids if c.status not in CLOSED_STATUSES]
            if active:
                report.errors.append(
                    f"{item.identifier} is Rejected but has active children: {', '.join(active)}"
                )


def _with_status(items: list[BacklogItem]) -> str:
    return ", ".join(f"{item.identifier} ({item.status})" for item in items)


def _rejected_hint(items: list[BacklogItem]) -> str:
    return f"; {REJECTED_REQUIRED_HINT}" if any(item.status == "Rejected" for item in items) else ""


def _reject_cycles(edges: dict[str, tuple[str, ...]], label: str, report: BacklogReport) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str, trail: tuple[str, ...]) -> bool:
        if identifier in visiting:
            report.errors.append(f"{label} cycle detected: {' -> '.join((*trail, identifier))}")
            return True
        if identifier in visited:
            return False
        visiting.add(identifier)
        for target in edges.get(identifier, ()):
            if visit(target, (*trail, identifier)):
                return True
        visiting.discard(identifier)
        visited.add(identifier)
        return False

    for identifier in edges:
        if identifier not in visited and visit(identifier, ()):
            return


def _scalar(value: str) -> str:
    normalized = value.strip()
    if normalized.endswith("."):
        normalized = normalized[:-1].rstrip()
    return normalized


def _references(identifier: str, name: str, value: str, errors: list[str]) -> tuple[str, ...]:
    normalized = _scalar(value)
    if normalized == "None":
        return ()
    references = []
    for part in (p.strip() for p in normalized.split(",")):
        match = _REFERENCE.fullmatch(part)
        if match is None:
            errors.append(f"{identifier} {name} must contain backticked identifiers or None")
            return ()
        references.append(match.group(1))
    if len(set(references)) != len(references):
        errors.append(f"{identifier} contains duplicate {name} references")
    return tuple(references)


def format_report(report: BacklogReport) -> str:
    lines = [f"error: {e}" for e in report.errors]
    lines += [f"notice: {n}" for n in report.notices]
    return "\n".join(lines)


def format_index(report: BacklogReport) -> str:
    lines = ["ID | Type | Status | Title | Parent"]
    for item in sorted(report.items, key=lambda i: i.identifier):
        status = item.status if item.deleted is None else f"{item.status} (deleted {item.deleted.isoformat()})"
        lines.append(
            f"{item.identifier} | {item.item_type} | {status} | {item.title} "
            f"| {item.parent or '-'}"
        )
    return "\n".join(lines)


def show_items(todo_dir: Path, identifiers: list[str]) -> tuple[str, list[str]]:
    """Return the raw entries of the given items from TODO.md and archive.md, and the missing IDs."""
    blocks: dict[str, str] = {}
    for name in (TODO_FILE, ARCHIVE_FILE):
        path = todo_dir / name
        if path.is_file():
            for identifier, block in _raw_entries(path):
                if identifier in identifiers and identifier not in blocks:
                    blocks[identifier] = f"Source: {name}\n{block}"
    shown = [blocks[i] for i in identifiers if i in blocks]
    return "\n\n".join(shown), [i for i in identifiers if i not in blocks]


def _raw_entries(path: Path) -> list[tuple[str, str]]:
    # Entries as written, without validation, so broken items can be shown too.
    entries: list[tuple[str, list[str]]] = []
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line == "## Work items"
            continue
        if not in_section:
            continue
        header = _ITEM_HEADER.fullmatch(line)
        if header:
            entries.append((header.group("identifier"), [line]))
        elif entries and (line.startswith("  ") or not line.strip()):
            entries[-1][1].append(line)
    return [(identifier, "\n".join(lines).rstrip()) for identifier, lines in entries]


USAGE = "usage: backlog.py <backlog-folder> [--index | --show <ID> [<ID> ...] | --confirm-state <ID>]"


def confirm_state(todo_dir: Path, identifier: str) -> int:
    """Set the stamp line of the item's notes head (skills/todo/format.md, section Notes)."""
    path = todo_dir / "items" / identifier / f"{identifier}_notes.md"
    try:
        with path.open(encoding="utf-8", newline="") as source:
            text = source.read()
    except OSError:
        print(f"no notes file: {path}", file=sys.stderr)
        return 1
    try:
        text = notes_head.confirmed(text)
    except notes_head.NotesHeadError as error:
        print(f"{identifier}: {error}", file=sys.stderr)
        return 1
    with path.open("w", encoding="utf-8", newline="") as target:
        target.write(text)
    stamp = notes_head.split(text).stamp
    print(f"confirmed {identifier}: {stamp.day} — {stamp.topic} ({stamp.checksum})")
    return 0


def main(argv: list[str]) -> int:
    args = argv[1:]
    if "--confirm-state" in args:
        at = args.index("--confirm-state")
        rest = args[:at] + args[at + 2:]
        if at + 1 >= len(args) or not re.fullmatch(_ANY_ID, args[at + 1]) or len(rest) != 1:
            print(USAGE, file=sys.stderr)
            return 2
        return confirm_state(Path(rest[0]), args[at + 1])
    identifiers: list[str] | None = None
    if "--show" in args:
        at = args.index("--show")
        args, identifiers = args[:at], args[at + 1:]
        if not identifiers or not all(re.fullmatch(_ANY_ID, i) for i in identifiers):
            print(USAGE, file=sys.stderr)
            return 2
    index = "--index" in args
    args = [a for a in args if a != "--index"]
    if len(args) != 1 or (index and identifiers is not None):
        print(USAGE, file=sys.stderr)
        return 2
    if identifiers is not None:
        output, missing = show_items(Path(args[0]), identifiers)
        if output:
            print(output)
        if missing:
            print(f"not found in {TODO_FILE} or {ARCHIVE_FILE}: {', '.join(missing)}", file=sys.stderr)
            return 1
        return 0
    report = validate_backlog(Path(args[0]))
    if index:
        print(format_index(report))
        if report.errors:
            print(f"({len(report.errors)} items or rules invalid; run without --index for details)")
        return 0 if report.ok else 1
    output = format_report(report)
    if output:
        print(output)
    print(f"{len(report.items)} valid items, {len(report.errors)} errors, {len(report.notices)} notices")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

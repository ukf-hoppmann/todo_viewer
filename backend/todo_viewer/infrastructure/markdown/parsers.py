"""Parsers turning the lines of one markdown file into Items."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from todo_viewer.domain.item import Item, ItemFormat, Location, Status

from .field_mapper import BacklogFieldMapper
from .syntax import CHECKBOX_RE, ENTRY_HEADER_RE, FIELD_RE, WORK_ITEMS_HEADER_RE


class ItemParser(Protocol):
    def parse(self, lines: list[str], source_file: str, project: str, location: Location) -> list[Item]: ...


class BacklogParser:
    """Structured backlog entries; only the `## Work items` section counts if present."""

    def __init__(self, fields: BacklogFieldMapper):
        self._fields = fields

    def parse(self, lines: list[str], source_file: str, project: str, location: Location) -> list[Item]:
        start = next((i for i, line in enumerate(lines) if WORK_ITEMS_HEADER_RE.match(line)), 0)
        items: list[Item] = []
        current: Item | None = None
        fields: list[list[str]] = []  # [label, value] in file order

        def flush() -> None:
            if current is not None:
                self._fields.apply(current, [(k, v) for k, v in fields])
                items.append(current)

        for lineno in range(start + 1, len(lines) + 1):
            raw_line = lines[lineno - 1]
            entry_match = ENTRY_HEADER_RE.match(raw_line)
            if entry_match:
                flush()
                entry_id, title = entry_match.groups()
                current = Item(id=entry_id, title=title, source_file=source_file, project=project,
                               line=lineno, location=location)
                fields = []
                continue

            if current is None:
                continue

            field_match = FIELD_RE.match(raw_line)
            if field_match:
                fields.append(list(field_match.groups()))
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


class ChecklistParser:
    """Nested `- [ ]` lists; indentation defines the parent. IDs are `<file stem>:<line>`."""

    def parse(self, lines: list[str], source_file: str, project: str, location: Location) -> list[Item]:
        items: list[Item] = []
        stack: list[tuple[int, str]] = []  # (indent width, item id)
        stem = Path(source_file).stem

        for lineno, raw_line in enumerate(lines, start=1):
            m = CHECKBOX_RE.match(raw_line)
            if not m:
                continue
            indent, mark, text = m.groups()
            item_id = f"{stem}:{lineno}"
            while stack and stack[-1][0] >= len(indent):
                stack.pop()
            items.append(Item(
                id=item_id,
                title=text.strip(),
                source_file=source_file,
                project=project,
                line=lineno,
                format=ItemFormat.CHECKBOX,
                status=Status.COMPLETED if mark.lower() == "x" else Status.OPEN,
                parent=stack[-1][1] if stack else None,
                location=location,
            ))
            stack.append((len(indent), item_id))
        return items

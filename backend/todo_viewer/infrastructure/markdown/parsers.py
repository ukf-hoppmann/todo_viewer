"""Parser turning the lines of one markdown file into Items."""
from __future__ import annotations

from todo_viewer.domain.item import Item, Location

from .field_mapper import BacklogFieldMapper
from .syntax import ENTRY_HEADER_RE, FIELD_RE, work_items_start


class BacklogParser:
    """Structured backlog entries; only the `## Work items` section counts if present."""

    def __init__(self, fields: BacklogFieldMapper):
        self._fields = fields

    def parse(self, lines: list[str], project: str, location: Location) -> list[Item]:
        start = work_items_start(lines)
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
                current = Item(id=entry_id, title=title, project=project, location=location)
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

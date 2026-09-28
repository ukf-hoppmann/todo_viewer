"""In-place edits on the lines of a markdown file. All methods mutate `lines`."""
from __future__ import annotations

from todo_viewer.domain.errors import DuplicateItemError, ItemNotFoundError

from .syntax import (
    ENTRY_HEADER_RE,
    FIELD_LABELS,
    FIELD_RE,
    NO_ENTRIES_LINE,
    WORK_ITEMS_HEADER_RE,
    field_key,
    work_items_start,
)


class EntryLocator:
    """Finds the line index of the entry with a given id by its header line."""

    def locate(self, lines: list[str], item_id: str) -> int:
        found = [i for i in range(work_items_start(lines), len(lines))
                 if (header := ENTRY_HEADER_RE.match(lines[i])) and header.group(1) == item_id]
        if not found:
            raise ItemNotFoundError(item_id)
        if len(found) > 1:
            raise DuplicateItemError(item_id)
        return found[0]


def block_end(lines: list[str], idx: int) -> int:
    """Index after the last line of the entry whose header is at `idx`."""
    end = idx + 1
    while end < len(lines):
        line = lines[end]
        if ENTRY_HEADER_RE.match(line) or not line.strip() or not line.startswith("  "):
            break
        end += 1
    return end


def _with_period(value: str) -> str:
    return value if value.endswith(".") else value + "."


class BacklogEntryEditor:
    """Sets or removes `  - Key: value.` fields of one structured entry."""

    def set_field(self, lines: list[str], idx: int, key: str, value: str) -> None:
        end = block_end(lines, idx)
        found = self._find_field(lines, idx + 1, end, key)
        value = _with_period(value.strip())
        if found is not None:
            first, stop = found
            match = FIELD_RE.match(lines[first])
            assert match is not None
            lines[first:stop] = [f"  - {match.group(1)}: {value}"]
        else:
            lines.insert(end, f"  - {FIELD_LABELS[key]}: {value}")

    def remove_field(self, lines: list[str], idx: int, key: str) -> None:
        end = block_end(lines, idx)
        found = self._find_field(lines, idx + 1, end, key)
        if found is not None:
            del lines[found[0]:found[1]]

    @staticmethod
    def _find_field(lines: list[str], start: int, end: int, key: str) -> tuple[int, int] | None:
        """(first line, end line exclusive) of a field incl. its continuation lines."""
        for i in range(start, end):
            m = FIELD_RE.match(lines[i])
            if m and field_key(m.group(1)) == key:
                j = i + 1
                while j < end and not FIELD_RE.match(lines[j]):
                    j += 1
                return i, j
        return None


class EntryMover:
    """Moves a structured entry between the `## Work items` sections of two files."""

    def cut(self, lines: list[str], idx: int) -> list[str]:
        """Removes the entry at `idx` (and one separating blank line) and returns it."""
        end = block_end(lines, idx)
        block = lines[idx:end]
        stop = end + 1 if end < len(lines) and not lines[end].strip() else end
        start = idx
        if stop == end and idx > 0 and not lines[idx - 1].strip():
            start = idx - 1  # last entry: drop the blank line before it instead
        del lines[start:stop]

        section = self._section_start(lines)
        if section is not None and not any(ENTRY_HEADER_RE.match(line) for line in lines[section:]):
            rest = [line for line in lines[section + 1:] if line.strip()]
            if not rest:
                del lines[section + 1:]
                lines.extend(["", NO_ENTRIES_LINE, ""])
        return block

    def append(self, lines: list[str], block: list[str]) -> None:
        section = self._section_start(lines)
        if section is not None:
            for i in range(section + 1, len(lines)):
                if lines[i].strip() == NO_ENTRIES_LINE:
                    del lines[i]
                    break
        while lines and not lines[-1].strip():
            lines.pop()
        lines.extend(["", *block, ""])

    @staticmethod
    def _section_start(lines: list[str]) -> int | None:
        return next((i for i, line in enumerate(lines) if WORK_ITEMS_HEADER_RE.match(line)), None)

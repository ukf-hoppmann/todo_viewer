"""In-place edits on the lines of a markdown file. All methods mutate `lines`."""
from __future__ import annotations

import textwrap

from todo_viewer.domain.editing import FieldValue
from todo_viewer.domain.errors import DuplicateItemError, ItemNotFoundError
from todo_viewer.domain.item import Item

from .document_paths import path_of
from .syntax import (
    ENTRY_HEADER_RE,
    FIELD_LABELS,
    FIELD_RE,
    ID_FIELDS,
    LINE_WIDTH,
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


def _file_value(key: str, value: FieldValue) -> str:
    """How a value is spelled in the file (ids in backticks, "None" for no reference)."""
    if key in ID_FIELDS:
        ids = [value] if isinstance(value, str) else list(value or ())
        return ", ".join(f"`{i}`" for i in ids) if ids else "None"
    return str(value or "").strip()


def _field_lines(label: str, value: str) -> list[str]:
    return textwrap.wrap(value, width=LINE_WIDTH, initial_indent=f"  - {label}: ", subsequent_indent="    ",
                         break_long_words=False, break_on_hyphens=False) or [f"  - {label}: "]


class BacklogEntryEditor:
    """Sets or removes `  - Key: value.` fields of one structured entry."""

    def set_field(self, lines: list[str], idx: int, key: str, value: FieldValue) -> None:
        if key == "title":
            lines[idx] = ENTRY_HEADER_RE.sub(lambda m: f"- `{m.group(1)}` **{value}**", lines[idx])
            return
        if key == "id":
            lines[idx] = ENTRY_HEADER_RE.sub(lambda m: f"- `{value}` **{m.group(2)}**", lines[idx])
            return
        end = block_end(lines, idx)
        found = self._find_field(lines, idx + 1, end, key)
        text = _with_period(_file_value(key, value))
        if found is not None:
            first, stop = found
            match = FIELD_RE.match(lines[first])
            assert match is not None
            lines[first:stop] = _field_lines(match.group(1), text)
        else:
            lines[end:end] = _field_lines(FIELD_LABELS[key], text)

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


class EntryRenderer:
    """Writes a new entry in the field order of the backlog format."""

    def render(self, item: Item) -> list[str]:
        lines = [f"- `{item.id}` **{item.title}**", *_field_lines("Type", _with_period(item.item_type))]
        if item.item_type != "Epic":
            lines += _field_lines("Parent", _with_period(_file_value("parent", item.parent)))
            if item.parent:
                lines += _field_lines("Required for parent", "Yes." if item.required_for_parent else "No.")
        for label, key, value in (
            ("Status", "status", item.status),
            ("Created", "created", item.created),
            ("Area", "area", item.area),
            ("Priority", "priority", item.priority),
            ("Dependencies", "dependencies", tuple(item.dependencies)),
            ("Goal", "goal", item.goal),
            ("Completion criteria", "completion_criteria", item.completion_criteria),
            ("Summary", "summary", item.summary),
        ):
            if value is not None and (value or key == "dependencies"):
                lines += _field_lines(label, _with_period(_file_value(key, value)))
        return lines


    def render_full(self, item: Item) -> list[str]:
        """Writes every field of the item, so that reading the entry back gives an item with the same version.

        Values the parser strips a trailing period from get one; free text is written as it is.
        """
        lines = [f"- `{item.id}` **{item.title}**", *_field_lines("Type", _with_period(item.item_type))]
        if item.parent or item.item_type != "Epic":
            lines += _field_lines("Parent", _with_period(_file_value("parent", item.parent)))
        if item.required_for_parent is not None:
            lines += _field_lines("Required for parent", "Yes." if item.required_for_parent else "No.")
        for label, value in (("Status", item.status), ("Created", item.created), ("Area", item.area),
                             ("Priority", item.priority)):
            if value:
                lines += _field_lines(label, _with_period(value))
        lines += _field_lines("Dependencies", _with_period(_file_value("dependencies", tuple(item.dependencies))))
        for label, text in (("Goal", item.goal), ("Completion criteria", item.completion_criteria),
                            ("Summary", item.summary), ("Resolution", item.resolution)):
            if text:
                lines += _field_lines(label, text)
        for label, key, names in (("Notes", "notes", item.notes), ("Spec", "spec", item.spec)):
            if names:
                paths = tuple(path_of(item.id, name) for name in names)
                lines += _field_lines(label, _with_period(_file_value(key, paths)))
        if item.deleted:
            lines += _field_lines("Deleted", _with_period(item.deleted))
        for label, text in item.extra_fields.items():
            lines += _field_lines(label, text)
        return lines

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

    def insert(self, lines: list[str], block: list[str]) -> None:
        """Adds a new entry at the end of the `## Work items` section (before a following heading)."""
        section = self._section_start(lines)
        end = next((i for i in range(section + 1, len(lines)) if lines[i].startswith("## ")), None) \
            if section is not None else None
        if section is None or end is None:
            self.append(lines, block)
            return
        for i in range(section + 1, end):
            if lines[i].strip() == NO_ENTRIES_LINE:
                del lines[i]
                end -= 1
                break
        stop = end
        while stop > section + 1 and not lines[stop - 1].strip():
            stop -= 1
        lines[stop:end] = ["", *block, ""]

    @staticmethod
    def _section_start(lines: list[str]) -> int | None:
        return next((i for i, line in enumerate(lines) if WORK_ITEMS_HEADER_RE.match(line)), None)

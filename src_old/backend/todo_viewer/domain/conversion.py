"""Turning a note into an item (promotion) and an open item back into a note (demotion).

Pure rules only: what may be demoted, what the long text of a promoted note becomes, and how documents are named
on the other side. The steps and the stores are the service's business.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence

from .documents import NotesEntry
from .editing import Field
from .errors import ConversionRefusedError
from .item import Item, Status

DEMOTE_RESOLUTION = "zur Notiz zurückgestuft"


def check_demote(item: Item, items: Sequence[Item]) -> None:
    """An item goes back to a note only while Open, without children, and when no item depends on it.

    Closed children count, they still hang on their parent. Items in the trash do not.
    """
    if item.status != Status.OPEN:
        raise ConversionRefusedError("demote_not_open", item.id)
    in_use = [i for i in items if i.deleted is None and i.id != item.id]
    children = _ids(i for i in in_use if i.parent == item.id)
    if children:
        raise ConversionRefusedError("demote_has_children", item.id, children)
    dependents = _ids(i for i in in_use if item.id in i.dependencies)
    if dependents:
        raise ConversionRefusedError("demote_referenced", item.id, dependents)


def promotion_marker(label: str) -> str:
    """The words in the heading of the notes entry that show a note's long text was taken over."""
    return f"Aus Note {label} befördert"


def promotion_entry(date: str, label: str, body: str | None) -> NotesEntry:
    """The long text of a promoted note as the first dated notes entry of the item, one bullet per line."""
    lines = [line for line in (body or "").splitlines() if line.strip()]
    return NotesEntry.create(date, promotion_marker(label), lines or [f"Note {label} ohne Langtext."], [], [])


def promotion_fields(note_summary: str, given: Mapping[str, object]) -> dict[str, object]:
    """Fields of the new item: title and summary come from the note's summary unless the caller gives them."""
    fields: dict[str, object] = {Field.TITLE: note_summary, Field.SUMMARY: note_summary}
    fields.update({name: value for name, value in given.items() if value is not None})
    return fields


def without_header(text: str) -> str:
    """A notes file without its `# <ID> — <title>` heading, so that its entries can join another notes file."""
    lines = text.lstrip("\n").splitlines(keepends=True)
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "".join(lines).strip("\n")


def renamed_document(name: str, old_label: str, new_label: str) -> str | None:
    """`<OLD>_notes.md` and `<OLD>_spec[_topic].md` under the other side's label; None for any other name."""
    base = name.rsplit("/", 1)[-1]
    if re.fullmatch(rf"{re.escape(old_label)}_(notes|spec(_[A-Za-z0-9-]+)?)\.md", base) is None:
        return None
    return new_label + base[len(old_label):]


def _ids(items: Iterable[Item]) -> tuple[str, ...]:
    return tuple(sorted(i.id for i in items))

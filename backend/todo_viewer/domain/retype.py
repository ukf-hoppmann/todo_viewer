"""Changing the type of an item: the type is the id's prefix, so the item gets a new id and every
reference to the old one inside the backlog follows."""
from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .backlog import Backlog
from .creation import TYPES, ItemFactory
from .editing import ChangeSet, Field, FieldValue
from .errors import InvalidValueError, LifecycleViolationError
from .item import Item

# Free text fields that may mention another item by id.
TEXT_FIELDS = (Field.TITLE, Field.SUMMARY, Field.GOAL, Field.COMPLETION_CRITERIA, Field.RESOLUTION)


def rewrite_ids(text: str, old: str, new: str) -> str:
    """Replaces `old` where it stands as an id of its own, also in names like `<ID>_notes.md`.

    Longer ids that merely start with it (STORY-0081, STORY-008-b) stay untouched.
    """
    pattern = rf"(?<![A-Za-z0-9_-]){re.escape(old)}(?![A-Za-z0-9-])(?!\.[A-Za-z0-9])(?!_(?!notes|spec))"
    return re.sub(pattern, new, text)


@dataclass(frozen=True)
class Notice:
    """Something the caller should know after a successful change. `code` is stable, `message` is English."""

    code: str
    message: str
    details: dict[str, str]


@dataclass(frozen=True)
class RetypePlan:
    new_id: str
    # Items whose stored entry changes (the item itself and everything that mentions it), in backlog order.
    changes: tuple[tuple[Item, ChangeSet], ...]
    # File names inside the item's folder: old name -> new name.
    file_renames: dict[str, str]
    # Every notes/spec document of the backlog: path before -> path after the retype.
    document_paths: dict[str, str]
    notices: tuple[Notice, ...]


class RetypePlanner:
    def plan(self, items: Sequence[Item], item_id: str, new_type: str) -> RetypePlan:
        item = Backlog(items=list(items)).find(item_id)
        if new_type not in TYPES or new_type == item.item_type:
            raise InvalidValueError("type", tuple(t for t in TYPES if t != item.item_type))
        if item.deleted:
            raise LifecycleViolationError("item_deleted", item_id)
        new_id = ItemFactory.next_id(new_type, items)
        old_folder, new_folder = f"items/{item_id}/", f"items/{new_id}/"

        def moved(path: str) -> str:
            if not path.startswith(old_folder):
                return path
            return new_folder + rewrite_ids(path[len(old_folder):], item_id, new_id)

        changes: list[tuple[Item, ChangeSet]] = []
        for other in items:
            fields: list[tuple[str, FieldValue]] = []
            if other is item:
                fields += [(Field.ID, new_id), (Field.TYPE, new_type)]
                for key, paths in ((Field.NOTES, other.notes), (Field.SPEC, other.spec)):
                    if any(moved(p) != p for p in paths):
                        fields.append((key, tuple(moved(p) for p in paths)))
            if other.parent == item_id:
                fields.append((Field.PARENT, new_id))
            if item_id in other.dependencies:
                fields.append((Field.DEPENDENCIES, tuple(new_id if d == item_id else d for d in other.dependencies)))
            for key in TEXT_FIELDS:
                text = getattr(other, key)
                if text and (rewritten := rewrite_ids(text, item_id, new_id)) != text:
                    fields.append((key, rewritten))
            if fields:
                changes.append((other, ChangeSet(set_fields=tuple(fields))))

        paths = [p for i in items for p in (*i.notes, *i.spec)]
        return RetypePlan(
            new_id=new_id,
            changes=tuple(changes),
            file_renames={_name(p): _name(moved(p)) for p in (*item.notes, *item.spec) if moved(p) != p},
            document_paths={p: moved(p) for p in paths},
            notices=(_external_references(item_id, new_id),),
        )


def _external_references(old_id: str, new_id: str) -> Notice:
    return Notice(
        code="external_references_may_remain",
        message=(f"References to {old_id} outside the backlog (technical docs, daily reports, code, commit "
                 f"messages) are not updated. Search for {old_id} and adapt where it is now {new_id}."),
        details={"old_id": old_id, "new_id": new_id},
    )


def _name(path: str) -> str:
    return path.rsplit("/", 1)[-1]

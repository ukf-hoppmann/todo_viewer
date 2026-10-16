from __future__ import annotations

import pytest

from todo_viewer.domain.creation import ItemFactory
from todo_viewer.domain.errors import InvalidValueError, NotEditableError, ValueRequiredError
from todo_viewer.domain.item import Item, Location

factory = ItemFactory()
FIELDS = {"title": "New  story", "area": "Core", "goal": "Reach it.", "completion_criteria": "Checked."}


def existing(*ids: str) -> list[Item]:
    return [Item(id=i, title=i, project="p", location=Location.ARCHIVE if i.endswith("9") else Location.ACTIVE)
            for i in ids]


def test_next_free_id_per_type_across_active_and_archive():
    items = existing("STORY-001", "STORY-009", "TASK-012", "EPIC-001", "STORY-X")

    assert factory.create("Story", FIELDS, items, "p", "2026-09-28").id == "STORY-010"
    assert factory.create("Task", FIELDS, items, "p", "2026-09-28").id == "TASK-013"
    assert factory.create("Epic", FIELDS, [], "p", "2026-09-28").id == "EPIC-001"


def test_new_item_defaults():
    item = factory.create("Story", FIELDS, [], "p", "2026-09-28")

    assert (item.title, item.item_type, item.status, item.created, item.priority, item.location) == \
        ("New story", "Story", "Open", "2026-09-28", "Normal", Location.ACTIVE)
    assert (item.parent, item.required_for_parent, item.dependencies, item.summary) == (None, None, [], None)


def test_optional_fields():
    item = factory.create("Task", {**FIELDS, "parent": "STORY-001", "required_for_parent": "No",
                                   "dependencies": ["TASK-001"], "priority": "Urgent", "summary": "Short.",
                                   "created": "2026-01-01"}, [], "p", "2026-09-28")

    assert (item.parent, item.required_for_parent, item.dependencies, item.priority, item.summary, item.created) \
        == ("STORY-001", False, ["TASK-001"], "Urgent", "Short.", "2026-01-01")


def test_validation():
    with pytest.raises(InvalidValueError):
        factory.create("Bug", FIELDS, [], "p", "2026-09-28")
    for field in ("title", "area", "goal", "completion_criteria"):
        with pytest.raises(ValueRequiredError):
            factory.create("Task", {k: v for k, v in FIELDS.items() if k != field}, [], "p", "2026-09-28")
    with pytest.raises(NotEditableError):
        factory.create("Task", {**FIELDS, "status": "Completed"}, [], "p", "2026-09-28")
    with pytest.raises(InvalidValueError):
        factory.create("Task", {**FIELDS, "created": "yesterday"}, [], "p", "2026-09-28")

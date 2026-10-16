from __future__ import annotations

import dataclasses

import pytest

from todo_viewer.domain.item import Item, Location


def _item(**overrides: object) -> Item:
    return dataclasses.replace(Item(id="T-1", title="t", project="p", dependencies=["A"]), **overrides)


def test_version_is_stable_for_equal_items():
    assert _item().version == _item().version
    assert len(_item().version) == 16


@pytest.mark.parametrize("change", [
    {"title": "other"}, {"status": "Completed"}, {"priority": "Urgent"}, {"required_for_parent": True},
    {"dependencies": ["A", "B"]}, {"goal": "g"}, {"resolution": "r"}, {"notes": ["n.md"]},
    {"extra_fields": {"X": "y"}}, {"location": Location.ARCHIVE},
])
def test_version_changes_with_every_field(change):
    assert _item(**change).version != _item().version


def test_version_ignores_the_source_display_name():
    assert _item(project="renamed").version == _item().version

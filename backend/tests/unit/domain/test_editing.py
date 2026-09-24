from __future__ import annotations

import pytest

from todo_viewer.domain.editing import ChangeSet, EditPlanner
from todo_viewer.domain.errors import (
    CheckboxStatusOnlyError,
    InvalidValueError,
    NotEditableError,
    ResolutionRequiredError,
)
from todo_viewer.domain.item import Item, ItemFormat, Location


def _item(fmt: ItemFormat = ItemFormat.BACKLOG_V2, location: Location = Location.ACTIVE) -> Item:
    return Item(id="T-1", title="t", source_file="f", project="p", line=1, format=fmt, location=location)


planner = EditPlanner()


def test_rejects_non_editable_field():
    with pytest.raises(NotEditableError):
        planner.plan(_item(), "title", "x", None, archive_supported=True)


def test_checkbox_allows_only_status():
    with pytest.raises(CheckboxStatusOnlyError):
        planner.plan(_item(ItemFormat.CHECKBOX), "priority", "Urgent", None, archive_supported=False)
    assert planner.plan(_item(ItemFormat.CHECKBOX), "status", "Completed", None, archive_supported=False) == \
        ChangeSet(set_fields=(("status", "Completed"),))


def test_priority_is_a_plain_field_change():
    assert planner.plan(_item(), "priority", "Urgent", None, archive_supported=True) == \
        ChangeSet(set_fields=(("priority", "Urgent"),))


def test_required_for_parent_accepts_only_yes_or_no():
    assert planner.plan(_item(), "required_for_parent", "No", None, archive_supported=True) == \
        ChangeSet(set_fields=(("required_for_parent", "No"),))
    with pytest.raises(InvalidValueError):
        planner.plan(_item(), "required_for_parent", "true", None, archive_supported=True)


def test_terminal_status_without_archive_is_a_plain_change():
    assert planner.plan(_item(), "status", "Completed", None, archive_supported=False) == \
        ChangeSet(set_fields=(("status", "Completed"),))


@pytest.mark.parametrize("resolution", [None, "", "   "])
def test_terminal_status_requires_resolution(resolution):
    with pytest.raises(ResolutionRequiredError):
        planner.plan(_item(), "status", "Rejected", resolution, archive_supported=True)


def test_terminal_status_archives_active_item():
    assert planner.plan(_item(), "status", "Completed", "Done", archive_supported=True) == ChangeSet(
        set_fields=(("status", "Completed"), ("resolution", "Done")), move_to=Location.ARCHIVE)


def test_terminal_status_in_archive_stays():
    assert planner.plan(_item(location=Location.ARCHIVE), "status", "Rejected", "No", archive_supported=True) == \
        ChangeSet(set_fields=(("status", "Rejected"), ("resolution", "No")))


def test_active_status_restores_archived_item():
    assert planner.plan(_item(location=Location.ARCHIVE), "status", "Open", None, archive_supported=True) == \
        ChangeSet(set_fields=(("status", "Open"),), remove_fields=("resolution",), move_to=Location.ACTIVE)


def test_active_status_on_active_item_drops_resolution():
    assert planner.plan(_item(), "status", "In progress", "ignored", archive_supported=True) == \
        ChangeSet(set_fields=(("status", "In progress"),), remove_fields=("resolution",))

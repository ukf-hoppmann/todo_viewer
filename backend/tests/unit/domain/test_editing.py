from __future__ import annotations

import pytest

from todo_viewer.domain.editing import ChangeSet, EditPlanner
from todo_viewer.domain.errors import InvalidValueError, NotEditableError, ResolutionRequiredError
from todo_viewer.domain.item import Item, Location


def _item(location: Location = Location.ACTIVE) -> Item:
    return Item(id="T-1", title="t", project="p", location=location)


planner = EditPlanner()


def test_rejects_non_editable_field():
    with pytest.raises(NotEditableError):
        planner.plan(_item(), "title", "x", None, archive_supported=True)


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


def test_change_set_applied_to_item():
    archived = ChangeSet(set_fields=(("status", "Completed"), ("resolution", "Done"), ("required_for_parent", "No")),
                         move_to=Location.ARCHIVE).applied_to(_item())
    reopened = ChangeSet(set_fields=(("status", "Open"),), remove_fields=("resolution",),
                         move_to=Location.ACTIVE).applied_to(archived)

    assert (archived.status, archived.resolution, archived.required_for_parent, archived.location) == \
        ("Completed", "Done", False, Location.ARCHIVE)
    assert (reopened.status, reopened.resolution, reopened.location) == ("Open", None, Location.ACTIVE)

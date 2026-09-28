from __future__ import annotations

import pytest

from todo_viewer.domain.editing import ChangeSet, EditPlanner
from todo_viewer.domain.errors import (
    InvalidValueError,
    NotEditableError,
    ResolutionRequiredError,
    ValueRequiredError,
)
from todo_viewer.domain.item import Item, Location


def _item(location: Location = Location.ACTIVE, **fields: object) -> Item:
    return Item(id="T-1", title="t", project="p", location=location, **fields)  # type: ignore[arg-type]


planner = EditPlanner()


def plan(changes: dict, resolution: str | None = None, archive: bool = True, item: Item | None = None) -> ChangeSet:
    return planner.plan(item or _item(), changes, resolution, archive_supported=archive)


def test_rejects_non_editable_field_and_empty_request():
    with pytest.raises(NotEditableError):
        plan({"created": "2026-01-01"})
    with pytest.raises(NotEditableError):
        plan({})


def test_priority_is_a_plain_field_change():
    assert plan({"priority": "Urgent"}) == ChangeSet(set_fields=(("priority", "Urgent"),))


def test_required_for_parent_accepts_only_yes_or_no():
    assert plan({"required_for_parent": "No"}) == ChangeSet(set_fields=(("required_for_parent", "No"),))
    with pytest.raises(InvalidValueError):
        plan({"required_for_parent": "true"})


def test_terminal_status_without_archive_is_a_plain_change():
    assert plan({"status": "Completed"}, archive=False) == ChangeSet(set_fields=(("status", "Completed"),))


@pytest.mark.parametrize("resolution", [None, "", "   "])
def test_terminal_status_requires_resolution(resolution):
    with pytest.raises(ResolutionRequiredError):
        plan({"status": "Rejected"}, resolution)


def test_terminal_status_archives_active_item():
    assert plan({"status": "Completed"}, "Done") == ChangeSet(
        set_fields=(("status", "Completed"), ("resolution", "Done")), move_to=Location.ARCHIVE)


def test_terminal_status_in_archive_stays():
    assert plan({"status": "Rejected"}, "No", item=_item(Location.ARCHIVE)) == \
        ChangeSet(set_fields=(("status", "Rejected"), ("resolution", "No")))


def test_active_status_restores_archived_item():
    assert plan({"status": "Open"}, item=_item(Location.ARCHIVE)) == \
        ChangeSet(set_fields=(("status", "Open"),), remove_fields=("resolution",), move_to=Location.ACTIVE)


def test_active_status_on_active_item_drops_resolution():
    assert plan({"status": "In progress"}, "ignored") == \
        ChangeSet(set_fields=(("status", "In progress"),), remove_fields=("resolution",))


# ---------- free fields ----------

def test_text_fields_are_trimmed_and_joined_to_one_line():
    changes = plan({"title": "  New  title ", "goal": "Line one\n  line two", "area": "Core",
                    "completion_criteria": "Done.", "summary": "Short."})

    assert changes == ChangeSet(set_fields=(
        ("title", "New title"), ("goal", "Line one line two"), ("area", "Core"),
        ("completion_criteria", "Done."), ("summary", "Short."),
    ))


@pytest.mark.parametrize("field", ["title", "goal", "completion_criteria", "area"])
@pytest.mark.parametrize("value", [None, "", "   "])
def test_required_text_fields_cannot_be_emptied(field, value):
    with pytest.raises(ValueRequiredError) as err:
        plan({field: value})
    assert err.value.details == {"field": field}


@pytest.mark.parametrize("value", [None, "  "])
def test_empty_summary_removes_the_field(value):
    assert plan({"summary": value}) == ChangeSet(remove_fields=("summary",))


def test_title_must_not_break_the_entry_header():
    with pytest.raises(InvalidValueError):
        plan({"title": "Bold **inside**"})


def test_parent_and_dependencies_are_ids():
    assert plan({"parent": "S-1", "required_for_parent": "Yes", "dependencies": ["A-1", " B-2 ", "A-1"]}) == \
        ChangeSet(set_fields=(("parent", "S-1"), ("required_for_parent", "Yes"), ("dependencies", ("A-1", "B-2"))))
    assert plan({"dependencies": []}) == ChangeSet(set_fields=(("dependencies", ()),))
    with pytest.raises(InvalidValueError):
        plan({"parent": "not an id"})
    with pytest.raises(InvalidValueError):
        plan({"dependencies": ["ok", "no`pe"]})


def test_removing_the_parent_also_removes_required_for_parent():
    item = _item(parent="S-1", required_for_parent=True)

    assert plan({"parent": None}, item=item) == \
        ChangeSet(set_fields=(("parent", None),), remove_fields=("required_for_parent",))


def test_status_and_other_fields_in_one_change():
    assert plan({"priority": "Urgent", "status": "Completed"}, "Done") == ChangeSet(
        set_fields=(("priority", "Urgent"), ("status", "Completed"), ("resolution", "Done")),
        move_to=Location.ARCHIVE)


def test_change_set_applied_to_item():
    archived = ChangeSet(set_fields=(("status", "Completed"), ("resolution", "Done"), ("required_for_parent", "No"),
                                     ("dependencies", ("A", "B")), ("parent", "S")),
                         move_to=Location.ARCHIVE).applied_to(_item())
    reopened = ChangeSet(set_fields=(("status", "Open"), ("parent", None)), remove_fields=("resolution",),
                         move_to=Location.ACTIVE).applied_to(archived)

    assert (archived.status, archived.resolution, archived.required_for_parent, archived.location) == \
        ("Completed", "Done", False, Location.ARCHIVE)
    assert (archived.dependencies, archived.parent) == (["A", "B"], "S")
    assert (reopened.status, reopened.resolution, reopened.location, reopened.parent) == \
        ("Open", None, Location.ACTIVE, None)

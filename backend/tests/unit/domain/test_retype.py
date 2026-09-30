from __future__ import annotations

import pytest

from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import InvalidValueError, LifecycleViolationError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.retype import RetypePlanner, rewrite_ids

planner = RetypePlanner()


def item(item_id: str, item_type: str = "Task", parent: str | None = None, dependencies: tuple[str, ...] = (),
         **fields) -> Item:
    fields.setdefault("title", "Titel")
    return Item(id=item_id, project="p", item_type=item_type, parent=parent,
                required_for_parent=True if parent else None, dependencies=list(dependencies), **fields)


def changes_of(plan, item_id: str) -> ChangeSet:
    return next(c for i, c in plan.changes if i.id == item_id)


# ---------- rewrite_ids ----------

@pytest.mark.parametrize("text, expected", [
    ("`STORY-008` und STORY-008.", "`TASK-003` und TASK-003."),
    ("siehe STORY-008, STORY-008;", "siehe TASK-003, TASK-003;"),
    ("items/STORY-008/STORY-008_notes.md", "items/TASK-003/TASK-003_notes.md"),
    ("STORY-008_spec.md und STORY-008_spec_api.md", "TASK-003_spec.md und TASK-003_spec_api.md"),
    ("STORY-0081", "STORY-0081"),
    ("STORY-0080 STORY-0008", "STORY-0080 STORY-0008"),
    ("XSTORY-008 und MY_STORY-008", "XSTORY-008 und MY_STORY-008"),
    ("STORY-008-b und STORY-008_x", "STORY-008-b und STORY-008_x"),
    ("STORY-008.md", "STORY-008.md"),
    ("kein Treffer", "kein Treffer"),
])
def test_rewrite_ids_replaces_whole_tokens_only(text, expected):
    assert rewrite_ids(text, "STORY-008", "TASK-003") == expected


# ---------- plan ----------

def test_new_id_is_next_free_number_of_the_target_type_over_all_items():
    items = [item("STORY-008", "Story"), item("TASK-001"), item("TASK-004", location=Location.ARCHIVE),
             item("TASK-009", deleted="2026-09-01")]

    plan = planner.plan(items, "STORY-008", "Task")

    assert plan.new_id == "TASK-010"


def test_item_gets_new_id_and_type():
    plan = planner.plan([item("STORY-008", "Story")], "STORY-008", "Task")

    assert [(i.id, c) for i, c in plan.changes] == [
        ("STORY-008", ChangeSet(set_fields=(("id", "TASK-001"), ("type", "Task"))))]
    assert changes_of(plan, "STORY-008").applied_to(item("STORY-008", "Story")).id == "TASK-001"
    assert changes_of(plan, "STORY-008").applied_to(item("STORY-008", "Story")).item_type == "Task"


def test_parent_and_dependencies_of_other_items_follow():
    items = [item("STORY-008", "Story"), item("TASK-001", parent="STORY-008"),
             item("TASK-002", dependencies=("X-1", "STORY-008")), item("TASK-003", dependencies=("X-1",)),
             item("TASK-004", parent="STORY-008", location=Location.ARCHIVE, status="Completed"),
             item("TASK-005", parent="STORY-008", deleted="2026-09-01", location=Location.ARCHIVE)]

    plan = planner.plan(items, "STORY-008", "Task")

    assert changes_of(plan, "TASK-001") == ChangeSet(set_fields=(("parent", "TASK-006"),))
    assert changes_of(plan, "TASK-002") == ChangeSet(set_fields=(("dependencies", ("X-1", "TASK-006")),))
    assert changes_of(plan, "TASK-004") == ChangeSet(set_fields=(("parent", "TASK-006"),))
    assert changes_of(plan, "TASK-005") == ChangeSet(set_fields=(("parent", "TASK-006"),))
    assert {i.id for i, _ in plan.changes} == {"STORY-008", "TASK-001", "TASK-002", "TASK-004", "TASK-005"}


def test_text_fields_mentioning_the_old_id_follow():
    items = [item("STORY-008", "Story"),
             item("TASK-001", title="Folgt STORY-008", goal="Wie in STORY-008.", summary="Siehe `STORY-008`.",
                  completion_criteria="STORY-008 ist fertig.", resolution="Nach STORY-008 bestätigt."),
             item("TASK-002", goal="unabhängig")]

    plan = planner.plan(items, "STORY-008", "Task")

    assert dict(changes_of(plan, "TASK-001").set_fields) == {
        "title": "Folgt TASK-003", "goal": "Wie in TASK-003.", "summary": "Siehe `TASK-003`.",
        "completion_criteria": "TASK-003 ist fertig.", "resolution": "Nach TASK-003 bestätigt."}
    assert "TASK-002" not in {i.id for i, _ in plan.changes}


def test_documents_of_the_item_move_with_it_and_others_keep_their_paths():
    own = item("STORY-008", "Story", notes=["items/STORY-008/STORY-008_notes.md"],
               spec=["items/STORY-008/STORY-008_spec.md", "items/STORY-008/STORY-008_spec_api.md"])
    other = item("TASK-001", notes=["items/TASK-001/TASK-001_notes.md"])

    plan = planner.plan([own, other], "STORY-008", "Task")

    assert dict(changes_of(plan, "STORY-008").set_fields)["notes"] == ("items/TASK-002/TASK-002_notes.md",)
    assert dict(changes_of(plan, "STORY-008").set_fields)["spec"] == (
        "items/TASK-002/TASK-002_spec.md", "items/TASK-002/TASK-002_spec_api.md")
    assert plan.file_renames == {"STORY-008_notes.md": "TASK-002_notes.md",
                                 "STORY-008_spec.md": "TASK-002_spec.md",
                                 "STORY-008_spec_api.md": "TASK-002_spec_api.md"}
    assert plan.document_paths == {
        "items/STORY-008/STORY-008_notes.md": "items/TASK-002/TASK-002_notes.md",
        "items/STORY-008/STORY-008_spec.md": "items/TASK-002/TASK-002_spec.md",
        "items/STORY-008/STORY-008_spec_api.md": "items/TASK-002/TASK-002_spec_api.md",
        "items/TASK-001/TASK-001_notes.md": "items/TASK-001/TASK-001_notes.md"}


def test_item_without_documents_has_nothing_to_rename():
    plan = planner.plan([item("STORY-008", "Story")], "STORY-008", "Task")

    assert plan.file_renames == {}
    assert plan.document_paths == {}


def test_documents_outside_the_item_folder_keep_their_path():
    own = item("STORY-008", "Story", notes=["notes/alt.md"])

    plan = planner.plan([own], "STORY-008", "Task")

    assert "notes" not in dict(changes_of(plan, "STORY-008").set_fields)
    assert plan.document_paths == {"notes/alt.md": "notes/alt.md"}


# ---------- refusals ----------

def test_same_type_is_refused():
    with pytest.raises(InvalidValueError) as err:
        planner.plan([item("STORY-008", "Story")], "STORY-008", "Story")

    assert err.value.details == {"field": "type"}


def test_unknown_type_is_refused():
    with pytest.raises(InvalidValueError):
        planner.plan([item("STORY-008", "Story")], "STORY-008", "Bug")


def test_item_in_the_trash_is_refused():
    with pytest.raises(LifecycleViolationError) as err:
        planner.plan([item("STORY-008", "Story", deleted="2026-09-01")], "STORY-008", "Task")

    assert err.value.code == "item_deleted"


# ---------- notices ----------

def test_plan_warns_about_references_outside_the_backlog():
    plan = planner.plan([item("STORY-008", "Story")], "STORY-008", "Task")

    (notice,) = plan.notices
    assert (notice.code, notice.details) == ("external_references_may_remain",
                                             {"old_id": "STORY-008", "new_id": "TASK-001"})
    assert "STORY-008" in notice.message and "TASK-001" in notice.message
    assert "outside the backlog" in notice.message

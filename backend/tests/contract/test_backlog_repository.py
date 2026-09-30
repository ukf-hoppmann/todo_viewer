"""Contract of `BacklogRepository`: what every storage adapter has to do the same way."""
from __future__ import annotations

import dataclasses

import pytest

from tests.contract.conftest import Adapter
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import DuplicateItemError, ItemNotFoundError, VersionConflictError
from todo_viewer.domain.item import Item, Location


def test_get_finds_items_in_the_active_list_and_the_archive(adapter: Adapter):
    assert adapter.repo.get(adapter.source, "TASK-001").location is Location.ACTIVE
    assert adapter.repo.get(adapter.source, "TASK-000").location is Location.ARCHIVE
    with pytest.raises(ItemNotFoundError):
        adapter.repo.get(adapter.source, "NOT-AN-ENTRY")


def test_apply_rejects_an_item_changed_in_the_meantime(adapter: Adapter):
    item = adapter.repo.get(adapter.source, "TASK-001")
    adapter.repo.apply(adapter.source, item, ChangeSet(set_fields=(("priority", "Urgent"),)))

    with pytest.raises(VersionConflictError):
        adapter.repo.apply(adapter.source, item, ChangeSet(set_fields=(("priority", "Normal"),)))

    assert adapter.repo.get(adapter.source, "TASK-001").priority == "Urgent"


def test_apply_moves_an_item_and_returns_it_at_its_new_place(adapter: Adapter):
    item = adapter.repo.get(adapter.source, "TASK-001")

    moved = adapter.repo.apply(adapter.source, item, ChangeSet(
        set_fields=(("status", "Completed"), ("resolution", "ok")), move_to=Location.ARCHIVE))

    assert (moved.location, moved.status) == (Location.ARCHIVE, "Completed")
    assert (moved.resolution or "").startswith("ok")
    assert adapter.repo.get(adapter.source, "TASK-001").location is Location.ARCHIVE


def test_create_stores_an_active_item_and_refuses_taken_ids(adapter: Adapter):
    new = Item(id="TASK-004", title="Created", project="P", item_type="Task", parent="STORY-001",
               required_for_parent=True, created="2026-09-28", area="Core", priority="Normal",
               goal="A goal.", completion_criteria="Checked.", dependencies=["TASK-001"])

    created = adapter.repo.create(adapter.source, new)

    assert created == new
    assert adapter.repo.get(adapter.source, "TASK-004") == new
    with pytest.raises(DuplicateItemError):
        adapter.repo.create(adapter.source, Item(id="TASK-000", title="Taken in the archive", project="P",
                                                 area="a", goal="g", completion_criteria="c"))


def test_delete_removes_active_and_archived_items_but_not_stale_ones(adapter: Adapter):
    repo, source = adapter.repo, adapter.source
    # Only items nobody refers to are deleted (the lifecycle rules ensure that): TASK-001 lets go of STORY-000.
    repo.apply(source, repo.get(source, "TASK-001"), ChangeSet(set_fields=(("dependencies", ("TASK-000",)),)))
    active, archived = repo.get(source, "TASK-002"), repo.get(source, "STORY-000")
    stale = repo.get(source, "TASK-003")
    repo.apply(source, stale, ChangeSet(set_fields=(("priority", "Urgent"),)))

    repo.delete(source, [active, archived])
    with pytest.raises(VersionConflictError):
        repo.delete(source, [stale])

    ids = {i.id for i in repo.load(source).items}
    assert "TASK-002" not in ids and "STORY-000" not in ids and "TASK-003" in ids


def test_apply_all_changes_and_moves_several_items(adapter: Adapter):
    repo, source = adapter.repo, adapter.source
    task, done = repo.get(source, "TASK-003"), repo.get(source, "TASK-000")
    mark = ChangeSet(set_fields=(("deleted", "2026-09-28"),))

    changed = repo.apply_all(source, [(task, dataclasses.replace(mark, move_to=Location.ARCHIVE)), (done, mark)])

    assert [(i.id, i.deleted, i.location) for i in changed] == [
        ("TASK-003", "2026-09-28", Location.ARCHIVE), ("TASK-000", "2026-09-28", Location.ARCHIVE)]
    assert repo.get(source, "TASK-003").location is Location.ARCHIVE
    assert repo.get(source, "TASK-000").deleted == "2026-09-28"


def test_apply_all_changes_nothing_when_one_item_is_stale(adapter: Adapter):
    repo, source = adapter.repo, adapter.source
    task, other = repo.get(source, "TASK-003"), repo.get(source, "TASK-001")
    repo.apply(source, other, ChangeSet(set_fields=(("priority", "Urgent"),)))
    mark = ChangeSet(set_fields=(("deleted", "2026-09-28"),))

    with pytest.raises(VersionConflictError):
        repo.apply_all(source, [(task, mark), (other, mark)])

    assert repo.get(source, "TASK-003").deleted is None


def test_a_usable_backlog_has_no_problem_and_an_archive(adapter: Adapter):
    assert adapter.repo.check(adapter.source) is None
    assert adapter.repo.archive_available(adapter.source)
    assert adapter.repo.load(adapter.source).problem is None


def test_items_list_their_documents_by_name(adapter: Adapter):
    item = adapter.repo.get(adapter.source, "TASK-002")

    assert (item.notes, item.spec) == (["notes.md"], ["spec.md", "extra.md"])


def test_documents_stay_listed_when_the_id_changes(adapter: Adapter):
    item = adapter.repo.get(adapter.source, "TASK-002")

    adapter.repo.apply(adapter.source, item, ChangeSet(set_fields=(("id", "STORY-009"), ("type", "Story"))))

    moved = adapter.repo.get(adapter.source, "STORY-009")
    assert (moved.notes, moved.spec) == (["notes.md"], ["spec.md", "extra.md"])

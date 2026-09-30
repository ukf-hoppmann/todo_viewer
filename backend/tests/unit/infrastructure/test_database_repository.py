"""Database-specific behavior of the backlog repository; the shared behavior is in tests/contract."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import BacklogExistsError, LifecycleViolationError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.repository import DatabaseBacklogRepository
from todo_viewer.infrastructure.markdown import build_markdown_repository

FIXTURE = Path(__file__).parents[2] / "fixtures" / "backlog"
SOURCE = Source(project="P", path="", backend="database", id="0b6c1f52-0000-4000-8000-000000000001")


@pytest.fixture
def repo(tmp_path: Path) -> DatabaseBacklogRepository:
    return DatabaseBacklogRepository(Database(f"sqlite:///{tmp_path / 'todo.db'}"))


def _fixture_items() -> list[Item]:
    return build_markdown_repository(Path("/")).load(Source(project="P", path=str(FIXTURE))).items


def test_a_stored_backlog_is_loaded_unchanged(repo: DatabaseBacklogRepository):
    items = _fixture_items()

    repo.store_all(SOURCE, items)
    loaded = repo.load(SOURCE)

    assert loaded.problem is None and loaded.archive_available
    assert loaded.items == items
    assert [i.version for i in loaded.items] == [i.version for i in items]


def test_every_field_survives_storing(repo: DatabaseBacklogRepository):
    parent = Item(id="STORY-001", title="Parent", project="P", item_type="Story")
    full = Item(id="TASK-001", title="All fields", project="P", status="Completed", parent="STORY-001",
                required_for_parent=False, dependencies=["STORY-001", "TASK-002"], created="2026-09-30", area="Core",
                priority="Urgent", goal="Goal", completion_criteria="Criteria", summary="Summary",
                resolution="Done.", notes=["TASK-001_notes.md"], spec=["TASK-001_spec.md", "docs/extra.md"],
                extra_fields={"Implementation": "x", "Verification": "y"}, location=Location.ARCHIVE,
                deleted="2026-09-30")
    other = Item(id="TASK-002", title="Other", project="P")

    repo.store_all(SOURCE, [parent, full, other])

    assert repo.get(SOURCE, "TASK-001") == full


def test_projects_are_kept_apart(repo: DatabaseBacklogRepository):
    repo.store_all(SOURCE, [Item(id="TASK-001", title="Mine", project="P")])
    other = dataclasses.replace(SOURCE, id="0b6c1f52-0000-4000-8000-000000000002")

    repo.store_all(other, [Item(id="TASK-001", title="Theirs", project="Q")])

    assert [i.title for i in repo.load(SOURCE).items] == ["Mine"]
    assert [(i.title, i.project) for i in repo.load(other).items] == [("Theirs", "P")]


def test_storing_again_replaces_the_backlog(repo: DatabaseBacklogRepository):
    repo.store_all(SOURCE, _fixture_items())

    repo.store_all(SOURCE, [Item(id="TASK-009", title="Only one", project="P")])

    assert [i.id for i in repo.load(SOURCE).items] == ["TASK-009"]


def test_references_to_unknown_items_are_refused(repo: DatabaseBacklogRepository):
    with pytest.raises(LifecycleViolationError) as err:
        repo.store_all(SOURCE, [Item(id="TASK-001", title="t", project="P", parent="STORY-404")])

    assert (err.value.code, err.value.details["items"]) == ("unknown_reference", "STORY-404")
    assert repo.load(SOURCE).items == []


def test_an_unknown_project_is_an_empty_backlog(repo: DatabaseBacklogRepository):
    assert repo.check(SOURCE) is None
    assert repo.load(SOURCE).items == []


def test_an_unreachable_database_is_reported_as_a_problem(tmp_path: Path):
    repo = DatabaseBacklogRepository(Database(f"sqlite:///{tmp_path / 'missing' / 'todo.db'}"))

    assert repo.check(SOURCE).code == "db_unavailable"
    assert repo.load(SOURCE).problem.code == "db_unavailable"


def test_a_change_with_an_unknown_reference_writes_nothing(repo: DatabaseBacklogRepository):
    repo.store_all(SOURCE, _fixture_items())
    task, other = repo.get(SOURCE, "TASK-001"), repo.get(SOURCE, "TASK-003")

    with pytest.raises(LifecycleViolationError) as err:
        repo.apply_all(SOURCE, [(task, ChangeSet(set_fields=(("priority", "Urgent"),))),
                                (other, ChangeSet(set_fields=(("parent", "STORY-404"),)))])

    assert err.value.code == "unknown_reference"
    assert repo.get(SOURCE, "TASK-001").priority == "Important"


def test_deleting_an_item_others_refer_to_is_refused(repo: DatabaseBacklogRepository):
    repo.store_all(SOURCE, _fixture_items())

    with pytest.raises(LifecycleViolationError) as err:
        repo.delete(SOURCE, [repo.get(SOURCE, "STORY-001")])

    assert err.value.code == "item_referenced"
    assert repo.get(SOURCE, "STORY-001").title == "Parse backlog files"


def test_an_item_and_its_children_can_be_deleted_together(repo: DatabaseBacklogRepository):
    story = Item(id="STORY-001", title="s", project="P", item_type="Story")
    task = Item(id="TASK-001", title="t", project="P", parent="STORY-001", required_for_parent=True)
    repo.store_all(SOURCE, [story, task])

    repo.delete(SOURCE, [story, task])

    assert repo.load(SOURCE).items == []


def test_a_new_id_keeps_the_references_of_other_items(repo: DatabaseBacklogRepository):
    repo.store_all(SOURCE, _fixture_items())
    story = repo.get(SOURCE, "STORY-001")
    children = [i for i in repo.load(SOURCE).items if i.parent == "STORY-001"]

    repo.apply_all(SOURCE, [(story, ChangeSet(set_fields=(("id", "TASK-009"), ("type", "Task")))),
                            *[(c, ChangeSet(set_fields=(("parent", "TASK-009"),))) for c in children]])

    assert {i.id for i in repo.load(SOURCE).items if i.parent == "TASK-009"} == {c.id for c in children}


def test_initialize_creates_an_empty_project_once(repo: DatabaseBacklogRepository):
    repo.initialize(SOURCE, "de")

    assert repo.load(SOURCE).items == []
    with pytest.raises(BacklogExistsError):
        repo.initialize(SOURCE, "de")

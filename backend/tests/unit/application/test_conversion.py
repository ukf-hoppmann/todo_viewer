"""ConversionService: a note becomes an item and an open item goes back to a note.

Notes live in a real SQLite file (the adapter has its own contract suite), items and their documents in the
in-memory fakes. A failing step is simulated by a wrapper that raises once.
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from tests.fakes import InMemoryBacklogRepository, InMemoryDocumentStore
from todo_viewer.application.services import (
    DocumentService,
    ItemService,
    NoteDocumentService,
    NoteService,
)
from todo_viewer.application.services.conversion import ConversionService
from todo_viewer.domain.creation import ItemFactory
from todo_viewer.domain.documents import DocumentKind
from todo_viewer.domain.editing import EditPlanner
from todo_viewer.domain.errors import (
    ConversionRefusedError,
    LifecycleViolationError,
    NoteLifecycleError,
    ValueRequiredError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Status
from todo_viewer.domain.lifecycle import LifecycleRules
from todo_viewer.domain.notes import LinkRole, LinkTarget, NoteStatus, NoticeSide, TargetKind
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.notes import DatabaseNoteDocumentStore, DatabaseNoteRepository

P = "proj"
SOURCE = Source(project=P, path="", backend="database", id="s1")
NOW = datetime(2027, 12, 11, 9, 0, tzinfo=UTC)
FIELDS = {"area": "Core", "goal": "A goal.", "completion_criteria": "Checked."}


class Sources:
    def all(self) -> list[Source]:
        return [SOURCE]


class Flaky:
    """Wraps an object; the named method raises once when told to, then works again."""

    def __init__(self, inner):
        self._inner = inner
        self.fail_next: str | None = None

    def __getattr__(self, name):
        target = getattr(self._inner, name)
        if name != self.fail_next:
            return target

        def failing(*args, **kwargs):
            self.fail_next = None
            raise RuntimeError(f"{name} failed")
        return failing


class World:
    def __init__(self, tmp_path: Path, items: list[Item] | None = None):
        database = Database(f"sqlite:///{tmp_path / 'todo.db'}")
        self.notes_repo = DatabaseNoteRepository(database, lambda: NOW)
        self.backlogs = InMemoryBacklogRepository(items or [])
        self.item_docs = InMemoryDocumentStore()
        today = lambda: date(2027, 12, 11)  # noqa: E731
        planner, rules = EditPlanner(), LifecycleRules()
        self.notes = NoteService(self.notes_repo, Sources(), self.backlogs, None, lambda: NOW)
        self.items = ItemService(self.backlogs, planner, rules, ItemFactory(planner), today, self.notes)
        self.documents = DocumentService(self.backlogs, self.item_docs, planner, rules, today)
        self.note_docs = NoteDocumentService(self.notes_repo, DatabaseNoteDocumentStore(database), today)
        self.flaky_documents = Flaky(self.documents)
        self.flaky_notes = Flaky(self.notes)
        self.service = ConversionService(self.items, self.flaky_documents, self.flaky_notes, self.note_docs,
                                         self.backlogs, Sources(), today)

    def note(self, summary: str = "An idea", body: str | None = "Long text.\nSecond line."):
        return self.notes.create(P, summary, body).note

    def promote(self, label: str = "NOTE-001", item_type: str = "Task", **extra):
        note = self.notes.show(P, label).note
        return self.service.promote(P, label, note.version, item_type, {**FIELDS, **extra})

    def origin_links(self, label: str):
        return [link for link in self.notes.links_of(P, label) if link.role is LinkRole.ORIGIN]

    def item_text(self, item_id: str, name: str) -> str:
        return self.documents.read(SOURCE, item_id, name).content


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def item(item_id: str, status: str = Status.OPEN, **fields) -> Item:
    return Item(id=item_id, title=f"Title of {item_id}", project=P, status=status, **fields)


# ---------- promote ----------

@pytest.mark.parametrize("item_type, item_id", [("Task", "TASK-001"), ("Story", "STORY-001"), ("Epic", "EPIC-001")])
def test_a_note_becomes_a_task_story_or_epic_and_is_archived_as_promoted(world: World, item_type, item_id):
    world.note()

    done = world.promote(item_type=item_type)

    assert (done.item.item.id, done.item.item.title, done.item.item.summary) == (item_id, "An idea", "An idea")
    assert (done.note.note.status, done.note.note.archived) == (NoteStatus.PROMOTED, True)
    assert [(link.target.label, link.target.kind) for link in world.origin_links("NOTE-001")] == [
        (item_id, TargetKind.ITEM)]


def test_the_caller_may_replace_title_and_summary(world: World):
    world.note()

    done = world.promote(title="Better title", summary="Better summary", priority="High")

    assert (done.item.item.title, done.item.item.summary, done.item.item.priority) == (
        "Better title", "Better summary", "High")


def test_the_long_text_is_the_first_notes_entry_of_the_item(world: World):
    world.note()

    done = world.promote()

    text = world.item_text(done.item.item.id, "TASK-001_notes.md")
    assert "## 2027-12-11 — Aus Note NOTE-001 befördert" in text
    assert "- Long text.\n- Second line.\n" in text
    assert done.item.item.notes == ["TASK-001_notes.md"]


def test_notes_and_specs_of_the_note_move_to_the_item_under_its_id(world: World):
    world.note()
    world.note_docs.append_notes(P, "NOTE-001", "Idea", ["talked"], ["chose"], [])
    world.note_docs.write(P, "NOTE-001", "NOTE-001_spec.md", "# Spec\n", None)
    world.note_docs.write(P, "NOTE-001", "NOTE-001_spec_api.md", "# API\n", None)

    done = world.promote()

    item_id = done.item.item.id
    notes = world.item_text(item_id, "TASK-001_notes.md")
    assert "Aus Note NOTE-001 befördert" in notes
    assert "### Decided\n\n- chose" in notes
    assert notes.count("# NOTE-001") == 0
    assert world.item_text(item_id, "TASK-001_spec.md") == "# Spec\n"
    assert world.item_text(item_id, "TASK-001_spec_api.md") == "# API\n"
    assert sorted(done.item.item.spec) == ["TASK-001_spec.md", "TASK-001_spec_api.md"]


def test_a_note_without_long_text_still_leaves_its_origin_in_the_notes(world: World):
    world.note(body=None)

    done = world.promote()

    assert "Note NOTE-001 ohne Langtext." in world.item_text(done.item.item.id, "TASK-001_notes.md")


def test_a_missing_required_field_is_refused_and_the_note_stays_untouched(world: World):
    note = world.note()

    with pytest.raises(ValueRequiredError) as refused:
        world.service.promote(P, "NOTE-001", note.version, "Task", {"area": "Core"})
    assert refused.value.details["field"] == "goal"

    assert world.backlogs.load(SOURCE).items == []
    assert world.notes.show(P, "NOTE-001").note.status is NoteStatus.WAITING
    assert world.origin_links("NOTE-001") == []


def test_a_closed_parent_is_refused_and_the_note_stays_untouched(tmp_path: Path):
    world = World(tmp_path, [Item(id="EPIC-001", title="Closed", project=P, item_type="Epic",
                                  status=Status.REJECTED, resolution="no")])
    note = world.note()

    with pytest.raises(LifecycleViolationError) as refused:
        world.service.promote(P, "NOTE-001", note.version, "Task",
                              {**FIELDS, "parent": "EPIC-001", "required_for_parent": "Yes"})

    assert refused.value.code == "parent_closed"
    assert len(world.backlogs.load(SOURCE).items) == 1
    assert (world.notes.show(P, "NOTE-001").note.status, world.origin_links("NOTE-001")) == (NoteStatus.WAITING, [])


def test_a_stale_version_or_a_closed_note_is_refused(world: World):
    note = world.note()

    with pytest.raises(VersionConflictError):
        world.service.promote(P, "NOTE-001", "stale", "Task", FIELDS)

    world.notes.finish(P, "NOTE-001", note.version, NoteStatus.DROPPED)
    dropped = world.notes.show(P, "NOTE-001").note
    with pytest.raises(NoteLifecycleError) as refused:
        world.service.promote(P, "NOTE-001", dropped.version, "Task", FIELDS)
    assert refused.value.code == "note_closed"


@pytest.mark.parametrize("failing", ["write", "finish"])
def test_a_failure_after_the_item_exists_is_repeatable_without_a_second_item(world: World, failing):
    note = world.note()
    world.note_docs.write(P, "NOTE-001", "NOTE-001_spec.md", "# Spec\n", None)
    (world.flaky_documents if failing == "write" else world.flaky_notes).fail_next = failing

    with pytest.raises(RuntimeError):
        world.service.promote(P, "NOTE-001", note.version, "Task", FIELDS)

    assert [i.id for i in world.backlogs.load(SOURCE).items] == ["TASK-001"]
    assert [link.target.label for link in world.origin_links("NOTE-001")] == ["TASK-001"]
    assert world.notes.show(P, "NOTE-001").note.status is not NoteStatus.PROMOTED

    done = world.service.promote(P, "NOTE-001", note.version, "Task", FIELDS)

    assert [i.id for i in world.backlogs.load(SOURCE).items] == ["TASK-001"]
    assert done.note.note.status is NoteStatus.PROMOTED
    text = world.item_text("TASK-001", "TASK-001_notes.md")
    assert text.count("Aus Note NOTE-001 befördert") == 1
    assert world.item_text("TASK-001", "TASK-001_spec.md") == "# Spec\n"


def test_a_repeat_after_the_item_vanished_is_refused_instead_of_creating_another(world: World):
    note = world.note()
    world.flaky_documents.fail_next = "write"
    with pytest.raises(RuntimeError):
        world.service.promote(P, "NOTE-001", note.version, "Task", FIELDS)
    world.backlogs.delete(SOURCE, world.backlogs.load(SOURCE).items)

    with pytest.raises(ConversionRefusedError) as refused:
        world.service.promote(P, "NOTE-001", note.version, "Task", FIELDS)

    assert (refused.value.code, refused.value.details["items"]) == ("promote_origin_missing", "TASK-001")
    assert world.backlogs.load(SOURCE).items == []


# ---------- demote ----------

def demote(world: World, item_id: str = "TASK-001", topic: str | None = None):
    found = world.backlogs.get(SOURCE, item_id)
    return world.service.demote(SOURCE, item_id, found.version, topic)


def test_an_open_item_becomes_a_note_and_is_closed_as_rejected(tmp_path: Path):
    world = World(tmp_path, [item("TASK-001", summary="What it is.")])

    done = demote(world)

    note = done.note.note
    assert (note.label, note.summary, note.body, note.status) == ("NOTE-001", "Title of TASK-001", "What it is.",
                                                                    NoteStatus.WAITING)
    assert [(link.target.label, link.target.kind) for link in world.origin_links("NOTE-001")] == [
        ("TASK-001", TargetKind.ITEM)]
    closed = world.backlogs.get(SOURCE, "TASK-001")
    assert (closed.status, closed.resolution) == (Status.REJECTED, "zur Notiz zurückgestuft")
    assert (done.item.item.status, done.item.item.resolution) == (Status.REJECTED, "zur Notiz zurückgestuft")


def test_the_topic_is_given_to_the_new_note(tmp_path: Path):
    world = World(tmp_path, [item("TASK-001")])
    topic = world.notes_repo.create_topic(P, "Ideas", None, None, 3)

    assert demote(world, topic=topic.label).note.note.topic == topic.label


def test_notes_and_specs_of_the_item_move_to_the_note_under_its_label(tmp_path: Path):
    world = World(tmp_path, [item("TASK-001", summary="What.")])
    world.documents.append_notes(SOURCE, "TASK-001", "Plan", ["talked"], ["chose"], [], None)
    world.documents.write(SOURCE, "TASK-001", "TASK-001_spec.md", "# Spec\n", None)

    done = demote(world)

    assert world.note_docs.read(P, "NOTE-001", "NOTE-001_spec.md").content == "# Spec\n"
    notes = world.note_docs.read(P, "NOTE-001", "NOTE-001_notes.md")
    assert (notes.kind, "### Decided\n\n- chose" in notes.content) == (DocumentKind.NOTES, True)
    assert sorted(name for name, _ in world.note_docs.names(P, "NOTE-001")) == [
        "NOTE-001_notes.md", "NOTE-001_spec.md"]
    assert done.note.note.status is NoteStatus.WAITING


@pytest.mark.parametrize("fields, code", [
    ({"status": Status.IN_PROGRESS}, "demote_not_open"),
    ({"status": Status.COMPLETED, "resolution": "done"}, "demote_not_open"),
])
def test_an_item_that_is_not_open_is_refused_and_nothing_is_created(tmp_path: Path, fields, code):
    world = World(tmp_path, [item("TASK-001", **fields)])

    with pytest.raises(ConversionRefusedError) as refused:
        demote(world)

    assert refused.value.code == code
    assert world.notes.overview(P) == []


def test_an_item_with_children_or_dependents_is_refused(tmp_path: Path):
    world = World(tmp_path, [item("STORY-001", item_type="Story"), item("TASK-001", parent="STORY-001",
                                                                          required_for_parent=True),
                             item("TASK-002", dependencies=["TASK-003"]), item("TASK-003")])

    with pytest.raises(ConversionRefusedError) as parent:
        demote(world, "STORY-001")
    with pytest.raises(ConversionRefusedError) as dependency:
        demote(world, "TASK-003")

    assert (parent.value.code, dependency.value.code) == ("demote_has_children", "demote_referenced")
    assert world.notes.overview(P) == []


def test_a_stale_item_version_is_refused(tmp_path: Path):
    world = World(tmp_path, [item("TASK-001")])

    with pytest.raises(VersionConflictError):
        world.service.demote(SOURCE, "TASK-001", "stale")

    assert world.notes.overview(P) == []


def test_a_document_that_a_note_cannot_hold_stops_the_demotion_before_anything_changes(tmp_path: Path):
    world = World(tmp_path, [item("TASK-001", notes=["design.md"], summary="x")])
    world.item_docs.write(SOURCE, "TASK-001", "design.md", "text", None)

    with pytest.raises(ConversionRefusedError) as refused:
        demote(world)

    assert refused.value.code == "demote_document_name"
    assert world.notes.overview(P) == []
    assert world.backlogs.get(SOURCE, "TASK-001").status == Status.OPEN


@pytest.mark.parametrize("failing", ["write", "edit"])
def test_a_failure_after_the_note_exists_is_repeatable_without_a_second_note(tmp_path: Path, failing):
    world = World(tmp_path, [item("TASK-001", summary="What.")])
    world.documents.write(SOURCE, "TASK-001", "TASK-001_spec.md", "# Spec\n", None)
    version = world.backlogs.get(SOURCE, "TASK-001").version
    if failing == "write":
        world.note_docs = Flaky(world.note_docs)
        world.service._note_documents = world.note_docs
        world.note_docs.fail_next = "write"
    else:
        flaky_items = Flaky(world.items)
        world.service._items = flaky_items
        flaky_items.fail_next = "edit"

    with pytest.raises(RuntimeError):
        world.service.demote(SOURCE, "TASK-001", version)

    assert [n.note.label for n in world.notes.overview(P)] == ["NOTE-001"]
    assert world.backlogs.get(SOURCE, "TASK-001").status == Status.OPEN

    world.service.demote(SOURCE, "TASK-001", version)

    assert [n.note.label for n in world.notes.overview(P)] == ["NOTE-001"]
    assert world.backlogs.get(SOURCE, "TASK-001").status == Status.REJECTED
    assert world.note_docs.read(P, "NOTE-001", "NOTE-001_spec.md").content == "# Spec\n"


def test_closing_the_item_tells_no_note_about_its_origin(tmp_path: Path):
    world = World(tmp_path, [item("TASK-001")])

    demote(world)

    assert world.notes.notices(P, "NOTE-001", NoticeSide.NOTE, open_only=False) == []


def test_an_item_that_came_from_a_note_can_be_demoted_into_a_new_note(world: World):
    world.note()
    promoted = world.promote()

    item_id = promoted.item.item.id
    back = demote(world, item_id)

    assert back.note.note.label == "NOTE-002"
    assert [n.note.status for n in world.notes.overview(P, archived=True)] == [NoteStatus.PROMOTED]
    assert LinkTarget(TargetKind.ITEM, P, item_id) in [link.target for link in world.origin_links("NOTE-002")]

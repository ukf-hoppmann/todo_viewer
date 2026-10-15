"""The contract of the notes store: label assignment, topic depth, links, triggers, documents, project change."""
from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from todo_viewer.application.ports import NoteDocumentStore, NoteRepository
from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    NoteNotFoundError,
    NoticeNotFoundError,
    TopicLoopError,
    TopicNotFoundError,
    TopicTooDeepError,
    VersionConflictError,
)
from todo_viewer.domain.notes import (
    LinkRole,
    LinkTarget,
    NewNote,
    NewNotice,
    NewTrigger,
    Note,
    NoteChanges,
    NoteStatus,
    NoticeCause,
    NoticeDecision,
    NoticeSide,
    TargetKind,
    Topic,
    TriggerKind,
    TriggerMode,
)
from todo_viewer.infrastructure.database.engine import Database
from todo_viewer.infrastructure.database.notes import DatabaseNoteDocumentStore, DatabaseNoteRepository

P, Q = "proj-a", "proj-b"
NOON = datetime(2027, 12, 11, 9, 0, tzinfo=timezone(timedelta(hours=1)))


@pytest.fixture(params=["database"])
def stores(request: pytest.FixtureRequest, tmp_path: Path) -> tuple[NoteRepository, NoteDocumentStore]:
    db = Database(f"sqlite:///{tmp_path / 'todo.db'}")
    return DatabaseNoteRepository(db), DatabaseNoteDocumentStore(db)


@pytest.fixture
def notes(stores: tuple[NoteRepository, NoteDocumentStore]) -> NoteRepository:
    return stores[0]


@pytest.fixture
def documents(stores: tuple[NoteRepository, NoteDocumentStore]) -> NoteDocumentStore:
    return stores[1]


def item(label: str, project: str = P) -> LinkTarget:
    return LinkTarget(TargetKind.ITEM, project, label)


# ---------- labels ----------

def test_labels_count_per_project_and_type(notes: NoteRepository):
    assert [notes.create_note(P, NewNote("a")).label, notes.create_note(P, NewNote("b")).label,
            notes.create_note(Q, NewNote("c")).label] == ["NOTE-001", "NOTE-002", "NOTE-001"]
    assert [notes.create_topic(P, "t", None, None, 3).label, notes.create_topic(Q, "t", None, None, 3).label,
            notes.create_topic(P, "u", None, None, 3).label] == ["TOPIC-001", "TOPIC-001", "TOPIC-002"]


def test_a_label_is_never_given_twice(notes: NoteRepository):
    notes.create_note(P, NewNote("a"))
    notes.delete_note(P, "NOTE-001", NOON)

    assert notes.create_note(P, NewNote("b")).label == "NOTE-002"


# ---------- topics ----------

def test_topics_nest_up_to_the_configured_depth(notes: NoteRepository):
    a = notes.create_topic(P, "a", None, None, 3)
    b = notes.create_topic(P, "b", a.label, None, 3)
    c = notes.create_topic(P, "c", b.label, None, 3)

    assert (b.parent, c.parent) == (a.label, b.label)
    with pytest.raises(TopicTooDeepError):
        notes.create_topic(P, "d", c.label, None, 3)
    assert notes.create_topic(P, "d", c.label, None, 4).label == "TOPIC-004"  # the refused one used no number


def test_a_topic_has_an_optional_due_date_stored_unambiguously(notes: NoteRepository):
    topic = notes.create_topic(P, "a", None, NOON, 3)

    assert topic.due_at == NOON
    assert topic.due_at is not None and topic.due_at.utcoffset() == timedelta(0)
    assert notes.update_topic(P, topic.label, "renamed", None).due_at is None
    assert notes.get_topic(P, topic.label).name == "renamed"


def test_an_unknown_parent_is_refused(notes: NoteRepository):
    with pytest.raises(TopicNotFoundError):
        notes.create_topic(P, "a", "TOPIC-099", None, 3)


def test_moving_a_topic_keeps_the_limits(notes: NoteRepository):
    a = notes.create_topic(P, "a", None, None, 3)
    b = notes.create_topic(P, "b", a.label, None, 3)
    c = notes.create_topic(P, "c", None, None, 3)
    d = notes.create_topic(P, "d", c.label, None, 3)

    with pytest.raises(TopicLoopError):
        notes.move_topic(P, a.label, b.label, 3)
    with pytest.raises(TopicTooDeepError):
        notes.move_topic(P, c.label, b.label, 3)  # c has a child: 2 + 2 levels
    assert notes.move_topic(P, d.label, b.label, 3).parent == b.label
    assert [t.label for t in notes.list_topics(P)] == [a.label, b.label, c.label, d.label]


# ---------- notes ----------

def test_a_note_starts_waiting_with_any_mode(notes: NoteRepository):
    topic = notes.create_topic(P, "t", None, None, 3)
    note = notes.create_note(P, NewNote("short", body="long", topic=topic.label, review_at=NOON))

    assert (note.status, note.trigger_mode, note.topic, note.body, note.review_at) == (
        NoteStatus.WAITING, TriggerMode.ANY, topic.label, "long", NOON)
    assert notes.get_note(P, note.label) == note


def test_a_note_with_an_unknown_topic_is_refused(notes: NoteRepository):
    with pytest.raises(TopicNotFoundError):
        notes.create_note(P, NewNote("a", topic="TOPIC-001"))
    assert notes.list_notes(P) == []


def test_update_replaces_only_the_given_fields(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a", body="b"))

    changed = notes.update_note(P, note.label, note.version, NoteChanges(
        summary="a2", status=NoteStatus.SNOOZED, trigger_mode=TriggerMode.ALL, clear_body=True))

    assert (changed.summary, changed.body, changed.status, changed.trigger_mode) == (
        "a2", None, NoteStatus.SNOOZED, TriggerMode.ALL)
    assert changed.version != note.version


def test_update_of_a_stale_version_is_refused(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    notes.update_note(P, note.label, note.version, NoteChanges(summary="b"))

    with pytest.raises(VersionConflictError):
        notes.update_note(P, note.label, note.version, NoteChanges(summary="c"))
    assert notes.get_note(P, note.label).summary == "b"


def test_deleted_notes_leave_the_list_and_can_come_back(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))

    notes.delete_note(P, note.label, NOON)
    assert notes.list_notes(P) == []
    assert [n.label for n in notes.list_notes(P, include_deleted=True)] == [note.label]
    assert notes.restore_note(P, note.label).deleted is None
    assert [n.label for n in notes.list_notes(P)] == [note.label]


def test_an_unknown_note_is_an_error(notes: NoteRepository):
    with pytest.raises(NoteNotFoundError):
        notes.get_note(P, "NOTE-001")


# ---------- links ----------

def test_a_link_has_a_role_and_can_be_found_from_its_target(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    other = notes.create_note(Q, NewNote("b"))

    ref = notes.add_link(P, note.label, item("TASK-001"), LinkRole.REFERENCE)
    origin = notes.add_link(Q, other.label, item("TASK-001", P), LinkRole.ORIGIN)  # across projects

    assert notes.links_of(P, note.label) == [ref]
    assert [(link.project, link.note, link.role) for link in notes.links_to(item("TASK-001"))] == [
        (P, note.label, LinkRole.REFERENCE), (Q, other.label, LinkRole.ORIGIN)]
    assert origin.target.project == P
    notes.remove_link(P, note.label, ref.id)
    assert notes.links_of(P, note.label) == []


def test_a_link_can_point_to_a_topic_or_a_note(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))

    notes.add_link(P, note.label, LinkTarget(TargetKind.TOPIC, P, "TOPIC-001"), LinkRole.REFERENCE)
    notes.add_link(P, note.label, LinkTarget(TargetKind.NOTE, P, "NOTE-009"), LinkRole.ORIGIN)

    assert [link.target.kind for link in notes.links_of(P, note.label)] == [TargetKind.TOPIC, TargetKind.NOTE]


def test_links_follow_a_new_item_label(notes: NoteRepository):
    """The retype of an item changes its label; its links and event triggers must follow."""
    note = notes.create_note(P, NewNote("a"))
    notes.add_link(P, note.label, item("STORY-001"), LinkRole.REFERENCE)
    notes.add_trigger(P, note.label, NewTrigger(TriggerKind.EVENT, target=item("STORY-001"),
                                                target_status="Completed"))
    notes.add_link(P, note.label, item("STORY-002"), LinkRole.REFERENCE)

    notes.relink_item(P, "STORY-001", "TASK-007")

    assert [link.target.label for link in notes.links_of(P, note.label)] == ["TASK-007", "TASK-007", "STORY-002"]
    assert [t.target.label for t in notes.triggers_of(P, note.label) if t.target] == ["TASK-007"]
    assert notes.links_to(item("STORY-001")) == []


def test_relinking_leaves_the_same_label_of_another_project_alone(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    notes.add_link(P, note.label, item("STORY-001", Q), LinkRole.REFERENCE)

    notes.relink_item(P, "STORY-001", "TASK-007")

    assert notes.links_of(P, note.label)[0].target.label == "STORY-001"


# ---------- triggers ----------

def test_trigger_kinds_and_their_state(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))

    time = notes.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=NOON))
    event = notes.add_trigger(P, note.label, NewTrigger(
        TriggerKind.EVENT, target=item("TASK-007"), target_status="Completed", fired_at=NOON, already_met=True))
    topic = notes.add_trigger(P, note.label, NewTrigger(TriggerKind.TOPIC_DUE))

    assert (time.at, time.fired_at, time.target) == (NOON, None, None)
    assert (event.target, event.target_status, event.fired_at, event.already_met) == (
        item("TASK-007"), "Completed", NOON, True)
    assert topic.kind is TriggerKind.TOPIC_DUE
    assert notes.triggers_of(P, note.label) == [time, event, topic]


def test_an_event_trigger_has_a_link_with_the_role_trigger(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    event = notes.add_trigger(P, note.label, NewTrigger(TriggerKind.EVENT, target=item("TASK-007"),
                                                        target_status="Completed"))

    assert [(link.id, link.role) for link in notes.links_of(P, note.label)] == [(event.link_id, LinkRole.TRIGGER)]
    notes.remove_trigger(P, note.label, event.id)
    assert notes.links_of(P, note.label) == [] and notes.triggers_of(P, note.label) == []


def test_every_trigger_arrives_on_its_own(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    first = notes.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=NOON))
    notes.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=NOON))

    fired = notes.mark_fired(P, note.label, first.id, NOON + timedelta(hours=1))

    assert fired.fired_at == NOON + timedelta(hours=1)
    assert [t.fired_at is not None for t in notes.triggers_of(P, note.label)] == [True, False]


# ---------- documents ----------

def test_notes_and_specs_of_a_note_can_be_saved_and_read(notes: NoteRepository, documents: NoteDocumentStore):
    note = notes.create_note(P, NewNote("a"))

    documents.write(P, note.label, "NOTE-001_notes.md", "# notes\n", None)
    documents.write(P, note.label, "NOTE-001_spec.md", "# spec\n", None)
    documents.write(P, note.label, "NOTE-001_spec_api.md", "# api\n", None)

    assert documents.read(P, note.label, "NOTE-001_spec.md") == "# spec\n"
    assert documents.names(P, note.label) == ["NOTE-001_notes.md", "NOTE-001_spec.md", "NOTE-001_spec_api.md"]
    documents.write(P, note.label, "NOTE-001_spec.md", "# spec 2\n", content_version("# spec\n"))
    assert documents.append(P, note.label, "NOTE-001_notes.md", "more", "# h") == "# notes\n\nmore"
    assert documents.append(P, note.label, "NOTE-001_spec_new.md", "x", "# h") == "# h\nx"
    documents.delete_document(P, note.label, "NOTE-001_spec.md")
    with pytest.raises(DocumentNotFoundError):
        documents.read(P, note.label, "NOTE-001_spec.md")


def test_a_stale_document_write_is_refused(notes: NoteRepository, documents: NoteDocumentStore):
    note = notes.create_note(P, NewNote("a"))
    documents.write(P, note.label, "NOTE-001_notes.md", "one", None)

    with pytest.raises(VersionConflictError):
        documents.write(P, note.label, "NOTE-001_notes.md", "two", content_version("old"))
    with pytest.raises(VersionConflictError):
        documents.write(P, note.label, "NOTE-001_notes.md", "two", None)


def test_foreign_document_names_are_refused(notes: NoteRepository, documents: NoteDocumentStore):
    note = notes.create_note(P, NewNote("a"))

    with pytest.raises(DocumentForbiddenError):
        documents.write(P, note.label, "NOTE-002_notes.md", "x", None)


# ---------- change of project ----------

def test_a_note_that_changes_project_is_a_new_note_there(notes: NoteRepository, documents: NoteDocumentStore):
    notes.create_note(Q, NewNote("already there"))
    topic = notes.create_topic(Q, "t", None, None, 3)
    note = notes.create_note(P, NewNote("a", body="b", review_at=NOON))
    note = notes.update_note(P, note.label, note.version, NoteChanges(status=NoteStatus.SNOOZED))
    notes.add_link(P, note.label, item("TASK-001"), LinkRole.REFERENCE)
    event = notes.add_trigger(P, note.label, NewTrigger(TriggerKind.EVENT, target=item("TASK-002"),
                                                        target_status="Completed"))
    notes.mark_fired(P, note.label, event.id, NOON)
    documents.write(P, note.label, "NOTE-001_notes.md", "# notes\n", None)
    pointing = notes.create_note(P, NewNote("points at the first"))
    notes.add_link(P, pointing.label, LinkTarget(TargetKind.NOTE, P, note.label), LinkRole.REFERENCE)

    moved = notes.move_note(P, note.label, Q, topic.label, NOON)

    assert (moved.project, moved.label) == (Q, "NOTE-002")
    assert (moved.summary, moved.body, moved.status, moved.topic, moved.review_at) == (
        "a", "b", NoteStatus.SNOOZED, topic.label, NOON)
    assert notes.get_note(P, note.label).deleted == NOON
    assert [n.label for n in notes.list_notes(P)] == [pointing.label]
    assert [(link.role, link.target.label) for link in notes.links_of(Q, moved.label)] == [
        (LinkRole.REFERENCE, "TASK-001"), (LinkRole.TRIGGER, "TASK-002")]
    new_event = notes.triggers_of(Q, moved.label)[0]
    assert (new_event.fired_at, new_event.target) == (NOON, item("TASK-002")) and new_event.link_id is not None
    assert documents.read(Q, moved.label, "NOTE-002_notes.md") == "# notes\n"
    assert notes.links_of(P, pointing.label)[0].target == LinkTarget(TargetKind.NOTE, Q, moved.label)


def test_a_failed_move_changes_nothing(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))

    with pytest.raises(TopicNotFoundError):
        notes.move_note(P, note.label, Q, "TOPIC-009", NOON)

    assert notes.list_notes(Q) == [] and notes.get_note(P, note.label).deleted is None
    assert notes.create_note(Q, NewNote("x")).label == "NOTE-001"


def test_moments_are_returned_in_utc(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a", review_at=NOON))

    assert note.review_at == NOON and note.review_at is not None and note.review_at.tzinfo == UTC


# ---------- archive filter and reset of triggers (STORY-040/043) ----------

def test_notes_can_be_filtered_by_the_archive(notes: NoteRepository):
    open_note = notes.create_note(P, NewNote("open"))
    closed = notes.create_note(P, NewNote("closed"))
    notes.update_note(P, closed.label, closed.version, NoteChanges(status=NoteStatus.DONE, archived=True))

    assert [n.label for n in notes.list_notes(P)] == [open_note.label, closed.label]
    assert [n.label for n in notes.list_notes(P, archived=False)] == [open_note.label]
    assert [n.label for n in notes.list_notes(P, archived=True)] == [closed.label]


def test_resetting_triggers_clears_what_has_fired(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    timed = notes.add_trigger(P, note.label, NewTrigger(TriggerKind.TIME, at=NOON, fired_at=NOON))
    event = notes.add_trigger(P, note.label, NewTrigger(TriggerKind.EVENT, target=item("STORY-001"),
                                                        target_status="Completed", fired_at=NOON, already_met=True))
    other = notes.create_note(P, NewNote("b"))
    keep = notes.add_trigger(P, other.label, NewTrigger(TriggerKind.TIME, at=NOON, fired_at=NOON))

    reset = notes.reset_triggers(P, note.label)

    assert [(t.id, t.fired_at, t.already_met) for t in reset] == [(timed.id, None, False), (event.id, None, False)]
    assert reset[0].at == NOON and reset[1].target == item("STORY-001") and reset[1].link_id == event.link_id
    assert notes.triggers_of(P, other.label) == [keep]


# ---------- topics in the trash ----------

def tree(notes: NoteRepository):
    a = notes.create_topic(P, "a", None, None, 3)
    b = notes.create_topic(P, "b", a.label, None, 3)
    n_a = notes.create_note(P, NewNote("in a", topic=a.label))
    n_b = notes.create_note(P, NewNote("in b", topic=b.label))
    return a, b, n_a, n_b


def test_topics_and_notes_go_to_the_trash_together(notes: NoteRepository):
    a, b, n_a, n_b = tree(notes)

    notes.trash_topics(P, [a.label, b.label], [n_b.label], NOON)

    assert [t.label for t in notes.list_topics(P)] == []
    assert [t.label for t in notes.list_topics(P, include_deleted=True)] == [a.label, b.label]
    assert notes.get_topic(P, a.label).deleted == NOON
    assert [n.label for n in notes.list_notes(P)] == [n_a.label]
    assert notes.get_note(P, n_b.label).deleted == NOON


def test_trashing_topics_is_all_or_nothing(notes: NoteRepository):
    a, b, n_a, n_b = tree(notes)

    with pytest.raises(NoteNotFoundError):
        notes.trash_topics(P, [a.label], ["NOTE-099"], NOON)

    assert notes.get_topic(P, a.label).deleted is None


def test_restoring_topics_brings_the_notes_back(notes: NoteRepository):
    a, b, n_a, n_b = tree(notes)
    notes.trash_topics(P, [a.label, b.label], [n_b.label], NOON)

    notes.restore_topics(P, [a.label, b.label], [n_b.label])

    assert [t.label for t in notes.list_topics(P)] == [a.label, b.label]
    assert notes.get_note(P, n_b.label).deleted is None


def test_purging_removes_notes_links_triggers_and_documents_but_not_the_label(notes: NoteRepository,
                                                                               documents: NoteDocumentStore):
    a, b, n_a, n_b = tree(notes)
    notes.add_link(P, n_a.label, LinkTarget(TargetKind.NOTE, P, n_b.label), LinkRole.REFERENCE)
    notes.add_trigger(P, n_b.label, NewTrigger(TriggerKind.EVENT, target=item("STORY-001"), target_status="Completed"))
    documents.write(P, n_b.label, f"{n_b.label}_notes.md", "text", None)
    notes.trash_topics(P, [a.label, b.label], [n_b.label], NOON)

    notes.purge_topics(P, [a.label, b.label], [n_b.label])

    with pytest.raises(TopicNotFoundError):
        notes.get_topic(P, b.label)
    with pytest.raises(NoteNotFoundError):
        notes.get_note(P, n_b.label)
    assert notes.links_of(P, n_a.label) == []  # the link to the purged note went with it
    assert notes.links_to(item("STORY-001")) == []
    with pytest.raises(NoteNotFoundError):
        documents.names(P, n_b.label)
    assert notes.create_note(P, NewNote("new")).label == "NOTE-003"
    assert notes.create_topic(P, "new", None, None, 3).label == "TOPIC-003"


def test_a_single_note_can_be_purged(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    keep = notes.create_note(P, NewNote("b"))
    notes.delete_note(P, note.label, NOON)

    notes.purge_note(P, note.label)

    with pytest.raises(NoteNotFoundError):
        notes.get_note(P, note.label)
    assert notes.get_note(P, keep.label) == keep


# ---------- notices ----------

def note_notice(label: str, item_label: str = "STORY-001", cause: NoticeCause = NoticeCause.ITEM_COMPLETED,
                project: str = P, item_project: str = P) -> NewNotice:
    return NewNotice(NoticeSide.NOTE, project, label, cause, item(item_label, item_project))


def item_notice(note_label: str, item_label: str = "STORY-001", cause: NoticeCause = NoticeCause.NOTE_DROPPED,
                project: str = P) -> NewNotice:
    return NewNotice(NoticeSide.ITEM, project, item_label, cause, LinkTarget(TargetKind.NOTE, P, note_label))


def test_a_notice_is_stored_open_with_both_sides(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))

    stored = notes.add_notice(note_notice(note.label))

    assert (stored.side, stored.project, stored.label, stored.cause) == (
        NoticeSide.NOTE, P, note.label, NoticeCause.ITEM_COMPLETED)
    assert stored.counterpart == item("STORY-001")
    assert stored.is_open and stored.decision is None and stored.created_at.utcoffset() == timedelta(0)
    assert notes.get_notice(stored.id) == stored


def test_an_open_notice_of_the_same_cause_and_counterpart_is_not_added_twice(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    first = notes.add_notice(note_notice(note.label))

    again = notes.add_notice(note_notice(note.label))
    other_cause = notes.add_notice(note_notice(note.label, cause=NoticeCause.ITEM_REJECTED))
    other_item = notes.add_notice(note_notice(note.label, "STORY-002"))

    assert again == first
    assert len({first.id, other_cause.id, other_item.id}) == 3
    assert len(notes.notices_of(P, note.label, NoticeSide.NOTE, open_only=True)) == 3


def test_a_decided_notice_does_not_block_a_new_one_of_the_same_cause(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    first = notes.add_notice(note_notice(note.label))
    notes.decide_notice(first.id, NoticeDecision.KEEP, NOON)

    second = notes.add_notice(note_notice(note.label))

    assert second.id != first.id and second.is_open


def test_notices_are_read_per_side_open_or_all(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    mine = notes.add_notice(note_notice(note.label))
    decided = notes.add_notice(note_notice(note.label, "STORY-002"))
    notes.decide_notice(decided.id, NoticeDecision.DETACH, NOON)
    on_item = notes.add_notice(item_notice(note.label))

    assert notes.notices_of(P, note.label, NoticeSide.NOTE, open_only=True) == [mine]
    assert [n.id for n in notes.notices_of(P, note.label, NoticeSide.NOTE, open_only=False)] == [mine.id, decided.id]
    assert notes.notices_of(P, "STORY-001", NoticeSide.ITEM, open_only=True) == [on_item]
    assert notes.notices_of(Q, "STORY-001", NoticeSide.ITEM, open_only=False) == []  # same label, other project


def test_deciding_closes_the_notice_with_the_decision_and_the_moment(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    stored = notes.add_notice(note_notice(note.label))

    decided = notes.decide_notice(stored.id, NoticeDecision.KEEP, NOON)

    assert (decided.decision, decided.decided_at, decided.is_open) == (NoticeDecision.KEEP, NOON, False)
    assert decided.decided_at is not None and decided.decided_at.utcoffset() == timedelta(0)
    assert notes.get_notice(stored.id) == decided


def test_an_unknown_notice_is_an_error(notes: NoteRepository):
    with pytest.raises(NoticeNotFoundError):
        notes.get_notice(99)
    with pytest.raises(NoticeNotFoundError):
        notes.decide_notice(99, NoticeDecision.KEEP, NOON)


def test_notices_of_an_unknown_note_are_an_error(notes: NoteRepository):
    with pytest.raises(NoteNotFoundError):
        notes.add_notice(note_notice("NOTE-009"))


def test_notices_follow_a_new_item_label(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    notes.add_notice(note_notice(note.label))
    notes.add_notice(item_notice(note.label))
    other_project = notes.add_notice(item_notice(note.label, project=Q))

    notes.relink_item(P, "STORY-001", "TASK-007")

    assert notes.notices_of(P, note.label, NoticeSide.NOTE, open_only=False)[0].counterpart == item("TASK-007")
    assert len(notes.notices_of(P, "TASK-007", NoticeSide.ITEM, open_only=False)) == 1
    assert notes.get_notice(other_project.id).label == "STORY-001"


def test_notices_come_along_when_a_note_changes_project(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    mine = notes.add_notice(note_notice(note.label))
    on_item = notes.add_notice(item_notice(note.label))

    moved = notes.move_note(P, note.label, Q, None, NOON)

    assert notes.notices_of(P, note.label, NoticeSide.NOTE, open_only=False) == []
    assert [(n.id, n.project, n.label) for n in notes.notices_of(Q, moved.label, NoticeSide.NOTE, open_only=False)] == [
        (mine.id, Q, moved.label)]
    assert notes.get_notice(on_item.id).counterpart == LinkTarget(TargetKind.NOTE, Q, moved.label)


def test_purging_a_note_removes_its_notices_and_those_that_name_it(notes: NoteRepository):
    note = notes.create_note(P, NewNote("a"))
    keep = notes.create_note(P, NewNote("b"))
    mine = notes.add_notice(note_notice(note.label))
    on_item = notes.add_notice(item_notice(note.label))
    kept = notes.add_notice(note_notice(keep.label))
    notes.delete_note(P, note.label, NOON)

    notes.purge_note(P, note.label)

    for gone in (mine, on_item):
        with pytest.raises(NoticeNotFoundError):
            notes.get_notice(gone.id)
    assert notes.get_notice(kept.id) == kept


# ---------- taking over whole notes and topics (the notes sync) ----------

def test_a_stored_topic_keeps_its_label_times_and_parent_and_is_replaced_by_the_next_store(notes: NoteRepository):
    root = Topic(P, "TOPIC-005", "Root", None, NOON, NOON, None)
    child = Topic(P, "TOPIC-006", "Child", "TOPIC-005", None, NOON, NOON)

    notes.store_topic(P, root)
    notes.store_topic(P, child)
    notes.store_topic(P, dataclasses.replace(root, name="Renamed", due_at=None))

    assert notes.get_topic(P, "TOPIC-006") == child
    assert notes.get_topic(P, "TOPIC-005") == dataclasses.replace(root, name="Renamed", due_at=None)
    assert [t.label for t in notes.list_topics(P, include_deleted=True)] == ["TOPIC-005", "TOPIC-006"]


def test_a_topic_below_an_unknown_parent_is_refused(notes: NoteRepository):
    with pytest.raises(TopicNotFoundError):
        notes.store_topic(P, Topic(P, "TOPIC-001", "x", "TOPIC-009", None, NOON, None))


def test_a_stored_note_takes_over_every_field_link_and_trigger_and_replaces_them_on_the_next_store(
        notes: NoteRepository):
    notes.store_topic(P, Topic(P, "TOPIC-001", "t", None, None, NOON, None))
    note = Note(P, "NOTE-007", "from the files", body="Text", status=NoteStatus.DONE, topic="TOPIC-001", review_at=NOON,
                trigger_mode=TriggerMode.ALL, created=NOON, updated=NOON + timedelta(days=1), archived=True,
                deleted=NOON + timedelta(days=2))
    story = item("STORY-001")
    links = [(story, LinkRole.REFERENCE), (LinkTarget(TargetKind.NOTE, P, "NOTE-001"), LinkRole.ORIGIN)]
    triggers = [NewTrigger(TriggerKind.TIME, at=NOON, fired_at=NOON),
                NewTrigger(TriggerKind.EVENT, target=story, target_status="Completed", fired_at=NOON, already_met=True),
                NewTrigger(TriggerKind.TOPIC_DUE)]

    notes.store_note(P, note, links, triggers)

    assert notes.get_note(P, "NOTE-007") == note
    assert [(link.target, link.role) for link in notes.links_of(P, "NOTE-007")] == [
        *links[:2], (story, LinkRole.TRIGGER)]  # the event trigger brings its link of the role trigger
    stored = notes.triggers_of(P, "NOTE-007")
    assert [(t.kind, t.at, t.target, t.target_status, t.fired_at, t.already_met) for t in stored] == [
        (TriggerKind.TIME, NOON, None, None, NOON, False),
        (TriggerKind.EVENT, None, story, "Completed", NOON, True),
        (TriggerKind.TOPIC_DUE, None, None, None, None, False)]

    notes.store_note(P, dataclasses.replace(note, summary="again", topic=None), links[:1], [])

    assert notes.get_note(P, "NOTE-007").summary == "again" and notes.get_note(P, "NOTE-007").topic is None
    assert [link.target for link in notes.links_of(P, "NOTE-007")] == [story]
    assert notes.triggers_of(P, "NOTE-007") == []


def test_a_stored_note_keeps_its_documents_and_notices(notes: NoteRepository, documents: NoteDocumentStore):
    note = Note(P, "NOTE-001", "a", created=NOON, updated=NOON)
    notes.store_note(P, note, [], [])
    documents.write(P, "NOTE-001", "NOTE-001_notes.md", "# notes\n", None)

    notes.store_note(P, dataclasses.replace(note, summary="b"), [], [])

    assert documents.read(P, "NOTE-001", "NOTE-001_notes.md") == "# notes\n"


def test_a_stored_note_under_an_unknown_topic_is_refused(notes: NoteRepository):
    with pytest.raises(TopicNotFoundError):
        notes.store_note(P, Note(P, "NOTE-001", "a", topic="TOPIC-009", created=NOON, updated=NOON), [], [])


def test_the_counters_only_rise_and_labels_continue_after_them(notes: NoteRepository):
    assert notes.counters(P) == {}
    notes.create_note(P, NewNote("a"))

    notes.raise_counter(P, "note", 7)
    notes.raise_counter(P, "note", 3)  # lower: no effect
    notes.raise_counter(P, "topic", 2)

    assert notes.counters(P) == {"note": 7, "topic": 2}
    assert notes.create_note(P, NewNote("b")).label == "NOTE-008"
    assert notes.next_label(P, "topic") == "TOPIC-003" and notes.next_label(P, "topic") == "TOPIC-004"

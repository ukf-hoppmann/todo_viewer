"""What the notes sync compares and rewrites: pure functions on the two sides' notes, topics, and documents."""
# ruff: noqa: E501  (long expectations)
from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.notes import LinkRole, NoteStatus, TargetKind
from todo_viewer.domain.notes_markdown import (
    ParsedLink,
    ParsedNote,
    ParsedTarget,
    TopicLine,
    parse_note,
    render_parsed,
)
from todo_viewer.domain.notes_sync import (
    NotesSide,
    NoteUnit,
    counters_floor,
    extra_entries,
    label_number,
    note_fields,
    note_unit,
    renamed_document,
    rewritten_note,
    side_versions,
    topic_fields,
    topic_version,
)
from todo_viewer.domain.sync import Change, EntryKey, EntryState, plan_sync

T0 = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def parsed(label: str | None, summary: str = "s", **fields: object) -> ParsedNote:
    return ParsedNote(label=label, summary=summary, created=T0, updated=T0, **fields)  # type: ignore[arg-type]


def side(notes: list[NoteUnit] | None = None, topics: list[TopicLine] | None = None,
         documents: dict[tuple[str, str], str] | None = None, counters: dict[str, int] | None = None) -> NotesSide:
    return NotesSide({t.key: t for t in topics or []}, {n.key: n for n in notes or []}, documents or {}, counters or {})


def unit(label: str | None, key: str | None = None, summary: str = "s", **fields: object) -> NoteUnit:
    return note_unit(key or label or "new-x", parsed(label, summary, **fields))


def entries(database: NotesSide, markdown: NotesSide, states: dict[EntryKey, EntryState] | None = None):
    plan = plan_sync([], [], {}, {}, states or {}, extras=extra_entries(database, markdown))
    return {(e.key.kind, e.key.label, e.key.name): e.change for e in plan.entries}, plan


def test_a_note_is_compared_by_its_normalized_file_text():
    a = unit("NOTE-001", summary="same")
    b = note_unit("NOTE-001", parse_note(render_parsed(parsed("NOTE-001", "same")).replace("\n", "\r\n")))

    assert a.version == b.version == content_version(a.text)
    assert unit("NOTE-001", summary="other").version != a.version


def test_what_only_one_side_has_is_new_there_and_what_differs_is_a_conflict_without_a_stored_state():
    changes, _ = entries(side([unit("NOTE-001"), unit("NOTE-002", summary="db")]),
                         side([unit("NOTE-002", summary="file"), unit(None, "new-idea")]))

    assert changes == {("note", "NOTE-001", ""): Change.DATABASE_NEW, ("note", "NOTE-002", ""): Change.BOTH_NEW,
                       ("note", "new-idea", ""): Change.MARKDOWN_NEW}


def test_with_a_stored_state_the_side_that_changed_is_known():
    base = unit("NOTE-001")
    states = {EntryKey("note", "NOTE-001"): EntryState(base.version, base.version)}

    changes, _ = entries(side([unit("NOTE-001", summary="edited in the database")]), side([base]), states)
    again, _ = entries(side([base]), side([unit("NOTE-001", summary="edited in the file")]), states)
    gone, _ = entries(side([]), side([base]), states)

    assert changes == {("note", "NOTE-001", ""): Change.DATABASE_CHANGED}
    assert again == {("note", "NOTE-001", ""): Change.MARKDOWN_CHANGED}
    assert gone == {("note", "NOTE-001", ""): Change.DATABASE_DELETED}


def test_topics_are_compared_with_their_parent_and_dates():
    a = TopicLine("TOPIC-001", "Root")
    moved = TopicLine("TOPIC-002", "Child", parent="TOPIC-001")

    assert topic_version(moved) != topic_version(dataclasses.replace(moved, parent=None))
    assert topic_version(a) != topic_version(dataclasses.replace(a, due_at=T0))
    changes, _ = entries(side(topics=[a]), side(topics=[a, TopicLine(None, "Ohne Label")]))
    assert changes == {("topic", "TOPIC-001", ""): Change.UNCHANGED, ("topic", "new:Ohne Label", ""): Change.MARKDOWN_NEW}


def test_documents_follow_their_note_when_it_is_new_and_are_compared_on_their_own_when_it_exists_on_both_sides():
    both = unit("NOTE-001")
    database = side([both, unit("NOTE-002")], documents={("NOTE-001", "NOTE-001_notes.md"): "db",
                                                      ("NOTE-002", "NOTE-002_notes.md"): "new note's"})
    markdown = side([both], documents={("NOTE-001", "NOTE-001_notes.md"): "file"})

    changes, _ = entries(database, markdown)

    assert changes[("note_document", "NOTE-001", "NOTE-001_notes.md")] is Change.BOTH_NEW
    assert changes[("note_document", "NOTE-002", "NOTE-002_notes.md")] is Change.DATABASE_NEW


def test_the_documents_of_a_deleted_note_are_not_listed_on_their_own():
    base = unit("NOTE-001")
    states = {EntryKey("note", "NOTE-001"): EntryState(base.version, base.version)}

    changes, _ = entries(side([]), side([base], documents={("NOTE-001", "NOTE-001_notes.md"): "x"}), states)

    assert changes == {("note", "NOTE-001", ""): Change.DATABASE_DELETED}


def test_a_conflict_shows_both_versions_as_fields_with_the_body_as_text():
    _, plan = entries(side([unit("NOTE-001", summary="db", body="one\ntwo")]),
                      side([unit("NOTE-001", summary="file", body="one\nTWO")]))

    [conflict] = plan.preview.conflicts
    fields = dict(conflict.database.fields)  # type: ignore[union-attr]
    assert (conflict.entry.kind, fields["summary"], fields["body"]) == ("note", "db", "one\ntwo")
    assert dict(conflict.markdown.fields)["body"] == "one\nTWO"  # type: ignore[union-attr]


def test_the_preview_counts_topics_notes_and_documents_apart_from_the_backlog():
    _, plan = entries(side([unit("NOTE-001")], [TopicLine("TOPIC-001", "t")], {("NOTE-001", "NOTE-001_notes.md"): "x"}),
                      side())

    preview = plan.preview
    assert [e.label for e in preview.notes.created] == ["NOTE-001"]
    assert [e.label for e in preview.topics.created] == ["TOPIC-001"]
    assert [e.name for e in preview.note_documents.created] == ["NOTE-001_notes.md"]
    assert preview.created == () and preview.created_documents == ()
    assert all(e.origin and e.origin.value == "database" for e in preview.notes.created)


def test_the_token_covers_the_notes_of_both_sides():
    base = plan_sync([], [], {}, {}, {}, extras=extra_entries(side([unit("NOTE-001")]), side())).preview.token

    assert base == plan_sync([], [], {}, {}, {}, extras=extra_entries(side([unit("NOTE-001")]), side())).preview.token
    assert base != plan_sync([], [], {}, {}, {}, extras=extra_entries(side([unit("NOTE-001", summary="x")]), side())).preview.token
    assert base != plan_sync([], [], {}, {}, {}, extras=extra_entries(side([unit("NOTE-001")]), side([unit("NOTE-009")]))).preview.token
    assert base != plan_sync([], [], {}, {}, {}).preview.token


def test_the_versions_of_a_side_are_listed_per_entry_for_the_stored_state():
    versions = side_versions(side([unit("NOTE-001")], [TopicLine("TOPIC-001", "t")], {("NOTE-001", "a_notes.md"): "x"}))

    assert set(versions) == {EntryKey("note", "NOTE-001"), EntryKey("topic", "TOPIC-001"),
                             EntryKey("note_document", "NOTE-001", "a_notes.md")}


def test_labels_have_numbers_and_the_counters_never_fall_below_what_exists():
    assert label_number("NOTE-015") == 15 and label_number("new-idea") == 0 and label_number("new:Name") == 0
    floor = counters_floor(side([unit("NOTE-015"), unit(None, "new-a")], [TopicLine("TOPIC-009", "t"), TopicLine(None, "n")],
                                counters={"note": 12, "topic": 3}))

    assert floor == {"note": 15, "topic": 9}
    assert counters_floor(side(counters={"note": 4})) == {"note": 4}
    assert counters_floor(side()) == {}


def test_references_to_labelless_entries_are_rewritten_to_their_new_labels():
    note = parsed(None, topic="new:Ideen", links=(
        ParsedLink(LinkRole.REFERENCE, ParsedTarget(TargetKind.NOTE, "new-andere")),
        ParsedLink(LinkRole.REFERENCE, ParsedTarget(TargetKind.NOTE, "NOTE-007")),
        ParsedLink(LinkRole.ORIGIN, ParsedTarget(TargetKind.ITEM, "STORY-1", "new-andere"))))  # a project named so

    result = rewritten_note(note, "NOTE-012", {"new:Ideen": "TOPIC-004"}, {"new-andere": "NOTE-013"})

    assert result.label == "NOTE-012" and result.topic == "TOPIC-004"
    assert [str(link.target) for link in result.links] == ["note:NOTE-013", "note:NOTE-007", "new-andere:STORY-1"]
    assert rewritten_note(parsed("NOTE-001", topic="TOPIC-001"), "NOTE-001", {}, {}).topic == "TOPIC-001"


def test_the_documents_of_a_labelled_note_get_its_new_label_in_their_names():
    assert renamed_document("new-idea_notes.md", "new-idea", "NOTE-012") == "NOTE-012_notes.md"
    assert renamed_document("new-idea_spec_ui.md", "new-idea", "NOTE-012") == "NOTE-012_spec_ui.md"
    assert renamed_document("NOTE-001_notes.md", "NOTE-001", "NOTE-001") == "NOTE-001_notes.md"


def test_fields_of_a_note_and_a_topic_are_texts_for_the_comparison():
    fields = dict(note_fields(parsed("NOTE-001", "sum", status=NoteStatus.DONE, body="b")))
    topic = dict(topic_fields(TopicLine("TOPIC-001", "t", parent="TOPIC-000", due_at=T0)))

    assert (fields["summary"], fields["status"], fields["body"], fields["archived"]) == ("sum", "done", "b", "false")
    assert (topic["name"], topic["parent"], topic["due"]) == ("t", "TOPIC-000", "2026-10-01T09:00:00Z")

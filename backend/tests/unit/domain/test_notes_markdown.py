"""The file format of notes, topics, and counters: pinned by golden files, round trips, and strict errors."""
# ruff: noqa: E501  (golden-file expectations are long lines)
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from todo_viewer.domain.errors import NoteFormatError
from todo_viewer.domain.notes import (
    Link,
    LinkRole,
    LinkTarget,
    Note,
    NoteStatus,
    TargetKind,
    Topic,
    Trigger,
    TriggerKind,
    TriggerMode,
)
from todo_viewer.domain.notes_markdown import (
    ParsedTarget,
    TopicLine,
    format_moment,
    parse_counters,
    parse_note,
    parse_topics,
    render_counters,
    render_note,
    render_parsed,
    render_topics,
    to_lines,
)

GOLDEN = Path(__file__).parents[2] / "golden" / "notes"


def golden(name: str) -> str:
    return (GOLDEN / name).read_bytes().decode("utf-8")


@pytest.mark.parametrize("name", ["note_full.md", "note_minimal.md", "note_new.md", "note_trashed_archived.md"])
def test_a_note_file_reads_and_writes_back_exactly(name: str):
    assert render_parsed(parse_note(golden(name))) == golden(name)


def test_the_full_note_has_every_field():
    note = parse_note(golden("note_full.md"))

    assert (note.label, note.summary, note.status, note.topic, note.mode) == (
        "NOTE-001", "Prüfen, ob der Sync Notes trägt", NoteStatus.WAITING, "TOPIC-001", TriggerMode.ALL)
    assert note.review_at == datetime(2026, 11, 7, 8, 0, tzinfo=UTC)
    assert note.updated == datetime(2026, 10, 12, 8, 0, 0, 500000, tzinfo=UTC)
    assert [(t.kind, t.fired_at is not None, t.already_met) for t in note.triggers] == [
        (TriggerKind.TIME, True, False), (TriggerKind.EVENT, True, True), (TriggerKind.EVENT, False, False),
        (TriggerKind.TOPIC_DUE, False, False)]
    assert note.triggers[1].target == ParsedTarget(TargetKind.ITEM, "STORY-003", "Mein Projekt")
    assert note.triggers[1].status == "Completed" and note.triggers[2].status == "In progress"
    assert [(link.role.value, str(link.target)) for link in note.links] == [
        ("reference", "Mein Projekt:STORY-004"), ("reference", "topic:TOPIC-002"), ("reference", "note:NOTE-007"),
        ("origin", "Mein Projekt:STORY-009")]
    assert note.body.startswith("# Überschrift\n\nEin Absatz") and note.body.endswith("ohne Zeilenende")  # type: ignore[union-attr]


def test_the_minimal_note_has_a_summary_and_nothing_else():
    note = parse_note(golden("note_minimal.md"))

    assert (note.summary, note.topic, note.review_at, note.body, note.triggers, note.links) == (
        "Nur eine Zeile", None, None, None, (), ())


def test_a_note_without_a_label_has_no_label_and_may_lack_its_times():
    note = parse_note(golden("note_new.md"))

    assert (note.label, note.topic, note.created, note.updated) == (None, "new:Ideen aus der Cloud", None, None)
    assert str(note.links[0].target) == "note:new-andere"


def test_a_trashed_and_archived_note_keeps_both():
    note = parse_note(golden("note_trashed_archived.md"))

    assert (note.status, note.archived, note.deleted) == (NoteStatus.DONE, True, datetime(2026, 9, 21, 11, 0, tzinfo=UTC))


def test_windows_line_ends_stay():
    text = golden("note_full.md").replace("\n", "\r\n")

    note = parse_note(text)

    assert note.newline == "\r\n" and render_parsed(note) == text


def test_a_stored_note_renders_like_the_golden_file_and_leaves_out_the_links_of_event_triggers():
    at = datetime(2026, 10, 12, 8, 0, tzinfo=UTC)
    note = Note("Mein Projekt", "NOTE-001", "Prüfen, ob der Sync Notes trägt",
                body=parse_note(golden("note_full.md")).body, topic="TOPIC-001",
                review_at=datetime(2026, 11, 7, 8, 0, tzinfo=UTC), trigger_mode=TriggerMode.ALL,
                created=datetime(2026, 10, 1, 9, 30, tzinfo=UTC), updated=datetime(2026, 10, 12, 8, 0, 0, 500000, tzinfo=UTC))
    story = LinkTarget(TargetKind.ITEM, "Mein Projekt", "STORY-003")
    triggers = [Trigger(1, "NOTE-001", TriggerKind.TIME, at=at, fired_at=at),
                Trigger(2, "NOTE-001", TriggerKind.EVENT, target=story, target_status="Completed", fired_at=at,
                        already_met=True, link_id=9),
                Trigger(3, "NOTE-001", TriggerKind.EVENT, target=LinkTarget(TargetKind.ITEM, "Mein Projekt", "STORY-004"),
                        target_status="In progress"),
                Trigger(4, "NOTE-001", TriggerKind.TOPIC_DUE)]
    links = [Link("NOTE-001", "Mein Projekt", LinkTarget(TargetKind.ITEM, "Mein Projekt", "STORY-004"), LinkRole.REFERENCE),
             Link("NOTE-001", "Mein Projekt", story, LinkRole.TRIGGER, 9),
             Link("NOTE-001", "Mein Projekt", LinkTarget(TargetKind.TOPIC, "Mein Projekt", "TOPIC-002"), LinkRole.REFERENCE),
             Link("NOTE-001", "Mein Projekt", LinkTarget(TargetKind.NOTE, "Mein Projekt", "NOTE-007"), LinkRole.REFERENCE),
             Link("NOTE-001", "Mein Projekt", LinkTarget(TargetKind.ITEM, "Mein Projekt", "STORY-009"), LinkRole.ORIGIN)]

    assert render_note(note, triggers, links) == golden("note_full.md")


@pytest.mark.parametrize("text, line, fragment", [
    ("Summary: x\n", 1, "starts with"),
    ("# NOTE-001\nSummary: x\nColour: red\n", 3, "unknown header"),
    ("# NOTE-001\nSummary: x\nStatus: sleeping\n", 3, "invalid Status"),
    ("# NOTE-001\nSummary: x\nReview: tomorrow\n", 3, "not a point in time"),
    ("# NOTE-001\nSummary: x\nArchived: yes\n", 3, "true or false"),
    ("# NOTE-001\nSummary: x\nMode: any\nMode: all\n", 4, "twice"),
    ("# NOTE-001\nSummary: x\n- reference topic:TOPIC-001\n", 3, "outside"),
    ("# NOTE-001\nSummary: x\nTriggers:\n- sometime\n", 4, "unknown trigger"),
    ("# NOTE-001\nSummary: x\nTriggers:\n- event Proj:T-1 Sleeping\n", 4, "names a status"),
    ("# NOTE-001\nSummary: x\nLinks:\n- friend topic:TOPIC-001\n", 4, "unknown link role"),
    ("# NOTE-001\nSummary: x\nLinks:\n- trigger P:T-1\n", 4, "event triggers"),
    ("# NOTE-001\nSummary: x\nLinks:\n- reference nowhere\n", 4, "project:label"),
    ("# not a label\nSummary: x\n", 1, "not a label"),
])
def test_what_does_not_follow_the_format_is_an_error_with_its_line(text: str, line: int, fragment: str):
    with pytest.raises(NoteFormatError) as error:
        parse_note(text, "NOTE-001.md")

    assert error.value.details["line"] == str(line) and fragment in error.value.message and "NOTE-001.md" in error.value.message
    assert error.value.code == "note_format"


def test_a_note_needs_a_summary():
    with pytest.raises(NoteFormatError, match="Summary is missing"):
        parse_note("# NOTE-001\nStatus: waiting\n")


def test_moments_are_utc_and_keep_their_fractions():
    assert format_moment(datetime(2026, 10, 12, 8, 0, tzinfo=UTC)) == "2026-10-12T08:00:00Z"
    assert format_moment(datetime(2026, 10, 12, 8, 0, 0, 120000, tzinfo=UTC)) == "2026-10-12T08:00:00.12Z"


# --- topics ---

def test_topics_read_and_write_back_exactly():
    text = golden("topics.md")

    topics = parse_topics(text)

    assert render_topics(topics) == text
    assert [(t.label, t.name, t.parent) for t in topics] == [
        ("TOPIC-001", "Sync", None), ("TOPIC-002", "Format | Dateien", "TOPIC-001"), ("TOPIC-003", "Tief", "TOPIC-002"),
        ("TOPIC-004", "Zweiter", None), (None, "Ohne Label", "TOPIC-004")]
    assert topics[2].deleted == datetime(2026, 9, 30, 9, 0, tzinfo=UTC) and topics[4].due_at is not None


def test_a_topic_without_a_label_is_known_by_its_name():
    assert TopicLine(None, "Ohne Label").key == "new:Ohne Label"
    assert TopicLine("TOPIC-001", "x").key == "TOPIC-001"


def test_names_with_a_bar_a_backslash_or_a_line_break_survive():
    name = "a | b \\ c\nd"
    text = render_topics([TopicLine("TOPIC-001", name)])

    assert "\n" not in text.rstrip("\n") and parse_topics(text)[0].name == name


def test_stored_topics_render_as_a_tree_under_their_parents():
    stored = [Topic("P", "TOPIC-002", "Child", parent="TOPIC-001"), Topic("P", "TOPIC-001", "Root")]

    assert render_topics(to_lines(stored)).splitlines() == [
        "- TOPIC-001 | Root | due= | created= | deleted=", "  - TOPIC-002 | Child | due= | created= | deleted="]


@pytest.mark.parametrize("text, line", [
    ("TOPIC-001 | x\n", 1), ("- TOPIC-001\n", 1), ("- TOPIC-1x | x\n", 1), ("  - TOPIC-001 | x\n", 1),
    (" - TOPIC-001 | x\n", 1), ("- TOPIC-001 | x\n    - TOPIC-002 | y\n", 2), ("- TOPIC-001 | x | colour=red\n", 1),
    ("- TOPIC-001 | x | due=soon\n", 1)])
def test_a_broken_topics_file_is_an_error_with_its_line(text: str, line: int):
    with pytest.raises(NoteFormatError) as error:
        parse_topics(text)

    assert error.value.details["line"] == str(line)


def test_topics_in_windows_line_ends_stay():
    text = golden("topics.md").replace("\n", "\r\n")

    assert render_topics(parse_topics(text), "\r\n") == text


# --- counters ---

def test_counters_read_and_write_back():
    text = golden("counters.md")

    assert parse_counters(text) == {"note": 15, "topic": 7}
    assert render_counters({"topic": 7, "note": 15}) == text
    assert render_counters({"note": 3}) == "NOTE: 3\n"


@pytest.mark.parametrize("text", ["NOTE 15\n", "NOTES: 3\n", "NOTE: many\n"])
def test_broken_counters_are_an_error(text: str):
    with pytest.raises(NoteFormatError):
        parse_counters(text)

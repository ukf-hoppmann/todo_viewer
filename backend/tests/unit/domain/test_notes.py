from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from todo_viewer.domain.errors import DocumentForbiddenError, TopicLoopError, TopicNotFoundError, TopicTooDeepError
from todo_viewer.domain.notes import (
    Note,
    check_new_topic,
    check_note_document_name,
    check_topic_move,
    format_label,
    subtree_height,
    topic_depth,
    utc,
)

TREE = {"TOPIC-001": None, "TOPIC-002": "TOPIC-001", "TOPIC-003": "TOPIC-002", "TOPIC-004": None}


def test_labels_have_three_digits():
    assert (format_label("note", 7), format_label("topic", 123)) == ("NOTE-007", "TOPIC-123")


def test_depth_counts_levels_from_the_root():
    assert [topic_depth(TREE, t) for t in ("TOPIC-001", "TOPIC-002", "TOPIC-003")] == [1, 2, 3]


def test_depth_of_an_unknown_topic_is_an_error():
    with pytest.raises(TopicNotFoundError):
        topic_depth(TREE, "TOPIC-009")


def test_a_new_topic_below_the_deepest_level_is_refused():
    check_new_topic(TREE, "TOPIC-002", 3, "TOPIC-005")
    with pytest.raises(TopicTooDeepError):
        check_new_topic(TREE, "TOPIC-003", 3, "TOPIC-005")


def test_the_depth_limit_is_configurable():
    check_new_topic(TREE, "TOPIC-003", 4, "TOPIC-005")
    with pytest.raises(TopicTooDeepError):
        check_new_topic(TREE, "TOPIC-001", 1, "TOPIC-005")


def test_subtree_height_counts_the_topic_itself():
    assert (subtree_height(TREE, "TOPIC-001"), subtree_height(TREE, "TOPIC-003")) == (3, 1)


def test_moving_checks_the_depth_of_the_whole_subtree():
    with pytest.raises(TopicTooDeepError):
        check_topic_move(TREE, "TOPIC-001", "TOPIC-004", 3)  # 1 + 3 levels
    check_topic_move(TREE, "TOPIC-002", "TOPIC-004", 3)  # 1 + 2 levels
    check_topic_move(TREE, "TOPIC-003", None, 3)


def test_a_topic_cannot_move_below_itself():
    with pytest.raises(TopicLoopError):
        check_topic_move(TREE, "TOPIC-001", "TOPIC-003", 5)
    with pytest.raises(TopicLoopError):
        check_topic_move(TREE, "TOPIC-001", "TOPIC-001", 5)


@pytest.mark.parametrize("name", ["NOTE-001_notes.md", "NOTE-001_spec.md", "NOTE-001_spec_api.md"])
def test_document_names_of_a_note(name: str):
    check_note_document_name("NOTE-001", name)


@pytest.mark.parametrize("name", ["NOTE-002_notes.md", "NOTE-001.md", "../NOTE-001_notes.md", "NOTE-001_notes.txt"])
def test_other_document_names_are_refused(name: str):
    with pytest.raises(DocumentForbiddenError):
        check_note_document_name("NOTE-001", name)


def test_a_moment_is_converted_to_utc():
    local = datetime(2027, 12, 11, 9, 0, tzinfo=timezone(timedelta(hours=1)))

    assert utc(local) == datetime(2027, 12, 11, 8, 0, tzinfo=UTC)


def test_the_version_changes_with_every_stored_field():
    note = Note(project="p", label="NOTE-001", summary="a")

    assert note.version == Note(project="p", label="NOTE-001", summary="a").version
    assert note.version != Note(project="p", label="NOTE-001", summary="b").version

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    InvalidValueError,
    TopicLoopError,
    TopicNotFoundError,
    TopicTooDeepError,
)
from todo_viewer.domain.notes import (
    Note,
    NotesSettings,
    Topic,
    changed_settings,
    check_new_topic,
    check_note_document_name,
    check_topic_move,
    format_label,
    subtree_height,
    subtree_labels,
    topic_depth,
    topic_path,
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


# ---------- topic paths, subtrees, and the options ----------

TOPICS = [Topic("p", "TOPIC-001", "Ideas"), Topic("p", "TOPIC-002", "Later", parent="TOPIC-001"),
          Topic("p", "TOPIC-003", "Soon", parent="TOPIC-002"), Topic("p", "TOPIC-004", "Other")]


def test_the_path_of_a_topic_runs_from_the_root_down():
    assert topic_path(TOPICS, "TOPIC-003") == ("Ideas", "Later", "Soon")
    assert topic_path(TOPICS, "TOPIC-004") == ("Other",)
    assert topic_path(TOPICS, "TOPIC-009") == ()


def test_the_path_of_a_broken_cycle_ends():
    loop = [Topic("p", "TOPIC-001", "a", parent="TOPIC-002"), Topic("p", "TOPIC-002", "b", parent="TOPIC-001")]

    assert len(topic_path(loop, "TOPIC-001")) <= 3


def test_a_subtree_holds_the_topic_and_everything_below():
    assert subtree_labels(TOPICS, "TOPIC-001") == {"TOPIC-001", "TOPIC-002", "TOPIC-003"}
    assert subtree_labels(TOPICS, "TOPIC-003") == {"TOPIC-003"}
    assert subtree_labels(TOPICS, "TOPIC-004") == {"TOPIC-004"}


def test_changed_settings_keep_what_is_not_given():
    current = NotesSettings(max_topic_depth=3, review_days=30)

    assert changed_settings(current, review_days=7) == NotesSettings(3, 7)
    assert changed_settings(current, max_topic_depth=2) == NotesSettings(2, 30)
    assert changed_settings(current) == current


@pytest.mark.parametrize(("depth", "days", "field"), [(0, None, "max_topic_depth"), (11, None, "max_topic_depth"),
                                                       (None, 0, "review_days"), (None, 3651, "review_days")])
def test_changed_settings_refuse_values_out_of_range(depth, days, field):
    with pytest.raises(InvalidValueError) as caught:
        changed_settings(NotesSettings(), depth, days)

    assert caught.value.details["field"] == field

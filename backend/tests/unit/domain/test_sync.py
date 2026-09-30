from __future__ import annotations

import dataclasses

import pytest

from todo_viewer.domain.errors import (
    BackupFailedError,
    ConflictError,
    SyncPathMissingError,
    SyncRequiredError,
    SyncSameBackendError,
    SyncStaleError,
)
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source, SyncBaseline
from todo_viewer.domain.sync import (
    SyncDirection,
    SyncEntry,
    SyncState,
    check_token,
    classify,
    default_direction,
    fingerprint,
    merged_items,
    plan_sync,
    primary_and_mirror,
    sync_pair,
)


def item(label: str, title: str = "t", **fields: object) -> Item:
    return Item(id=label, title=title, project="P", **fields)  # type: ignore[arg-type]


def test_sync_pair_is_the_database_project_and_its_markdown_folder():
    source = Source(project="P", path="", backend="database", id="abc", sync_path="/data/md")

    for direction in SyncDirection:
        database, markdown = sync_pair(source, direction)

        assert database == source
        assert (markdown.backend, markdown.path, markdown.project, markdown.id) == ("markdown", "/data/md", "P", "abc")


def test_sync_pair_needs_a_sync_path():
    with pytest.raises(SyncPathMissingError) as error:
        sync_pair(Source(project="P", path="", backend="database", id="abc"), SyncDirection.TO_MD)
    assert error.value.code == "sync_path_missing"


def test_a_markdown_project_can_be_read_into_the_database_under_its_id():
    source = Source(project="P", path="docs", backend="markdown", id="abc", sync_path=None)

    database, markdown = sync_pair(source, SyncDirection.FROM_MD)

    assert markdown == source
    assert (database.backend, database.path, database.sync_path, database.id, database.project) == (
        "database", "", None, "abc", "P")


def test_a_markdown_project_without_a_database_mirror_cannot_be_written_anywhere():
    with pytest.raises(SyncSameBackendError) as error:
        sync_pair(Source(project="P", path="docs", backend="markdown", id="abc"), SyncDirection.TO_MD)
    assert error.value.code == "sync_same_backend"


def test_a_markdown_project_with_a_database_mirror_syncs_in_both_directions():
    source = Source(project="P", path="docs", backend="markdown", id="abc", mirror_database=True)

    for direction in SyncDirection:
        database, markdown = sync_pair(source, direction)

        assert markdown == source
        assert (database.backend, database.path, database.id, database.project) == ("database", "", "abc", "P")


def test_the_switch_needs_a_sync_first():
    error = SyncRequiredError()

    assert (error.code, isinstance(error, ConflictError)) == ("sync_required", True)


def test_new_changed_unchanged_and_missing_items_are_told_apart():
    source = [item("TASK-001"), item("TASK-002", "new title"), item("TASK-003")]
    target = [item("TASK-001"), item("TASK-002", "old title"), item("TASK-009", "gone")]

    preview = plan_sync(source, target, {}, {})

    assert [e.label for e in preview.created] == ["TASK-003"]
    assert [e.label for e in preview.changed] == ["TASK-002"]
    assert preview.unchanged == 1
    assert preview.missing == (SyncEntry("item", "TASK-009", "gone"),)


def test_trashed_and_archived_state_counts_as_a_change():
    source = [item("TASK-001", deleted="2026-01-01", location=Location.ARCHIVE)]
    target = [item("TASK-001")]

    assert [e.label for e in plan_sync(source, target, {}, {}).changed] == ["TASK-001"]


def test_documents_are_compared_by_content_including_topic_specs():
    both = [item("STORY-001", "s")]
    source_docs = {("STORY-001", "STORY-001_spec.md"): "same", ("STORY-001", "STORY-001_spec_ui.md"): "new",
                   ("STORY-001", "STORY-001_notes.md"): "after"}
    target_docs = {("STORY-001", "STORY-001_spec.md"): "same", ("STORY-001", "STORY-001_notes.md"): "before",
                   ("STORY-001", "STORY-001_spec_old.md"): "x"}

    preview = plan_sync(both, both, source_docs, target_docs)

    assert preview.created_documents == (SyncEntry("document", "STORY-001", "s", "STORY-001_spec_ui.md"),)
    assert preview.changed_documents == (SyncEntry("document", "STORY-001", "s", "STORY-001_notes.md"),)
    assert preview.missing_documents == (SyncEntry("document", "STORY-001", "s", "STORY-001_spec_old.md"),)
    assert preview.unchanged_documents == 1


def test_documents_of_missing_items_are_not_listed_separately():
    preview = plan_sync([], [item("TASK-009", "gone")], {}, {("TASK-009", "TASK-009_notes.md"): "x"})

    assert preview.missing_documents == ()


def test_documents_of_new_items_are_new():
    preview = plan_sync([item("TASK-001", "t")], [], {("TASK-001", "TASK-001_notes.md"): "x"}, {})

    assert preview.created_documents == (SyncEntry("document", "TASK-001", "t", "TASK-001_notes.md"),)


def test_skipped_entries_are_passed_through():
    skipped = (SyncEntry("document", "TASK-001", "t", "items/TASK-001/photo.png"),)

    assert plan_sync([], [], {}, {}, skipped).skipped == skipped


def test_merged_items_keep_missing_ones_unless_they_are_to_be_deleted():
    source = [item("TASK-002"), item("TASK-001")]
    target = [item("TASK-001"), item("TASK-009")]

    assert [i.id for i in merged_items(source, target, delete_missing=False)] == ["TASK-002", "TASK-001", "TASK-009"]
    assert [i.id for i in merged_items(source, target, delete_missing=True)] == ["TASK-002", "TASK-001"]


def test_token_changes_with_every_change_on_either_side():
    source, target = [item("TASK-001")], [item("TASK-001")]
    base = plan_sync(source, target, {("TASK-001", "a.md"): "x"}, {}).token

    assert plan_sync(source, target, {("TASK-001", "a.md"): "x"}, {}).token == base
    assert plan_sync(source, target, {("TASK-001", "a.md"): "y"}, {}).token != base
    assert plan_sync(source, [item("TASK-001", "other")], {("TASK-001", "a.md"): "x"}, {}).token != base
    assert plan_sync([dataclasses.replace(source[0], status="Completed")], target,
                     {("TASK-001", "a.md"): "x"}, {}).token != base
    assert plan_sync(source, target, {("TASK-001", "a.md"): "x"}, {("TASK-001", "b.md"): "z"}).token != base


def test_check_token_refuses_a_state_that_changed_since_the_preview():
    check_token("abc", "abc")
    with pytest.raises(SyncStaleError) as error:
        check_token("abc", "abd")
    assert error.value.code == "sync_stale"
    with pytest.raises(SyncStaleError):
        check_token(None, "abc")


def test_directions_are_the_api_values():
    assert {d.value for d in SyncDirection} == {"to_md", "from_md"}


def test_the_default_direction_goes_from_the_primary_source_to_the_mirror():
    database = Source(project="P", path="", backend="database", id="abc", sync_path="/md")
    markdown = Source(project="P", path="docs", backend="markdown", id="abc", mirror_database=True)

    assert default_direction(database) is SyncDirection.TO_MD
    assert default_direction(markdown) is SyncDirection.FROM_MD
    assert default_direction(dataclasses.replace(markdown, mirror_database=False)) is SyncDirection.FROM_MD


def test_a_failed_backup_refuses_the_switch_and_names_the_reason():
    error = BackupFailedError("disk full")

    assert (error.code, isinstance(error, ConflictError), error.details) == ("backup_failed", True,
                                                                             {"reason": "disk full"})
    assert "disk full" in error.message and "Nothing was changed" in error.message


def test_a_side_is_fingerprinted_by_its_items_and_documents_regardless_of_order():
    a, b = item("TASK-001", "A"), item("TASK-002", "B")
    docs = {("TASK-001", "notes.md"): "one", ("TASK-002", "notes.md"): "two"}

    same = fingerprint([a, b], docs)

    assert fingerprint([b, a], dict(reversed(list(docs.items())))) == same
    assert fingerprint([a, item("TASK-002", "B changed")], docs) != same
    assert fingerprint([a, b], {**docs, ("TASK-001", "notes.md"): "one, edited"}) != same
    assert fingerprint([a, b], {**docs, ("TASK-001", "spec.md"): "new"}) != same
    assert fingerprint([a], docs) != same


BASE = SyncBaseline(at="2026-09-30T10:00:00+02:00", primary="p0", mirror="m0")


@pytest.mark.parametrize("primary, mirror, state", [
    ("p0", "m0", SyncState.IN_SYNC),
    ("p0", "m1", SyncState.MIRROR_CHANGED),
    ("p1", "m0", SyncState.PRIMARY_CHANGED),
    ("p1", "m1", SyncState.BOTH_CHANGED),
    ("x", "x", SyncState.IN_SYNC),  # both moved to the same content: nothing left to sync
])
def test_the_state_follows_which_side_moved_since_the_last_sync(primary, mirror, state):
    assert classify(primary, mirror, BASE) is state


def test_without_a_last_sync_equal_sides_are_in_sync_and_different_ones_unknown():
    assert classify("x", "x", None) is SyncState.IN_SYNC
    assert classify("x", "y", None) is SyncState.UNKNOWN


def test_what_stayed_different_on_purpose_does_not_count_as_a_change():
    assert classify("p0", "m0", BASE) is SyncState.IN_SYNC  # kept entries make the sides differ for good


def test_primary_and_mirror_are_the_two_sides_of_a_project_with_a_mirror():
    database = Source(project="P", path="", backend="database", id="a", sync_path="/md")
    markdown = Source(project="P", path="/docs", id="b", mirror_database=True)

    primary, mirror = primary_and_mirror(database)  # type: ignore[misc]
    assert (primary.backend, mirror.backend, mirror.path) == ("database", "markdown", "/md")
    primary, mirror = primary_and_mirror(markdown)  # type: ignore[misc]
    assert (primary.backend, primary.path, mirror.backend) == ("markdown", "/docs", "database")
    assert primary_and_mirror(Source(project="P", path="/docs")) is None
    assert primary_and_mirror(Source(project="P", path="", backend="database")) is None

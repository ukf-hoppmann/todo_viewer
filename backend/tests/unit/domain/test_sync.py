from __future__ import annotations

import dataclasses

import pytest

from todo_viewer.domain.errors import SyncPathMissingError, SyncSameBackendError, SyncStaleError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source
from todo_viewer.domain.sync import (
    SyncDirection,
    SyncEntry,
    check_token,
    merged_items,
    plan_sync,
    sync_pair,
)


def item(label: str, title: str = "t", **fields: object) -> Item:
    return Item(id=label, title=title, project="P", **fields)  # type: ignore[arg-type]


def test_sync_pair_is_the_database_project_and_its_markdown_folder():
    source = Source(project="P", path="", backend="database", id="abc", sync_path="/data/md")

    database, markdown = sync_pair(source)

    assert database == source
    assert (markdown.backend, markdown.path, markdown.project, markdown.id) == ("markdown", "/data/md", "P", "abc")


def test_sync_pair_needs_a_sync_path():
    with pytest.raises(SyncPathMissingError) as error:
        sync_pair(Source(project="P", path="", backend="database", id="abc"))
    assert error.value.code == "sync_path_missing"


def test_sync_pair_refuses_markdown_projects():
    with pytest.raises(SyncSameBackendError) as error:
        sync_pair(Source(project="P", path="docs", backend="markdown", id="abc", sync_path="/x"))
    assert error.value.code == "sync_same_backend"


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

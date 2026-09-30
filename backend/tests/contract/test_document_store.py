"""Contract of `DocumentStore`: what every storage adapter has to do the same way."""
from __future__ import annotations

import pytest

from tests.contract.conftest import Adapter
from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    ItemFolderExistsError,
    VersionConflictError,
)


def test_write_creates_documents_and_checks_versions(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    path = "items/TASK-009/TASK-009_spec.md"

    docs.write(source, path, "v1\n", expected_version=None)
    with pytest.raises(VersionConflictError):
        docs.write(source, path, "again\n", expected_version=None)  # exists already
    with pytest.raises(VersionConflictError):
        docs.write(source, path, "v2\n", expected_version=content_version("other"))
    docs.write(source, path, "v2\n", expected_version=content_version("v1\n"))

    assert docs.read(source, path) == "v2\n"
    with pytest.raises(VersionConflictError):
        docs.write(source, "items/TASK-009/missing.md", "x", expected_version=content_version("x"))


def test_append_starts_new_documents_with_a_header(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    path = "items/TASK-009/TASK-009_notes.md"

    first = docs.append(source, path, "## entry 1\n", header="# TASK-009 — t\n")
    second = docs.append(source, path, "## entry 2\n", header="# ignored\n")

    assert first == "# TASK-009 — t\n\n## entry 1\n"
    assert second == "# TASK-009 — t\n\n## entry 1\n\n## entry 2\n"
    assert docs.append(source, "items/TASK-002/notes.md", "## e\n", header="#") == \
        "# Notes for TASK-002\n\nSome *markdown* notes.\n\n## e\n"


def test_reading_a_missing_document_fails(adapter: Adapter):
    with pytest.raises(DocumentNotFoundError):
        adapter.docs.read(adapter.source, "items/TASK-404/TASK-404_spec.md")


def test_paths_outside_the_item_documents_are_forbidden(adapter: Adapter):
    for path in ("../x.md", "items/../../x.md", "items/a/b.json"):
        with pytest.raises(DocumentForbiddenError):
            adapter.docs.write(adapter.source, path, "x", expected_version=None)


def test_deleting_an_item_folder_removes_its_documents_only(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    docs.write(source, "items/TASK-009/TASK-009_spec.md", "keep", expected_version=None)

    docs.delete_item_folder(source, "TASK-002")
    docs.delete_item_folder(source, "TASK-404")  # no folder: nothing to do

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "items/TASK-002/notes.md")
    assert docs.read(source, "items/TASK-009/TASK-009_spec.md") == "keep"
    for bad in ("..", "../b", "", "a/b"):
        with pytest.raises(DocumentForbiddenError):
            docs.delete_item_folder(source, bad)


def test_renaming_an_item_folder_moves_its_documents(adapter: Adapter):
    docs, source = adapter.docs, adapter.source

    docs.rename_item_folder(source, "TASK-002", "STORY-009", {"notes.md": "STORY-009_notes.md"})
    docs.rename_item_folder(source, "TASK-404", "STORY-010", {"x.md": "y.md"})  # no folder: nothing to do

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "items/TASK-002/notes.md")
    assert docs.read(source, "items/STORY-009/STORY-009_notes.md").startswith("# Notes for TASK-002")


def test_renaming_refuses_existing_targets_and_bad_names(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    docs.write(source, "items/STORY-009/STORY-009_spec.md", "x", expected_version=None)

    with pytest.raises(ItemFolderExistsError):
        docs.rename_item_folder(source, "TASK-002", "STORY-009", {})
    for old, new, renames in [("..", "X-1", {}), ("TASK-002", "../x", {}), ("TASK-002", "a/b", {}),
                              ("TASK-002", "X-1", {"notes.md": "../out.md"}), ("TASK-002", "X-1", {"../a": "b"})]:
        with pytest.raises(DocumentForbiddenError):
            docs.rename_item_folder(source, old, new, renames)

    assert docs.read(source, "items/TASK-002/notes.md").startswith("# Notes for TASK-002")
    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "items/X-1/notes.md")

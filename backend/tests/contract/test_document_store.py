"""Contract of `DocumentStore`: what every storage adapter has to do the same way.

Documents belong to items that exist; what a store does with documents of unknown items is not part of the
contract. Relabeling is tested as the retype does it: documents first, then the item's id.
"""
from __future__ import annotations

import pytest

from tests.contract.conftest import Adapter
from todo_viewer.domain.documents import content_version
from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import (
    DocumentForbiddenError,
    DocumentNotFoundError,
    ItemFolderExistsError,
    VersionConflictError,
)


def _retype(adapter: Adapter, old_id: str, new_id: str, renames: dict[str, str]) -> None:
    adapter.docs.relabel_documents(adapter.source, old_id, new_id, renames)
    item = adapter.repo.get(adapter.source, old_id)
    adapter.repo.apply(adapter.source, item, ChangeSet(set_fields=(("id", new_id), ("type", "Story"))))


def test_write_creates_documents_and_checks_versions(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    name = "TASK-001_spec.md"

    docs.write(source, "TASK-001", name, "v1\n", expected_version=None)
    with pytest.raises(VersionConflictError):
        docs.write(source, "TASK-001", name, "again\n", expected_version=None)  # exists already
    with pytest.raises(VersionConflictError):
        docs.write(source, "TASK-001", name, "v2\n", expected_version=content_version("other"))
    docs.write(source, "TASK-001", name, "v2\n", expected_version=content_version("v1\n"))

    assert docs.read(source, "TASK-001", name) == "v2\n"
    with pytest.raises(VersionConflictError):
        docs.write(source, "TASK-001", "missing.md", "x", expected_version=content_version("x"))


def test_documents_belong_to_their_item(adapter: Adapter):
    docs, source = adapter.docs, adapter.source

    docs.write(source, "TASK-001", "TASK-001_spec.md", "mine\n", expected_version=None)

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "TASK-003", "TASK-001_spec.md")


def test_append_starts_new_documents_with_a_header(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    name = "TASK-001_notes.md"

    first = docs.append(source, "TASK-001", name, "## entry 1\n", header="# TASK-001 — t\n")
    second = docs.append(source, "TASK-001", name, "## entry 2\n", header="# ignored\n")

    assert first == "# TASK-001 — t\n\n## entry 1\n"
    assert second == "# TASK-001 — t\n\n## entry 1\n\n## entry 2\n"
    assert docs.append(source, "TASK-002", "notes.md", "## e\n", header="#") == \
        "# Notes for TASK-002\n\nSome *markdown* notes.\n\n## e\n"


def test_reading_a_missing_document_fails(adapter: Adapter):
    for item_id, name in (("TASK-001", "TASK-001_spec.md"), ("TASK-404", "TASK-404_spec.md")):
        with pytest.raises(DocumentNotFoundError):
            adapter.docs.read(adapter.source, item_id, name)


def test_names_and_ids_that_could_leave_the_item_are_forbidden(adapter: Adapter):
    for item_id, name in (("TASK-002", "../../../x.md"), ("TASK-002", "b.json"), ("..", "x.md"), ("a/b", "x.md"),
                          ("TASK-002", "")):
        with pytest.raises(DocumentForbiddenError):
            adapter.docs.write(adapter.source, item_id, name, "x", expected_version=None)


def test_deleting_removes_the_documents_of_one_item_only(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    docs.write(source, "TASK-001", "TASK-001_spec.md", "keep", expected_version=None)

    docs.delete_documents(source, "TASK-002")
    docs.delete_documents(source, "TASK-404")  # no documents: nothing to do

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "TASK-002", "notes.md")
    assert docs.read(source, "TASK-001", "TASK-001_spec.md") == "keep"
    for bad in ("..", "../b", "", "a/b"):
        with pytest.raises(DocumentForbiddenError):
            docs.delete_documents(source, bad)


def test_documents_follow_a_new_id(adapter: Adapter):
    docs, source = adapter.docs, adapter.source

    _retype(adapter, "TASK-002", "STORY-009", {"notes.md": "STORY-009_notes.md"})
    docs.relabel_documents(source, "TASK-404", "STORY-010", {"x.md": "y.md"})  # no documents: nothing to do

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "TASK-002", "notes.md")
    assert docs.read(source, "STORY-009", "STORY-009_notes.md").startswith("# Notes for TASK-002")


def test_relabeling_back_before_the_id_changes_restores_the_documents(adapter: Adapter):
    docs, source = adapter.docs, adapter.source

    docs.relabel_documents(source, "TASK-002", "STORY-009", {"notes.md": "STORY-009_notes.md"})
    docs.relabel_documents(source, "STORY-009", "TASK-002", {"STORY-009_notes.md": "notes.md"})

    assert docs.read(source, "TASK-002", "notes.md").startswith("# Notes for TASK-002")


def test_relabeling_refuses_ids_with_documents_and_bad_names(adapter: Adapter):
    docs, source = adapter.docs, adapter.source
    docs.write(source, "TASK-001", "TASK-001_spec.md", "x", expected_version=None)

    with pytest.raises(ItemFolderExistsError):
        docs.relabel_documents(source, "TASK-001", "TASK-002", {})
    for old, new, renames in [("..", "X-1", {}), ("TASK-002", "../x", {}), ("TASK-002", "a/b", {}),
                              ("TASK-002", "X-1", {"notes.md": "../out.md"}), ("TASK-002", "X-1", {"../a": "b"})]:
        with pytest.raises(DocumentForbiddenError):
            docs.relabel_documents(source, old, new, renames)

    assert docs.read(source, "TASK-002", "notes.md").startswith("# Notes for TASK-002")
    assert docs.read(source, "TASK-001", "TASK-001_spec.md") == "x"

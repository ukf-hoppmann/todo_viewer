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


def test_write_creates_documents_and_checks_versions(docs_adapter: Adapter):
    docs, source = docs_adapter.docs, docs_adapter.source
    name = "TASK-009_spec.md"

    docs.write(source, "TASK-009", name, "v1\n", expected_version=None)
    with pytest.raises(VersionConflictError):
        docs.write(source, "TASK-009", name, "again\n", expected_version=None)  # exists already
    with pytest.raises(VersionConflictError):
        docs.write(source, "TASK-009", name, "v2\n", expected_version=content_version("other"))
    docs.write(source, "TASK-009", name, "v2\n", expected_version=content_version("v1\n"))

    assert docs.read(source, "TASK-009", name) == "v2\n"
    with pytest.raises(VersionConflictError):
        docs.write(source, "TASK-009", "missing.md", "x", expected_version=content_version("x"))


def test_documents_belong_to_their_item(docs_adapter: Adapter):
    docs, source = docs_adapter.docs, docs_adapter.source

    docs.write(source, "TASK-009", "TASK-009_spec.md", "mine\n", expected_version=None)

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "TASK-008", "TASK-009_spec.md")


def test_append_starts_new_documents_with_a_header(docs_adapter: Adapter):
    docs, source = docs_adapter.docs, docs_adapter.source
    name = "TASK-009_notes.md"

    first = docs.append(source, "TASK-009", name, "## entry 1\n", header="# TASK-009 — t\n")
    second = docs.append(source, "TASK-009", name, "## entry 2\n", header="# ignored\n")

    assert first == "# TASK-009 — t\n\n## entry 1\n"
    assert second == "# TASK-009 — t\n\n## entry 1\n\n## entry 2\n"
    assert docs.append(source, "TASK-002", "notes.md", "## e\n", header="#") == \
        "# Notes for TASK-002\n\nSome *markdown* notes.\n\n## e\n"


def test_reading_a_missing_document_fails(docs_adapter: Adapter):
    with pytest.raises(DocumentNotFoundError):
        docs_adapter.docs.read(docs_adapter.source, "TASK-404", "TASK-404_spec.md")


def test_names_and_ids_that_could_leave_the_item_are_forbidden(docs_adapter: Adapter):
    for item_id, name in (("TASK-002", "../../../x.md"), ("TASK-002", "b.json"), ("..", "x.md"), ("a/b", "x.md"),
                          ("TASK-002", "")):
        with pytest.raises(DocumentForbiddenError):
            docs_adapter.docs.write(docs_adapter.source, item_id, name, "x", expected_version=None)


def test_deleting_removes_the_documents_of_one_item_only(docs_adapter: Adapter):
    docs, source = docs_adapter.docs, docs_adapter.source
    docs.write(source, "TASK-009", "TASK-009_spec.md", "keep", expected_version=None)

    docs.delete_documents(source, "TASK-002")
    docs.delete_documents(source, "TASK-404")  # no documents: nothing to do

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "TASK-002", "notes.md")
    assert docs.read(source, "TASK-009", "TASK-009_spec.md") == "keep"
    for bad in ("..", "../b", "", "a/b"):
        with pytest.raises(DocumentForbiddenError):
            docs.delete_documents(source, bad)


def test_relabeling_moves_the_documents_to_the_new_id(docs_adapter: Adapter):
    docs, source = docs_adapter.docs, docs_adapter.source

    docs.relabel_documents(source, "TASK-002", "STORY-009", {"notes.md": "STORY-009_notes.md"})
    docs.relabel_documents(source, "TASK-404", "STORY-010", {"x.md": "y.md"})  # no documents: nothing to do

    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "TASK-002", "notes.md")
    assert docs.read(source, "STORY-009", "STORY-009_notes.md").startswith("# Notes for TASK-002")
    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "STORY-010", "y.md")


def test_relabeling_refuses_ids_with_documents_and_bad_names(docs_adapter: Adapter):
    docs, source = docs_adapter.docs, docs_adapter.source
    docs.write(source, "STORY-009", "STORY-009_spec.md", "x", expected_version=None)

    with pytest.raises(ItemFolderExistsError):
        docs.relabel_documents(source, "TASK-002", "STORY-009", {})
    for old, new, renames in [("..", "X-1", {}), ("TASK-002", "../x", {}), ("TASK-002", "a/b", {}),
                              ("TASK-002", "X-1", {"notes.md": "../out.md"}), ("TASK-002", "X-1", {"../a": "b"})]:
        with pytest.raises(DocumentForbiddenError):
            docs.relabel_documents(source, old, new, renames)

    assert docs.read(source, "TASK-002", "notes.md").startswith("# Notes for TASK-002")
    with pytest.raises(DocumentNotFoundError):
        docs.read(source, "X-1", "notes.md")

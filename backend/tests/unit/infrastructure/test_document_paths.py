"""Markdown keeps documents in `items/<ID>/`; the rest of the application only knows item ids and names."""
from __future__ import annotations

from pathlib import Path

import pytest

from todo_viewer.domain.errors import DocumentForbiddenError
from todo_viewer.infrastructure.markdown.document_paths import document_file, name_of, path_of


def test_paths_in_the_items_folder_become_plain_names():
    assert name_of("TASK-002", "items/TASK-002/notes.md") == "notes.md"
    assert name_of("TASK-002", "items/TASK-002/TASK-002_spec_api.md") == "TASK-002_spec_api.md"


def test_other_paths_are_kept_as_they_are():
    assert name_of("TASK-002", "items/TASK-003/notes.md") == "items/TASK-003/notes.md"
    assert name_of("TASK-002", "items/TASK-002/sub/x.md") == "items/TASK-002/sub/x.md"
    assert name_of("TASK-002", "docs/x.md") == "docs/x.md"


def test_names_become_paths_of_the_given_item():
    assert path_of("STORY-009", "notes.md") == "items/STORY-009/notes.md"
    assert path_of("STORY-009", "docs/x.md") == "docs/x.md"


def test_document_files_stay_inside_the_backlog(tmp_path: Path):
    base = tmp_path / "b"

    assert document_file(base, "TASK-002", "notes.md") == (base / "items" / "TASK-002" / "notes.md").resolve()
    assert document_file(base, "TASK-002", "docs/x.md") == (base / "docs" / "x.md").resolve()
    for item_id, name in [("TASK-002", "../../x.md"), ("TASK-002", "x.json"), ("..", "x.md"), ("a/b", "x.md"),
                          ("TASK-002", "")]:
        with pytest.raises(DocumentForbiddenError):
            document_file(base, item_id, name)

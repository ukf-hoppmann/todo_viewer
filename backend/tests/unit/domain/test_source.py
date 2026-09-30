from __future__ import annotations

from todo_viewer.domain.source import Source


def test_source_uses_the_markdown_backend_by_default():
    assert Source(project="P", path="docs").backend == "markdown"


def test_updated_source_keeps_its_backend():
    source = Source(project="P", path="docs", backend="database")

    updated = source.updated("Q", "other")

    assert (updated.project, updated.path, updated.backend) == ("Q", "other", "database")


def test_a_source_keeps_its_id_when_name_or_path_change():
    source = Source(project="P", path="docs", id="3f0c9a4e-0000-4000-8000-000000000001")

    updated = source.updated("Q", "other")

    assert updated.id == "3f0c9a4e-0000-4000-8000-000000000001"

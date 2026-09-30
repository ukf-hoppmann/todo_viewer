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


def test_markdown_path_is_the_folder_on_either_side():
    markdown = Source(project="P", path="docs")
    database = Source(project="P", path="", backend="database", sync_path="/md")

    assert (markdown.markdown_path, database.markdown_path) == ("docs", "/md")
    assert Source(project="P", path="", backend="database").markdown_path is None


def test_the_mirror_is_the_other_side_when_it_is_kept():
    assert Source(project="P", path="docs").mirror == "none"
    assert Source(project="P", path="docs", mirror_database=True).mirror == "database"
    assert Source(project="P", path="", backend="database").mirror == "none"
    assert Source(project="P", path="", backend="database", sync_path="/md").mirror == "markdown"


def test_updated_source_keeps_its_database_mirror():
    source = Source(project="P", path="docs", mirror_database=True)

    assert source.updated("Q", "other").mirror_database is True


def test_a_database_project_keeps_its_folder_while_the_mirror_is_off():
    on = Source(project="P", path="", backend="database", sync_path="/md")
    off = Source(project="P", path="", backend="database", sync_path="/md", mirror_disabled=True)

    assert (on.mirror, off.mirror) == ("markdown", "none")
    assert (on.markdown_path, off.markdown_path) == ("/md", "/md")
    assert Source(project="P", path="", backend="database", mirror_disabled=True).mirror == "none"


def test_switching_a_mirror_off_does_not_touch_a_markdown_project():
    assert Source(project="P", path="docs", mirror_database=True, mirror_disabled=True).mirror == "database"

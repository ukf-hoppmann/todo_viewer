"""`write_backlog` on markdown files: what happens to the text around the entries and to missing files."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from todo_viewer.domain.errors import FileChangedError, InvalidSourceError
from todo_viewer.domain.item import Item, Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown import build_markdown_repository

FIXTURE = Path(__file__).parents[2] / "fixtures" / "backlog"


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    shutil.copytree(FIXTURE, tmp_path / "b")
    return tmp_path / "b"


def _source(folder: Path) -> Source:
    return Source(project="P", path=str(folder))


def test_text_around_the_entries_stays(folder: Path):
    repo = build_markdown_repository(Path("/"))
    items = repo.load(_source(folder)).items

    repo.write_backlog(_source(folder), items, "en")

    text = (folder / "TODO.md").read_text(encoding="utf-8")
    assert text.startswith("# Backlog\n\nExample backlog format version 2 for the test suite.\n")
    assert "- `NOT-AN-ENTRY` **Entries before the work items section are ignored**" in text
    assert text.rstrip().endswith("## Other section\n\nFree text ends the last entry.")


def test_writing_twice_gives_identical_files(folder: Path):
    repo = build_markdown_repository(Path("/"))
    repo.write_backlog(_source(folder), repo.load(_source(folder)).items, "en")
    first = {name: (folder / name).read_text(encoding="utf-8") for name in ("TODO.md", "archive.md")}

    repo.write_backlog(_source(folder), repo.load(_source(folder)).items, "en")

    assert {name: (folder / name).read_text(encoding="utf-8") for name in first} == first


def test_a_missing_archive_is_created_in_the_given_language(folder: Path):
    (folder / "archive.md").unlink()
    repo = build_markdown_repository(Path("/"))
    active = [i for i in repo.load(_source(folder)).items if i.location is Location.ACTIVE]
    done = Item(id="TASK-100", title="Done", project="P", status="Completed", location=Location.ARCHIVE)

    repo.write_backlog(_source(folder), [*active, done], "de")

    archive = (folder / "archive.md").read_text(encoding="utf-8")
    assert archive.startswith("# Projekt-Backlog-Archiv")
    assert "- `TASK-100` **Done**" in archive


def test_an_empty_list_leaves_the_no_entries_line(folder: Path):
    repo = build_markdown_repository(Path("/"))

    repo.write_backlog(_source(folder), [], "en")

    assert "No entries." in (folder / "archive.md").read_text(encoding="utf-8")
    assert repo.load(_source(folder)).items == []


def test_a_folder_without_backlog_is_refused_and_nothing_is_created(tmp_path: Path):
    repo = build_markdown_repository(Path("/"))

    with pytest.raises(InvalidSourceError) as error:
        repo.write_backlog(_source(tmp_path / "missing"), [], "en")

    assert error.value.code == "not_found"
    assert not (tmp_path / "missing").exists()


def test_a_file_changed_since_it_was_read_is_not_overwritten(folder: Path, monkeypatch: pytest.MonkeyPatch):
    repo = build_markdown_repository(Path("/"))
    items = repo.load(_source(folder)).items
    real_read = repo._files.read  # noqa: SLF001

    def read_then_change(path: Path):  # type: ignore[no-untyped-def]
        doc = real_read(path)
        if path.name == "archive.md":
            path.write_text(path.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
        return doc

    monkeypatch.setattr(repo._files, "read", read_then_change)  # noqa: SLF001

    with pytest.raises(FileChangedError):
        repo.write_backlog(_source(folder), items, "en")

    assert (folder / "TODO.md").read_text(encoding="utf-8") == (FIXTURE / "TODO.md").read_text(encoding="utf-8")

"""The byte-exact copy of a markdown backlog that precedes a switch of the primary source."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown.backup import MarkdownRawBackup
from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver

FIXTURE = Path(__file__).parents[2] / "fixtures" / "backlog"


@pytest.fixture
def backup() -> MarkdownRawBackup:
    return MarkdownRawBackup(LayoutFactory(SourcePathResolver(Path("/"))))


def _files(folder: Path) -> dict[str, bytes]:
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_the_backlog_files_are_copied_byte_for_byte(backup: MarkdownRawBackup, tmp_path: Path):
    folder = tmp_path / "docs"
    shutil.copytree(FIXTURE, folder)
    (folder / "TODO.md").write_bytes(b"# Backlog\r\n\r\nhand written   \r\n")  # odd formatting must survive

    copied = backup.copy(Source(project="P", path=str(folder)), str(tmp_path / "backup" / "1"))

    assert copied is True
    assert _files(tmp_path / "backup" / "1") == _files(folder)


def test_files_that_are_not_part_of_the_backlog_are_left_out(backup: MarkdownRawBackup, tmp_path: Path):
    folder = tmp_path / "docs"
    shutil.copytree(FIXTURE, folder)
    (folder / "notes.txt").write_text("unrelated", encoding="utf-8")

    backup.copy(Source(project="P", path=str(folder)), str(tmp_path / "b"))

    assert set(_files(tmp_path / "b")) == {"TODO.md", "archive.md", "items/TASK-002/notes.md"}


def test_a_backlog_without_archive_or_items_is_copied_as_it_is(backup: MarkdownRawBackup, tmp_path: Path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "TODO.md").write_text("# Backlog\n", encoding="utf-8")

    backup.copy(Source(project="P", path=str(folder)), str(tmp_path / "b"))

    assert _files(tmp_path / "b") == {"TODO.md": b"# Backlog\n"}


def test_a_target_that_cannot_be_written_raises(backup: MarkdownRawBackup, tmp_path: Path):
    folder = tmp_path / "docs"
    shutil.copytree(FIXTURE, folder)
    blocker = tmp_path / "blocked"
    blocker.write_text("a file, not a folder", encoding="utf-8")

    with pytest.raises(OSError):
        backup.copy(Source(project="P", path=str(folder)), str(blocker / "inside"))


def test_a_copy_that_differs_from_the_original_is_not_reported_as_done(backup: MarkdownRawBackup, tmp_path: Path,
                                                                        monkeypatch: pytest.MonkeyPatch):
    folder = tmp_path / "docs"
    shutil.copytree(FIXTURE, folder)
    monkeypatch.setattr(shutil, "copy2", lambda src, dst, **_: Path(dst).write_bytes(b"corrupt"))

    with pytest.raises(OSError, match="differs"):
        backup.copy(Source(project="P", path=str(folder)), str(tmp_path / "b"))

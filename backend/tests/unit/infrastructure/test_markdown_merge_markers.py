"""Files with Git merge markers are found, so an automatic sync does not read half-merged text."""
from __future__ import annotations

from pathlib import Path

from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver
from todo_viewer.infrastructure.markdown.merge_markers import MarkdownMergeMarkers

CONFLICTED = "before\n<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> origin/main\nafter\n"


def _check(folder: Path) -> list[str]:
    return MarkdownMergeMarkers(LayoutFactory(SourcePathResolver(Path("/")))).files_with_markers(
        Source(project="P", path=str(folder)))


def test_a_clean_folder_has_no_files_with_markers(tmp_path: Path):
    # a setext underline is no marker
    (tmp_path / "TODO.md").write_text("# Backlog\n\nTitle\n=======\n", encoding="utf-8")

    assert _check(tmp_path) == []


def test_the_backlog_files_and_item_documents_are_checked(tmp_path: Path):
    (tmp_path / "items" / "TASK-1").mkdir(parents=True)
    (tmp_path / "TODO.md").write_text(CONFLICTED, encoding="utf-8")
    (tmp_path / "archive.md").write_text("fine\n", encoding="utf-8")
    (tmp_path / "items" / "TASK-1" / "TASK-1_notes.md").write_text(CONFLICTED, encoding="utf-8")
    (tmp_path / "items" / "TASK-1" / "TASK-1_spec.md").write_text("fine\n", encoding="utf-8")

    assert _check(tmp_path) == ["TODO.md", "items/TASK-1/TASK-1_notes.md"]


def test_a_start_marker_without_an_end_marker_is_text(tmp_path: Path):
    (tmp_path / "TODO.md").write_text("<<<<<<< not a conflict\n", encoding="utf-8")

    assert _check(tmp_path) == []


def test_a_missing_or_unreadable_file_is_not_a_marker(tmp_path: Path):
    (tmp_path / "TODO.md").write_bytes(b"\xff\xfe\x00 not utf-8")

    assert _check(tmp_path) == []
    assert _check(tmp_path / "nowhere") == []

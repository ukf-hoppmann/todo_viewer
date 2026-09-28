from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import (
    DuplicateItemError,
    FileChangedError,
    InvalidSourceError,
    ItemNotFoundError,
    VersionConflictError,
)
from todo_viewer.domain.item import Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown import build_markdown_repository
from todo_viewer.infrastructure.markdown.detector import FormatDetector
from todo_viewer.infrastructure.markdown.editors import BacklogEntryEditor, EntryLocator, EntryMover
from todo_viewer.infrastructure.markdown.field_mapper import PriorityNormalizer, extract_paths
from todo_viewer.infrastructure.markdown.text_file import TextFileStore

FIXTURES = Path(__file__).parents[2] / "fixtures"


# ---------- TextFileStore ----------

def test_text_file_keeps_crlf_and_trailing_newline(tmp_path):
    path = tmp_path / "f.md"
    path.write_bytes(b"a\r\nb\r\n")
    store = TextFileStore()

    doc = store.read(path)
    doc.lines[0] = "A"
    store.write(doc)

    assert doc.lines == ["A", "b", ""]
    assert path.read_bytes() == b"A\r\nb\r\n"


def test_text_file_refuses_to_overwrite_external_change(tmp_path):
    path = tmp_path / "f.md"
    path.write_text("one\n", encoding="utf-8")
    store = TextFileStore()
    doc = store.read(path)

    path.write_text("changed by someone else\n", encoding="utf-8")
    os.utime(path, ns=(doc.stamp.mtime_ns + 1_000_000, doc.stamp.mtime_ns + 1_000_000))
    with pytest.raises(FileChangedError):
        store.write(doc)

    assert path.read_text(encoding="utf-8") == "changed by someone else\n"


def test_text_file_write_is_atomic_and_keeps_mode(tmp_path):
    path = tmp_path / "f.md"
    path.write_text("x\n", encoding="utf-8")
    path.chmod(0o640)
    store = TextFileStore()

    doc = store.read(path)
    doc.lines[0] = "y"
    store.write(doc)

    assert oct(path.stat().st_mode & 0o777) == oct(0o640)
    assert [p.name for p in tmp_path.iterdir()] == ["f.md"]  # no temp file left behind


# ---------- small parts ----------

def test_detector():
    detector = FormatDetector()

    assert detector.is_backlog("backlog format version 2\n- `T-1` **x**\n")
    assert detector.is_backlog("Claude_Harness-Backlog-Format Version 1.\n\nNo entries.\n")
    assert not detector.is_backlog("- [ ] a")


def test_locator_finds_entry_by_id_inside_work_items():
    lines = ["- `T-1` **before the section**", "## Work items", "", "- `T-2` **x**", "- `T-1` **y**"]
    locator = EntryLocator()

    assert locator.locate(lines, "T-1") == 4
    with pytest.raises(ItemNotFoundError):
        locator.locate(lines, "T-9")
    with pytest.raises(DuplicateItemError):
        locator.locate([*lines, "- `T-2` **again**"], "T-2")


def test_priority_normalizer_and_paths():
    assert PriorityNormalizer().normalize("WICHTIG") == "Important"
    assert PriorityNormalizer().normalize("Custom") == "Custom"
    assert extract_paths("`a.md`, `b.md`.") == ["a.md", "b.md"]
    assert extract_paths("None.") == []


def test_entry_editor_replaces_continuation_lines_and_inserts_missing_fields():
    lines = ["- `T-1` **x**", "  - Status: Open.", "  - Resolution: a", "    b", "", "rest"]
    editor = BacklogEntryEditor()

    editor.set_field(lines, 0, "resolution", "done")
    editor.set_field(lines, 0, "priority", "Urgent")

    assert lines == ["- `T-1` **x**", "  - Status: Open.", "  - Resolution: done.", "  - Priority: Urgent.", "",
                     "rest"]


def test_entry_editor_writes_title_ids_and_wrapped_text():
    lines = ["- `T-1` **Old**", "  - Type: Task.", "  - Parent: `S-1`.", "  - Dependencies: None.",
             "  - Goal: short.", "", "rest"]
    editor = BacklogEntryEditor()
    long_goal = "A goal that is long enough to need more than one line in the file, " \
                "so it wraps like the backlog format expects"

    editor.set_field(lines, 0, "title", "New title")
    editor.set_field(lines, 0, "parent", None)
    editor.set_field(lines, 0, "dependencies", ("A-1", "B-2"))
    editor.set_field(lines, 0, "goal", long_goal)
    editor.set_field(lines, 0, "summary", "Short")

    assert lines == [
        "- `T-1` **New title**",
        "  - Type: Task.",
        "  - Parent: None.",
        "  - Dependencies: `A-1`, `B-2`.",
        "  - Goal: A goal that is long enough to need more than one line in the file,",
        "    so it wraps like the backlog format expects.",
        "  - Summary: Short.",
        "",
        "rest",
    ]
    assert all(len(line) <= 76 for line in lines)
    editor.set_field(lines, 0, "dependencies", ())
    assert lines[3] == "  - Dependencies: None."


def test_mover_writes_no_entries_marker_when_section_empties():
    lines = ["## Work items", "", "- `T-1` **x**", "  - Status: Open.", ""]
    mover = EntryMover()

    block = mover.cut(lines, 2)

    assert block == ["- `T-1` **x**", "  - Status: Open."]
    assert lines == ["## Work items", "", "No entries.", ""]


# ---------- repository ----------

@pytest.fixture
def backlog(tmp_path) -> Source:
    shutil.copytree(FIXTURES / "backlog", tmp_path / "b")
    return Source(project="P", path=str(tmp_path / "b"))


def test_repository_get_by_id_in_both_files(backlog):
    repo = build_markdown_repository(Path("/"))

    assert repo.get(backlog, "TASK-001").location is Location.ACTIVE
    assert repo.get(backlog, "TASK-000").location is Location.ARCHIVE
    with pytest.raises(ItemNotFoundError):
        repo.get(backlog, "NOT-AN-ENTRY")  # before `## Work items`


def test_repository_get_rejects_duplicate_ids(backlog):
    todo = Path(backlog.path) / "TODO.md"
    todo.write_text(todo.read_text(encoding="utf-8") + "\n- `TASK-000` **Same id as an archived item**\n",
                    encoding="utf-8")
    repo = build_markdown_repository(Path("/"))

    with pytest.raises(DuplicateItemError):
        repo.get(backlog, "TASK-000")


def test_repository_apply_rejects_item_changed_in_the_meantime(backlog):
    repo = build_markdown_repository(Path("/"))
    item = repo.get(backlog, "TASK-001")
    repo.apply(backlog, item, ChangeSet(set_fields=(("priority", "Urgent"),)))
    before = (Path(backlog.path) / "TODO.md").read_bytes()

    with pytest.raises(VersionConflictError):
        repo.apply(backlog, item, ChangeSet(set_fields=(("priority", "Normal"),)))

    assert (Path(backlog.path) / "TODO.md").read_bytes() == before


def test_repository_rejects_files_without_backlog_format(tmp_path):
    shutil.copytree(FIXTURES / "checklist", tmp_path / "c")
    source = Source(project="C", path=str(tmp_path / "c"))
    repo = build_markdown_repository(Path("/"))

    assert repo.check(source).code == "unsupported_format"
    assert repo.load(source).items == []
    with pytest.raises(InvalidSourceError):
        repo.get(source, "anything")


def test_repository_move_returns_item_at_new_place(backlog):
    repo = build_markdown_repository(Path("/"))
    item = repo.get(backlog, "TASK-001")

    moved = repo.apply(backlog, item, ChangeSet(set_fields=(("status", "Completed"), ("resolution", "ok")),
                                                move_to=Location.ARCHIVE))

    assert (moved.location, moved.status, moved.resolution) == (Location.ARCHIVE, "Completed", "ok.")
    assert "- `TASK-001` **" not in (Path(backlog.path) / "TODO.md").read_text(encoding="utf-8")


def test_repository_relative_source_path(tmp_path):
    shutil.copytree(FIXTURES / "backlog", tmp_path / "docs")
    repo = build_markdown_repository(tmp_path)

    assert repo.check(Source(project="P", path="docs")) is None
    assert len(repo.load(Source(project="P", path="docs")).items) == 7

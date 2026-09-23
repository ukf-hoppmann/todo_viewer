from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import EntryMovedError, FileChangedError
from todo_viewer.domain.item import ItemFormat, ItemRef, Location
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.markdown import build_markdown_repository
from todo_viewer.infrastructure.markdown.detector import FormatDetector
from todo_viewer.infrastructure.markdown.editors import BacklogEntryEditor, EntryMover
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
    backlog = "backlog format version 2\n- `T-1` **x**\n"

    assert detector.detect(backlog, Location.ACTIVE) is ItemFormat.BACKLOG_V2
    assert detector.detect("- [ ] a", Location.ACTIVE) is ItemFormat.CHECKBOX
    assert detector.detect("No entries.", Location.ARCHIVE) is None


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


def test_repository_find_checks_line(backlog):
    repo = build_markdown_repository(Path("/"))
    item = next(i for i in repo.load(backlog).items if i.id == "TASK-001")

    assert repo.find(backlog, item.ref) == item
    with pytest.raises(EntryMovedError):
        repo.find(backlog, ItemRef("TASK-001", Location.ACTIVE, item.line + 1))
    with pytest.raises(EntryMovedError):
        repo.find(backlog, ItemRef("TASK-001", Location.ARCHIVE, item.line))


def test_repository_move_returns_item_at_new_place(backlog):
    repo = build_markdown_repository(Path("/"))
    item = next(i for i in repo.load(backlog).items if i.id == "TASK-001")

    moved = repo.apply(backlog, item, ChangeSet(set_fields=(("status", "Completed"), ("resolution", "ok")),
                                                move_to=Location.ARCHIVE))

    assert (moved.location, moved.status, moved.resolution) == (Location.ARCHIVE, "Completed", "ok.")
    assert "- `TASK-001` **" not in (Path(backlog.path) / "TODO.md").read_text(encoding="utf-8")


def test_repository_relative_source_path(tmp_path):
    shutil.copytree(FIXTURES / "backlog", tmp_path / "docs")
    repo = build_markdown_repository(tmp_path)

    assert repo.check(Source(project="P", path="docs")) is None
    assert len(repo.load(Source(project="P", path="docs")).items) == 7

from __future__ import annotations

import dataclasses
import os
import shutil
from pathlib import Path

import pytest

from todo_viewer.domain.editing import ChangeSet
from todo_viewer.domain.errors import (
    DuplicateItemError,
    FileChangedError,
    InvalidSourceError,
    InvalidValueError,
    ItemNotFoundError,
    VersionConflictError,
)
from todo_viewer.domain.item import Item, Location
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


# ---------- initialize ----------

def test_initialize_keeps_an_existing_archive_and_rejects_bad_targets(tmp_path):
    repo = build_markdown_repository(tmp_path)
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "archive.md").write_text("kept\n", encoding="utf-8")
    (tmp_path / "file").write_text("", encoding="utf-8")

    repo.initialize(Source("P", str(folder)), "en")
    with pytest.raises(InvalidSourceError) as not_a_dir:
        repo.initialize(Source("P", str(tmp_path / "file")), "en")
    with pytest.raises(InvalidValueError):
        repo.initialize(Source("P", str(tmp_path / "other")), "fr")

    assert (folder / "archive.md").read_text(encoding="utf-8") == "kept\n"
    assert repo.check(Source("P", str(folder))) is None
    assert repo.load(Source("P", str(folder))).items == []
    assert not_a_dir.value.code == "not_a_dir"
    assert not (tmp_path / "other").exists()


# ---------- small parts ----------

def test_detector():
    detector = FormatDetector()

    assert detector.is_backlog("backlog format version 2\n- `T-1` **x**\n")
    assert detector.is_backlog("Claude_Harness-Backlog-Format Version 1.\n\nNo entries.\n")
    assert detector.is_backlog("Format: Claude_Harness-Backlogformat Version 1.\n")
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


def test_mover_inserts_at_the_end_of_the_work_items_section():
    mover = EntryMover()
    with_other = ["## Work items", "", "- `T-1` **x**", "", "## Other", "", "text"]
    empty = ["## Work items", "", "No entries.", ""]

    mover.insert(with_other, ["- `T-2` **y**"])
    mover.insert(empty, ["- `T-2` **y**"])

    assert with_other == ["## Work items", "", "- `T-1` **x**", "", "- `T-2` **y**", "", "## Other", "", "text"]
    assert empty == ["## Work items", "", "- `T-2` **y**", ""]


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


def test_repository_creates_entry_and_refuses_taken_ids(backlog):
    repo = build_markdown_repository(Path("/"))
    new = Item(id="TASK-004", title="Created", project="P", item_type="Task", parent="STORY-001",
               required_for_parent=True, created="2026-09-28", area="Core", priority="Normal",
               goal="A goal.", completion_criteria="Checked.", dependencies=["TASK-001"])

    created = repo.create(backlog, new)

    assert created == new
    assert repo.get(backlog, "TASK-004") == new
    with pytest.raises(DuplicateItemError):
        repo.create(backlog, Item(id="TASK-000", title="Taken in the archive", project="P", area="a", goal="g",
                                  completion_criteria="c"))


# ---------- documents ----------

def _documents():
    from todo_viewer.infrastructure.markdown.documents import MarkdownDocumentStore
    from todo_viewer.infrastructure.markdown.layout import LayoutFactory, SourcePathResolver
    from todo_viewer.infrastructure.markdown.text_file import KeyedLocks

    return MarkdownDocumentStore(LayoutFactory(SourcePathResolver(Path("/"))), TextFileStore(), KeyedLocks())


def test_document_write_creates_folders_and_checks_versions(backlog):
    from todo_viewer.domain.documents import content_version

    store = _documents()
    path = "items/TASK-009/TASK-009_spec.md"

    store.write(backlog, path, "v1\n", expected_version=None)
    with pytest.raises(VersionConflictError):
        store.write(backlog, path, "again\n", expected_version=None)  # exists already
    with pytest.raises(VersionConflictError):
        store.write(backlog, path, "v2\n", expected_version=content_version("other"))
    store.write(backlog, path, "v2\n", expected_version=content_version("v1\n"))

    assert store.read(backlog, path) == "v2\n"
    with pytest.raises(VersionConflictError):
        store.write(backlog, "items/TASK-009/missing.md", "x", expected_version=content_version("x"))


def test_document_append_starts_new_files_with_a_header(backlog):
    store = _documents()
    path = "items/TASK-009/TASK-009_notes.md"

    first = store.append(backlog, path, "## entry 1\n", header="# TASK-009 — t\n")
    second = store.append(backlog, path, "## entry 2\n", header="# ignored\n")

    assert first == "# TASK-009 — t\n\n## entry 1\n"
    assert second == "# TASK-009 — t\n\n## entry 1\n\n## entry 2\n"
    assert store.append(backlog, "items/TASK-002/notes.md", "## e\n", header="#") == \
        "# Notes for TASK-002\n\nSome *markdown* notes.\n\n## e\n"


def test_document_paths_stay_inside_the_backlog(backlog):
    from todo_viewer.domain.errors import DocumentForbiddenError

    for path in ("../x.md", "items/../../x.md", "items/a/b.json"):
        with pytest.raises(DocumentForbiddenError):
            _documents().write(backlog, path, "x", expected_version=None)


def test_repository_delete_cuts_active_and_archived_entries(backlog):
    repo = build_markdown_repository(Path("/"))
    active, archived = repo.get(backlog, "TASK-002"), repo.get(backlog, "STORY-000")
    stale = repo.get(backlog, "TASK-003")
    repo.apply(backlog, stale, ChangeSet(set_fields=(("priority", "Urgent"),)))

    repo.delete(backlog, [active, archived])
    with pytest.raises(VersionConflictError):
        repo.delete(backlog, [stale])

    ids = {i.id for i in repo.load(backlog).items}
    assert "TASK-002" not in ids and "STORY-000" not in ids and "TASK-003" in ids


def test_document_store_deletes_the_item_folder(backlog):
    store = _documents()
    folder = Path(backlog.path) / "items" / "TASK-002"
    assert folder.is_dir()

    store.delete_item_folder(backlog, "TASK-002")
    store.delete_item_folder(backlog, "TASK-404")  # no folder: nothing to do

    assert not folder.exists()
    assert (Path(backlog.path) / "TODO.md").is_file()
    from todo_viewer.domain.errors import DocumentForbiddenError
    for bad in ("..", "../b", "", "a/b"):
        with pytest.raises(DocumentForbiddenError):
            store.delete_item_folder(backlog, bad)


def test_repository_apply_all_marks_and_moves_several_entries(backlog):
    repo = build_markdown_repository(Path("/"))
    task, done = repo.get(backlog, "TASK-003"), repo.get(backlog, "TASK-000")
    mark = ChangeSet(set_fields=(("deleted", "2026-09-28"),))

    changed = repo.apply_all(backlog, [(task, dataclasses.replace(mark, move_to=Location.ARCHIVE)), (done, mark)])

    assert [(i.id, i.deleted, i.location) for i in changed] == [
        ("TASK-003", "2026-09-28", Location.ARCHIVE), ("TASK-000", "2026-09-28", Location.ARCHIVE)]
    assert "- `TASK-003` **" not in (Path(backlog.path) / "TODO.md").read_text(encoding="utf-8")
    assert "  - Deleted: 2026-09-28." in (Path(backlog.path) / "archive.md").read_text(encoding="utf-8")
    with pytest.raises(VersionConflictError):
        repo.apply_all(backlog, [(task, mark)])  # stale: already changed

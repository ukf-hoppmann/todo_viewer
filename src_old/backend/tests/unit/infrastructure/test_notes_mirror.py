"""The notes folder of the mirror: atomic writes, conflicts, line endings, and a fingerprint that only reads."""
from __future__ import annotations

from pathlib import Path

import pytest

from todo_viewer.domain.documents import content_version
from todo_viewer.domain.errors import MirrorConflictError
from todo_viewer.domain.source import Source
from todo_viewer.infrastructure.notes_files import FilesNotesMirror


@pytest.fixture
def mirror(tmp_path: Path) -> FilesNotesMirror:
    return FilesNotesMirror(tmp_path)


@pytest.fixture
def source(tmp_path: Path) -> Source:
    return Source(project="P", path=str(tmp_path / "md"), backend="markdown")


def files(source: Source) -> dict[str, str]:
    folder = Path(source.path) / "notes"
    return {p.name: p.read_bytes().decode("utf-8") for p in sorted(folder.glob("*")) if p.is_file()}


def test_a_missing_folder_reads_as_empty(mirror: FilesNotesMirror, source: Source):
    assert mirror.read(source) == {}
    assert mirror.fingerprint(source) == mirror.fingerprint(source)
    assert not Path(source.path).exists()  # reading creates nothing


def test_writing_creates_the_folder_and_reading_gives_back_the_same_files(mirror: FilesNotesMirror, source: Source):
    for name in ("NOTE-001.md", "NOTE-001_notes.md", "NOTE-001_spec_ui.md", "new-idea.md", "new-idea_spec.md",
                 "topics.md", "counters.md"):
        mirror.write(source, name, f"# {name}\nÜmlaut\n", None)

    assert mirror.read(source) == files(source)
    assert set(mirror.read(source)) == {"NOTE-001.md", "NOTE-001_notes.md", "NOTE-001_spec_ui.md", "new-idea.md",
                                        "new-idea_spec.md", "topics.md", "counters.md"}
    assert mirror.read(source)["NOTE-001.md"] == "# NOTE-001.md\nÜmlaut\n"


def test_other_files_in_the_folder_are_not_notes_files(mirror: FilesNotesMirror, source: Source):
    mirror.write(source, "topics.md", "- TOPIC-001 | A\n", None)
    folder = Path(source.path) / "notes"
    (folder / "README.md").write_text("hello", encoding="utf-8")
    (folder / "sub").mkdir()
    (folder / "sub" / "NOTE-009.md").write_text("x", encoding="utf-8")
    (folder / ".NOTE-001.md.tmp").write_text("x", encoding="utf-8")

    assert set(mirror.read(source)) == {"topics.md"}


@pytest.mark.parametrize("name", ["../NOTE-001.md", "sub/NOTE-001.md", "README.md", "NOTE-001.txt", "note-1.md", ""])
def test_only_notes_file_names_can_be_written(mirror: FilesNotesMirror, source: Source, name: str):
    with pytest.raises(ValueError):
        mirror.write(source, name, "x", None)


def test_a_file_that_changed_since_it_was_read_is_not_overwritten(mirror: FilesNotesMirror, source: Source):
    mirror.write(source, "NOTE-001.md", "one\n", None)
    seen = content_version(mirror.read(source)["NOTE-001.md"])
    (Path(source.path) / "notes" / "NOTE-001.md").write_text("edited outside\n", encoding="utf-8")

    with pytest.raises(MirrorConflictError) as error:
        mirror.write(source, "NOTE-001.md", "two\n", seen)

    assert error.value.code == "mirror_conflict"
    assert files(source)["NOTE-001.md"] == "edited outside\n"


def test_a_new_file_must_not_exist_and_a_deleted_one_must_be_unchanged(mirror: FilesNotesMirror, source: Source):
    mirror.write(source, "NOTE-001.md", "one\n", None)

    with pytest.raises(MirrorConflictError):
        mirror.write(source, "NOTE-001.md", "two\n", None)
    with pytest.raises(MirrorConflictError):
        mirror.delete(source, "NOTE-001.md", content_version("other\n"))
    mirror.delete(source, "NOTE-001.md", content_version("one\n"))

    assert files(source) == {}


def test_a_file_that_vanished_is_a_conflict_too(mirror: FilesNotesMirror, source: Source):
    with pytest.raises(MirrorConflictError):
        mirror.write(source, "NOTE-001.md", "x\n", content_version("was here\n"))


def test_the_line_ending_of_the_file_it_replaces_stays(mirror: FilesNotesMirror, source: Source):
    mirror.write(source, "NOTE-001.md", "a\r\nb\r\n", None)
    seen = content_version(mirror.read(source)["NOTE-001.md"])

    mirror.write(source, "NOTE-001.md", "a\nc\n", seen)

    assert files(source)["NOTE-001.md"] == "a\r\nc\r\n"


def test_an_error_while_renaming_leaves_the_old_file_and_no_temporary_file(mirror: FilesNotesMirror, source: Source,
                                                                          monkeypatch: pytest.MonkeyPatch):
    mirror.write(source, "NOTE-001.md", "old\n", None)
    seen = content_version("old\n")

    def broken(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("os.replace", broken)
    with pytest.raises(OSError):
        mirror.write(source, "NOTE-001.md", "new\n", seen)
    monkeypatch.undo()

    assert sorted(p.name for p in (Path(source.path) / "notes").iterdir()) == ["NOTE-001.md"]
    assert files(source)["NOTE-001.md"] == "old\n"


def test_the_fingerprint_follows_every_change_and_changes_nothing(mirror: FilesNotesMirror, source: Source):
    empty = mirror.fingerprint(source)
    mirror.write(source, "NOTE-001.md", "one\n", None)
    one = mirror.fingerprint(source)
    mirror.write(source, "NOTE-001.md", "two\n", content_version("one\n"))
    two = mirror.fingerprint(source)
    mirror.write(source, "NOTE-002.md", "two\n", None)
    three = mirror.fingerprint(source)

    assert len({empty, one, two, three}) == 4 and mirror.fingerprint(source) == three
    assert files(source) == {"NOTE-001.md": "two\n", "NOTE-002.md": "two\n"}


def test_files_with_merge_markers_are_named(mirror: FilesNotesMirror, source: Source):
    mirror.write(source, "NOTE-001.md", "a\n<<<<<<< HEAD\nb\n=======\nc\n>>>>>>> main\n", None)
    mirror.write(source, "NOTE-002.md", "fine\n", None)

    assert mirror.files_with_markers(source) == ["notes/NOTE-001.md"]

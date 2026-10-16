"""Contract-Suite des `FileStore`-Ports: gilt für `LocalFileStore` (echte Ordner) und `InMemoryFileStore` (Fake)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from file_store_harness import Harness, LocalHarness, MemoryHarness
from viewer.core.domain.errors import InvalidInput
from viewer.core.domain.files import DeleteFile, MirrorBlocked, MirrorConflict, RenameFile, WriteFile

MD = ("**/*.md",)


@pytest.fixture(params=["local", "memory"])
def h(request: pytest.FixtureRequest, tmp_path: Path) -> Harness:
    return LocalHarness(tmp_path) if request.param == "local" else MemoryHarness(tmp_path)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- Lesen -----------------------------------------------------------------------------------------------------


def test_reads_matching_files_with_content_and_sha256_version(h: Harness) -> None:
    h.put("TODO.md", "# Titel\n")
    h.put("items/STORY-1/STORY-1_spec.md", "Spec\n")
    h.put("notes/a.md", "Note\n")
    h.put("other.txt", "ignoriert")
    h.put("items/readme.txt", "ignoriert")
    files = h.store.read(h.folder, ["TODO.md", "items/**/*.md"]).files
    assert sorted(files) == ["TODO.md", "items/STORY-1/STORY-1_spec.md"]
    assert files["TODO.md"].text == "# Titel\n"
    assert files["TODO.md"].version == sha(b"# Titel\n")


def test_double_star_matches_files_at_the_top_level_too(h: Harness) -> None:
    h.put("a.md", "x")
    h.put("deep/er/b.md", "y")
    assert sorted(h.store.read(h.folder, MD).files) == ["a.md", "deep/er/b.md"]


def test_version_changes_with_every_content_change(h: Harness) -> None:
    h.put("a.md", "eins")
    first = h.store.read(h.folder, MD).files["a.md"].version
    h.put("a.md", "zwei")
    assert h.store.read(h.folder, MD).files["a.md"].version != first


def test_crlf_files_are_read_with_lf_and_report_their_line_ending(h: Harness) -> None:
    h.put("crlf.md", b"a\r\nb\r\n")
    h.put("lf.md", b"a\nb\n")
    files = h.store.read(h.folder, MD).files
    assert (files["crlf.md"].text, files["crlf.md"].newline) == ("a\nb\n", "\r\n")
    assert (files["lf.md"].text, files["lf.md"].newline) == ("a\nb\n", "\n")
    assert files["crlf.md"].version == sha(b"a\r\nb\r\n")


def test_temporary_files_of_atomic_writes_are_not_part_of_the_mirror(h: Harness) -> None:
    h.put("a.md", "x")
    h.put(".a.md.k3j2h.tmp", "halb")
    assert sorted(h.store.read(h.folder, ["**/*", "*"]).files) == ["a.md"]


# --- Schreiben -------------------------------------------------------------------------------------------------


def test_write_creates_replaces_and_deletes_and_returns_new_versions(h: Harness) -> None:
    h.put("old.md", "alt")
    h.put("gone.md", "weg")
    result = h.store.write(
        h.folder,
        [WriteFile("new/dir/n.md", "neu\n"), WriteFile("old.md", "geändert"), DeleteFile("gone.md")],
        {"new/dir/n.md": None, "old.md": sha(b"alt"), "gone.md": sha(b"weg")},
    )
    assert h.get("new/dir/n.md") == b"neu\n" and h.get("old.md") == "geändert".encode() and h.get("gone.md") is None
    assert result == {"new/dir/n.md": sha(b"neu\n"), "old.md": sha("geändert".encode()), "gone.md": None}


def test_rename_moves_the_file(h: Harness) -> None:
    h.put("a.md", "inhalt")
    result = h.store.write(h.folder, [RenameFile("a.md", "sub/b.md")], {"a.md": sha(b"inhalt"), "sub/b.md": None})
    assert h.get("a.md") is None and h.get("sub/b.md") == b"inhalt"
    assert result == {"a.md": None, "sub/b.md": sha(b"inhalt")}


def test_write_keeps_crlf_of_existing_files_and_uses_lf_for_new_ones(h: Harness) -> None:
    h.put("crlf.md", b"a\r\n")
    h.put("lf.md", b"a\n")
    h.store.write(
        h.folder,
        [WriteFile("crlf.md", "x\ny\n"), WriteFile("lf.md", "x\ny\n"), WriteFile("new.md", "x\ny\n")],
        {"crlf.md": sha(b"a\r\n"), "lf.md": sha(b"a\n"), "new.md": None},
    )
    assert h.get("crlf.md") == b"x\r\ny\r\n"
    assert h.get("lf.md") == b"x\ny\n"
    assert h.get("new.md") == b"x\ny\n"


def test_write_leaves_no_temporary_files_behind(h: Harness) -> None:
    h.put("a.md", "x")
    h.store.write(h.folder, [WriteFile("a.md", "y"), WriteFile("b.md", "z")], {"a.md": sha(b"x"), "b.md": None})
    assert h.names() == {"a.md", "b.md"}


def test_changed_file_raises_mirror_conflict_and_nothing_is_written(h: Harness) -> None:
    h.put("a.md", "alt")
    h.put("b.md", "b")
    read = h.store.read(h.folder, MD).versions()
    h.put("b.md", "extern geändert")
    with pytest.raises(MirrorConflict) as err:
        h.store.write(h.folder, [WriteFile("a.md", "neu"), WriteFile("b.md", "neu")], read)
    assert err.value.code == "mirror_conflict" and err.value.details == {"paths": ["b.md"]}
    assert h.get("a.md") == b"alt" and h.get("b.md") == "extern geändert".encode()


def test_file_created_meanwhile_is_a_conflict_for_expected_none(h: Harness) -> None:
    h.put("neu.md", "von jemand anderem")
    with pytest.raises(MirrorConflict):
        h.store.write(h.folder, [WriteFile("neu.md", "meins")], {"neu.md": None})
    assert h.get("neu.md") == b"von jemand anderem"


def test_file_deleted_meanwhile_is_a_conflict(h: Harness) -> None:
    with pytest.raises(MirrorConflict):
        h.store.write(h.folder, [WriteFile("a.md", "x")], {"a.md": sha(b"war mal da")})


def test_rename_onto_an_existing_file_is_a_conflict(h: Harness) -> None:
    h.put("a.md", "a")
    h.put("b.md", "b")
    with pytest.raises(MirrorConflict):
        h.store.write(h.folder, [RenameFile("a.md", "b.md")], {"a.md": sha(b"a"), "b.md": None})
    assert h.get("a.md") == b"a" and h.get("b.md") == b"b"


def test_a_guarded_but_unchanged_file_may_conflict_too(h: Harness) -> None:
    h.put("a.md", "a")
    h.put("guard.md", "g")
    h.put("guard.md", "g2")
    with pytest.raises(MirrorConflict):
        h.store.write(h.folder, [WriteFile("a.md", "x")], {"a.md": sha(b"a"), "guard.md": sha(b"g")})


def test_every_touched_path_needs_an_expected_version(h: Harness) -> None:
    with pytest.raises(ValueError):
        h.store.write(h.folder, [WriteFile("a.md", "x")], {})


@pytest.mark.parametrize("path", ["../out.md", "/abs.md", "a/../../b.md", "", ".git/config", "a\\b.md", "a//b.md"])
def test_paths_outside_the_folder_are_rejected(h: Harness, path: str) -> None:
    with pytest.raises(InvalidInput):
        h.store.write(h.folder, [WriteFile(path, "x")], {path: None})


def test_failure_in_the_middle_restores_everything_done_so_far(h: Harness) -> None:
    h.put("a.md", "alt")
    h.put("gone.md", "bleibt")
    h.put("blocker", "ich bin eine Datei")
    with pytest.raises(OSError):
        h.store.write(
            h.folder,
            [
                WriteFile("a.md", "neu"),
                DeleteFile("gone.md"),
                WriteFile("new/dir/x.md", "x"),
                WriteFile("blocker/x.md", "y"),
            ],
            {"a.md": sha(b"alt"), "gone.md": sha(b"bleibt"), "new/dir/x.md": None, "blocker/x.md": None},
        )
    assert h.get("a.md") == b"alt" and h.get("gone.md") == b"bleibt" and h.get("new/dir/x.md") is None
    assert h.names() == {"a.md", "gone.md", "blocker"}


# --- Zustand des Ordners ---------------------------------------------------------------------------------------


def test_missing_folder_is_reported_by_inspect_and_blocks_read_and_write(h: Harness) -> None:
    h.remove_folder()
    assert h.store.inspect(h.folder).status == "missing"
    with pytest.raises(MirrorBlocked) as err:
        h.store.read(h.folder, MD)
    assert err.value.code == "mirror_blocked" and err.value.details["state"] == "missing"
    with pytest.raises(MirrorBlocked):
        h.store.write(h.folder, [WriteFile("a.md", "x")], {"a.md": None})


def test_write_can_create_the_folder_when_asked(h: Harness) -> None:
    h.remove_folder()
    h.store.write(h.folder, [WriteFile("a.md", "x")], {"a.md": None}, create_folder=True)
    assert h.get("a.md") == b"x"


def test_merge_markers_block_reading_and_are_listed(h: Harness) -> None:
    h.put("ok.md", "gut")
    h.put("items/x/bad.md", "a\n<<<<<<< HEAD\nmeins\n=======\ndeins\n>>>>>>> branch\nb\n")
    state = h.store.inspect(h.folder)
    assert (state.status, state.files) == ("merge_markers", ("items/x/bad.md",))
    with pytest.raises(MirrorBlocked) as err:
        h.store.read(h.folder, MD)
    assert err.value.details == {"state": "merge_markers", "files": ["items/x/bad.md"]}


def test_a_single_marker_line_is_not_a_conflict(h: Harness) -> None:
    h.put("a.md", "Text\n<<<<<<< nur ein Zitat\n")
    assert h.store.inspect(h.folder).ok


def test_writing_over_a_file_with_markers_is_blocked(h: Harness) -> None:
    content = "<<<<<<< HEAD\na\n=======\nb\n>>>>>>> x\n"
    h.put("a.md", content)
    with pytest.raises(MirrorBlocked):
        h.store.write(h.folder, [WriteFile("a.md", "neu")], {"a.md": sha(content.encode())})
    assert h.get("a.md") == content.encode()


def test_git_lock_blocks_everything_and_is_reported(h: Harness) -> None:
    h.put("a.md", "x")
    h.add_git_lock()
    state = h.store.inspect(h.folder)
    assert (state.status, state.files) == ("git_operation", (".git/index.lock",))
    with pytest.raises(MirrorBlocked) as err:
        h.store.read(h.folder, MD)
    assert err.value.details["state"] == "git_operation"
    with pytest.raises(MirrorBlocked):
        h.store.write(h.folder, [WriteFile("b.md", "x")], {"b.md": None})
    assert h.get("b.md") is None


def test_unreadable_file_blocks_reading(h: Harness) -> None:
    h.put("a.md", "gut")
    h.put("kaputt.md", b"\xff\xfe\x00 kein utf-8 \x80")
    state = h.store.inspect(h.folder)
    assert (state.status, state.files) == ("unreadable", ("kaputt.md",))
    with pytest.raises(MirrorBlocked):
        h.store.read(h.folder, MD)


def test_healthy_folder_is_ok(h: Harness) -> None:
    h.put("a.md", "x")
    assert h.store.inspect(h.folder).ok


# --- Ordner-Browser --------------------------------------------------------------------------------------------


def test_list_folders_lists_subfolders_without_hidden_ones_sorted_and_marks_mirrors(h: Harness) -> None:
    h.put("beta/TODO.md", "x")
    h.put("Alpha/a.md", "x")
    h.put(".versteckt/a.md", "x")
    h.put("datei.md", "x")

    listing = h.store.list_folders(h.folder)

    assert [(f.name, f.has_mirror) for f in listing.folders] == [("Alpha", False), ("beta", True)]
    assert listing.path == str(h.folder) and listing.parent == str(h.folder.parent)
    assert listing.error is None and not listing.has_mirror


def test_list_folders_knows_when_the_folder_itself_is_a_mirror(h: Harness) -> None:
    h.put("TODO.md", "x")

    assert h.store.list_folders(h.folder).has_mirror


def test_list_folders_falls_back_to_the_nearest_existing_parent(h: Harness) -> None:
    h.put("a/b.md", "x")

    listing = h.store.list_folders(h.folder / "gibt-es-nicht" / "auch-nicht")

    assert listing.path == str(h.folder)
    assert [f.name for f in listing.folders] == ["a"]

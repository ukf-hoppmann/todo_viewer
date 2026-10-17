"""Nur für `LocalFileStore`: Eigenschaften, die nur ein echtes Dateisystem hat."""

from __future__ import annotations

import os
import stat
import threading
from pathlib import Path

from file_store_harness import sha256_of
from viewer.core.domain.files import WriteFile
from viewer.core.infrastructure.files import LocalFileStore


def test_file_mode_of_an_existing_file_is_kept(tmp_path: Path) -> None:
    target = tmp_path / "a.md"
    target.write_text("x")
    target.chmod(0o600)
    LocalFileStore().write(tmp_path, [WriteFile("a.md", "y")], {"a.md": sha256_of(b"x")})
    assert stat.S_IMODE(os.stat(target).st_mode) == 0o600


def test_new_files_are_created_world_readable(tmp_path: Path) -> None:
    LocalFileStore().write(tmp_path, [WriteFile("n.md", "y")], {"n.md": None})
    assert stat.S_IMODE(os.stat(tmp_path / "n.md").st_mode) == 0o644


def test_git_lock_of_a_worktree_gitfile_is_found(tmp_path: Path) -> None:
    gitdir = tmp_path / "real-git"
    gitdir.mkdir()
    (gitdir / "index.lock").write_text("")
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").write_text(f"gitdir: {gitdir}\n")
    state = LocalFileStore().inspect(project)
    assert state.status == "git_operation"


def test_git_lock_in_a_parent_repository_blocks_a_subfolder(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD.lock").write_text("")
    sub = tmp_path / "docs" / "todo"
    sub.mkdir(parents=True)
    assert LocalFileStore().inspect(sub).files == (".git/HEAD.lock",)


def test_concurrent_writers_in_one_process_never_both_win(tmp_path: Path) -> None:
    store = LocalFileStore()
    (tmp_path / "a.md").write_text("start")
    outcomes: list[str] = []

    def writer(name: str) -> None:
        try:
            store.write(tmp_path, [WriteFile("a.md", name)], {"a.md": sha256_of(b"start")})
            outcomes.append("ok")
        except Exception as exc:
            outcomes.append(type(exc).__name__)

    threads = [threading.Thread(target=writer, args=(f"w{i}",)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(outcomes) == ["MirrorConflict"] * 7 + ["ok"]


def test_a_folder_that_a_delete_or_rename_empties_is_removed_but_never_the_mirror_folder(tmp_path: Path) -> None:
    from viewer.core.domain.files import DeleteFile, RenameFile
    from viewer.core.infrastructure.files import LocalFileStore

    store = LocalFileStore()
    (tmp_path / "items" / "A-1").mkdir(parents=True)
    (tmp_path / "items" / "A-1" / "x.md").write_text("x", encoding="utf-8")
    (tmp_path / "items" / "B-1").mkdir()
    (tmp_path / "items" / "B-1" / "y.md").write_text("y", encoding="utf-8")
    versions = store.read(tmp_path, ["items/**/*.md"]).versions()

    store.write(
        tmp_path,
        [RenameFile("items/A-1/x.md", "items/A-2/x.md")],
        {"items/A-1/x.md": versions["items/A-1/x.md"], "items/A-2/x.md": None},
    )
    store.write(tmp_path, [DeleteFile("items/B-1/y.md")], {"items/B-1/y.md": versions["items/B-1/y.md"]})

    assert not (tmp_path / "items" / "A-1").exists() and not (tmp_path / "items" / "B-1").exists()
    assert (tmp_path / "items" / "A-2" / "x.md").is_file()
    store.write(
        tmp_path,
        [DeleteFile("items/A-2/x.md")],
        {"items/A-2/x.md": store.read(tmp_path, ["items/**/*.md"]).versions()["items/A-2/x.md"]},
    )
    assert tmp_path.is_dir() and not (tmp_path / "items").exists()

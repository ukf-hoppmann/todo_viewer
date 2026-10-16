from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

# Git config key below branch.<worktree-branch> that stores the branch to merge back into.
BASE_KEY = "harnessBase"
# Mirroring ignored files into a new worktree: never taken over, linked instead of copied
# (large, and virtual environments break when copied), and left out (rebuilt on demand).
NEVER_MIRRORED = (PurePosixPath(".git"), PurePosixPath(".claude/worktrees"))
LINKED_NAMES = frozenset({"node_modules", ".venv", "venv"})
SKIPPED_NAMES = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build"})
# Claude Code settings files that can set worktree.baseRef, highest precedence first.
PROJECT_SETTINGS = (".claude/settings.local.json", ".claude/settings.json")
USER_SETTINGS = ".claude/settings.json"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def is_git_repo(root: Path) -> bool:
    try:
        return _git(root, "rev-parse", "--is-inside-work-tree").stdout.strip() == "true"
    except OSError:
        return False


def base_ref_setting(root: Path, home: Path) -> str | None:
    """Effective worktree.baseRef from the settings files; unreadable files count as unset."""
    for path in [root / p for p in PROJECT_SETTINGS] + [home / USER_SETTINGS]:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        section = data.get("worktree") if isinstance(data, dict) else None
        value = section.get("baseRef") if isinstance(section, dict) else None
        if isinstance(value, str):
            return value
    return None


class WorktreeError(Exception):
    """A precondition of the change workflow is not met."""


class CheckFailed(WorktreeError):
    """check found a blocker; the findings are still printed."""

    def __init__(self, lines: list[str]):
        super().__init__("merge blocked")
        self.lines = lines


def _git_out(cwd: Path, *args: str) -> str:
    result = _git(cwd, *args)
    if result.returncode != 0:
        raise WorktreeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _worktrees(cwd: Path) -> list[tuple[Path, str | None]]:
    """Path and checked-out branch (None if detached) of every worktree, the main checkout first."""
    trees: list[tuple[Path, str | None]] = []
    for line in _git_out(cwd, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            trees.append((Path(line[len("worktree "):]), None))
        elif line.startswith("branch ") and trees:
            trees[-1] = (trees[-1][0], line[len("branch "):].removeprefix("refs/heads/"))
    return trees


def _main_checkout(cwd: Path) -> tuple[Path, str | None]:
    """Path and checked-out branch (None if detached) of the repository's main worktree."""
    trees = _worktrees(cwd)
    if not trees:
        raise WorktreeError("no main checkout found")
    return trees[0]


def in_main_checkout(path: Path) -> Path:
    """The same place as the directory path, but in the repository's main worktree; WorktreeError outside Git."""
    top = Path(_git_out(path, "rev-parse", "--show-toplevel")).resolve()
    return _main_checkout(path)[0].resolve() / path.resolve().relative_to(top)


def _current_worktree_branch(cwd: Path) -> str:
    git_dir = Path(_git_out(cwd, "rev-parse", "--absolute-git-dir")).resolve()
    common_dir = (cwd / _git_out(cwd, "rev-parse", "--git-common-dir")).resolve()
    if git_dir == common_dir:
        raise WorktreeError("not inside a linked worktree; run this in the worktree of the change")
    branch = _git_out(cwd, "branch", "--show-current")
    if not branch:
        raise WorktreeError("the worktree has no branch checked out")
    return branch


class _Mirror:
    def __init__(self, source: Path, target: Path):
        self.source, self.target = source, target
        self.copied = 0
        self.linked: list[str] = []
        self.skipped: list[str] = []

    def add(self, rel: PurePosixPath) -> None:
        if any(rel == p or rel.is_relative_to(p) for p in NEVER_MIRRORED):
            return
        src, dst = self.source / rel, self.target / rel
        if rel.name in SKIPPED_NAMES:
            self.skipped.append(str(rel))
        elif rel.name in LINKED_NAMES and src.is_dir():
            if not os.path.lexists(dst):
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.symlink_to(src)
                self.linked.append(str(rel))
        elif src.is_dir() and not src.is_symlink():
            for child in sorted(src.iterdir()):
                self.add(rel / child.name)
        elif not os.path.lexists(dst):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst, follow_symlinks=False)
            self.copied += 1


def _mirror_ignored(main: Path, worktree: Path) -> list[str]:
    listing = _git_out(main, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory")
    mirror = _Mirror(main, worktree)
    for entry in filter(None, listing.split("\0")):
        mirror.add(PurePosixPath(entry.rstrip("/")))
    return [
        f"copied: {mirror.copied} files",
        f"linked: {', '.join(mirror.linked) or 'none'}",
        f"skipped: {', '.join(mirror.skipped) or 'none'}",
    ]


def start(cwd: Path) -> list[str]:
    branch = _current_worktree_branch(cwd)
    main, base = _main_checkout(cwd)
    if base is None:
        raise WorktreeError("the main checkout is in detached HEAD state; ask which branch to merge into")
    _git_out(cwd, "config", f"branch.{branch}.{BASE_KEY}", base)
    root = Path(_git_out(cwd, "rev-parse", "--show-toplevel"))
    return [f"base: {base}", *_mirror_ignored(main, root)]


def check(cwd: Path) -> list[str]:
    """Findings before merging back; raises when the merge must not happen."""
    branch = _current_worktree_branch(cwd)
    base = _git(cwd, "config", f"branch.{branch}.{BASE_KEY}").stdout.strip()
    if not base:
        raise WorktreeError(f"no base branch recorded for {branch}; was 'worktree.py start' run?")
    main, main_branch = _main_checkout(cwd)
    clean = not _git_out(cwd, "status", "--porcelain")
    moved = _git(cwd, "merge-base", "--is-ancestor", base, "HEAD").returncode != 0
    on_base = main_branch == base
    # The owner switched the main checkout away: the worktree itself checks out the base and merges.
    base_free = all(branch != base for _, branch in _worktrees(cwd))
    merge_in = "main" if on_base else "worktree" if base_free else "none"
    lines = [
        f"base: {base}",
        f"main: {main}",
        f"clean: {'yes' if clean else 'no'}",
        f"base_moved: {'yes' if moved else 'no'}",
        f"main_on_base: {'yes' if on_base else 'no'}",
        f"merge_in: {merge_in}",
    ]
    if not clean or merge_in == "none":
        raise CheckFailed(lines)
    return lines


COMMANDS = {"start": start, "check": check}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in COMMANDS:
        print(f"usage: worktree.py {'|'.join(COMMANDS)}", file=sys.stderr)
        return 2
    try:
        lines = COMMANDS[argv[0]](Path.cwd())
    except CheckFailed as exc:
        print("\n".join(exc.lines))
        return 1
    except (WorktreeError, OSError) as exc:
        print(f"error: {exc}")
        return 1
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

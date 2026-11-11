"""Bring the current branch of a cloud session up to date with origin, or say how far it is off.

Cloud sessions can start on a stale, cached clone. At session start (cloud only, see session_start.py) this
fetches the current branch from origin and fast-forwards a clean working tree. It never overwrites anything:
a dirty tree, commits on both sides, no shared history, or a failed fetch give one line with the gap and the
fitting command. It fetches only the current branch and never deepens a shallow clone, so the start stays fast.
Network and the fast-forward are an approved exception to architecture rules 2 and 5 (STORY-052).
"""

from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path

REMOTE = "origin"
# The session start hook has 30 s; the fetch gets half of it, the local git calls a few seconds each.
FETCH_TIMEOUT = 15.0
LOCAL_TIMEOUT = 5.0
_NO_REMOTE_REF = "couldn't find remote ref"


@dataclass
class _Run:
    code: int
    out: str
    err: str


class _TimedOut(Exception):
    pass


def _git(root: Path, *args: str, timeout: float = LOCAL_TIMEOUT) -> _Run:
    """Run git in its own process group, so that a timeout also stops helpers such as ssh."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}
    proc = subprocess.Popen(
        ["git", *args], cwd=root, env=env, text=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        raise _TimedOut from None
    return _Run(proc.returncode, out.strip(), err.strip())


def sync_branch(root: Path, fetch_timeout: float = FETCH_TIMEOUT) -> str | None:
    """Fetch and fast-forward the current branch; a line for the session start, or None when there is nothing to say."""
    try:
        return _sync(root, fetch_timeout)
    except (_TimedOut, OSError):
        # Local git calls hanging or git missing: the session start must not fail because of this check.
        return None


def _sync(root: Path, fetch_timeout: float) -> str | None:
    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch.code != 0 or not branch.out:
        return None  # detached HEAD or not a repository
    b = branch.out
    if _git(root, "remote", "get-url", REMOTE).code != 0:
        return None
    tracking = f"refs/remotes/{REMOTE}/{b}"
    try:
        fetched = _git(
            root, "fetch", "--quiet", "--no-tags", "--no-recurse-submodules", REMOTE, f"+refs/heads/{b}:{tracking}",
            timeout=fetch_timeout,
        )
    except _TimedOut:
        return f"Git: could not fetch {REMOTE}/{b} (timed out after {fetch_timeout:g} s); the checkout may be stale."
    if fetched.code != 0:
        if _NO_REMOTE_REF in fetched.err:
            return None  # a branch that was never pushed
        reason = (fetched.err.splitlines() or ["git fetch failed"])[0]
        return f"Git: could not fetch {REMOTE}/{b} ({reason}); the checkout may be stale."
    local, remote = _rev(root, "HEAD"), _rev(root, tracking)
    if not local or not remote or local == remote:
        return None
    if _is_ancestor(root, local, remote):
        return _behind(root, b, local, remote)
    if _is_ancestor(root, remote, local):
        return None  # only local commits: the normal state before a push
    if _git(root, "merge-base", local, remote).code == 0:
        ahead, behind = _count(root, remote, local), _count(root, local, remote)
        return (
            f"Git: {b} and {REMOTE}/{b} have diverged ({ahead} local, {behind} remote commit(s)); nothing changed. "
            f"Tell the user before working; rebase with git rebase {REMOTE}/{b}, "
            f"or git reset --hard {REMOTE}/{b} only if the user asks."
        )
    return (
        f"Git: {b} shares no history with {REMOTE}/{b} in this shallow clone "
        f"(local {_describe(root, local)}; origin {_describe(root, remote)}). Nothing changed. "
        "Likely a stale cached clone or a force-push. Tell the user before working; "
        f"reset only on request: git reset --hard {REMOTE}/{b}."
    )


def _behind(root: Path, b: str, local: str, remote: str) -> str:
    count = _count(root, local, remote)
    if _git(root, "status", "--porcelain", "--untracked-files=no").out:
        return (
            f"Git: {b} is {count} commit(s) behind {REMOTE}/{b}, but the working tree has changes; nothing changed. "
            f"Commit or stash them, then run git merge --ff-only {REMOTE}/{b}."
        )
    merged = _git(root, "merge", "--ff-only", "--quiet", remote)
    if merged.code != 0:
        reason = (merged.err.splitlines() or ["git merge failed"])[0]
        return (
            f"Git: {b} is {count} commit(s) behind {REMOTE}/{b}; fast-forward failed ({reason}); nothing changed. "
            f"Run git merge --ff-only {REMOTE}/{b}."
        )
    return f"Git: fast-forwarded {b} from {local[:7]} to {remote[:7]} ({count} new commit(s) from {REMOTE})."


def _rev(root: Path, ref: str) -> str | None:
    result = _git(root, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    return result.out if result.code == 0 and result.out else None


def _is_ancestor(root: Path, older: str, newer: str) -> bool:
    return _git(root, "merge-base", "--is-ancestor", older, newer).code == 0


def _count(root: Path, base: str, tip: str) -> str:
    result = _git(root, "rev-list", "--count", f"{base}..{tip}")
    return result.out if result.code == 0 and result.out else "?"


def _describe(root: Path, commit: str) -> str:
    result = _git(root, "log", "-1", "--format=%h, %cs", commit)
    return result.out if result.code == 0 and result.out else commit[:7]

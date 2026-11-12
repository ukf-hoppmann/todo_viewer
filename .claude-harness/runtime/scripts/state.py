from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from harness_config import ROOT_PROJECT

try:
    import fcntl
except ImportError:  # no file locks on this platform
    fcntl = None  # type: ignore[assignment]


def state_dir() -> Path:
    data_dir = os.environ.get("CLAUDE_PLUGIN_DATA")
    if data_dir:
        return Path(data_dir)
    return Path(tempfile.gettempdir()) / "claude-harness"


def _safe(session_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", session_id)


def dirty_marker(session_id: str) -> Path:
    """JSON list of the projects whose backlog changed; an empty file means the root project."""
    return state_dir() / f"backlog-dirty-{_safe(session_id)}"


def read_names(path: Path) -> set[str]:
    try:
        text = path.read_text()
    except OSError:
        return set()
    if not text.strip():
        return {ROOT_PROJECT}
    try:
        return {str(name) for name in json.loads(text)}
    except (ValueError, TypeError):
        return {ROOT_PROJECT}


def write_names(path: Path, names: set[str]) -> None:
    """Store names; an empty set removes the file."""
    if not names:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(names)))


def memos_folder_marker(session_id: str) -> Path:
    """JSON list of the projects whose notes folder (below the backlog folder) changed in the session."""
    return state_dir() / f"backlog-memos-folder-{_safe(session_id)}"


def notes_changed_file(session_id: str) -> Path:
    """JSON list of "<project>\t<path relative to the project>" for notes files changed in the session."""
    return state_dir() / f"backlog-notes-{_safe(session_id)}.json"


def read_changed_notes(session_id: str) -> set[tuple[str, str]]:
    """(project, path relative to the project) of the notes files changed in the session."""
    try:
        entries = json.loads(notes_changed_file(session_id).read_text())
    except (OSError, ValueError):
        return set()
    return {tuple(str(entry).split("\t", 1)) for entry in entries if "\t" in str(entry)}


def write_changed_notes(session_id: str, notes: set[tuple[str, str]]) -> None:
    """Store the changed notes files; an empty set removes the file."""
    path = notes_changed_file(session_id)
    if not notes:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(f"{project}\t{relative}" for project, relative in notes)))


NotesMark = dict[str, "str | int | None"]


def notes_marks_file(session_id: str) -> Path:
    """JSON object "<project>\\t<ID>" -> {"state", "turns"} for the backlog items of the session (API backend).

    `state` is the state of the item's notes head as the helper last reported it (`current`, `stale`, `missing`, or
    null when only known as active); `turns` counts the prompts since the item became active or got a notes entry
    (null while the item is not active).
    """
    return state_dir() / f"notes-marks-{_safe(session_id)}.json"


def read_notes_marks(session_id: str) -> dict[tuple[str, str], NotesMark]:
    try:
        entries = json.loads(notes_marks_file(session_id).read_text())
    except (OSError, ValueError):
        return {}
    marks: dict[tuple[str, str], NotesMark] = {}
    if not isinstance(entries, dict):
        return marks
    for key, mark in entries.items():
        project, separator, identifier = str(key).partition("\t")
        if separator and isinstance(mark, dict) and "state" in mark and "turns" in mark:
            marks[(project, identifier)] = {"state": mark["state"], "turns": mark["turns"]}
    return marks


def write_notes_marks(session_id: str, marks: dict[tuple[str, str], NotesMark]) -> None:
    """Store the marks; an empty dict removes the file. The file is replaced in one step, never half written."""
    path = notes_marks_file(session_id)
    if not marks:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps({f"{project}\t{identifier}": mark for (project, identifier), mark in sorted(marks.items())})
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


@contextmanager
def edit_notes_marks(session_id: str) -> Iterator[dict[tuple[str, str], NotesMark]]:
    """Read the marks, let the caller change them, store them: one writer at a time.

    The hooks of tool calls that run in parallel (and the prompt hook) would otherwise overwrite each other's marks.
    An error in the block stores nothing. Without file locks (not on Linux or macOS) the update is unprotected.
    """
    path = notes_marks_file(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_name(path.name + ".lock"), "a") as lock:
        if fcntl is not None:
            fcntl.flock(lock, fcntl.LOCK_EX)
        marks = read_notes_marks(session_id)
        yield marks
        write_notes_marks(session_id, marks)


def delivered_notices_file(session_id: str) -> Path:
    return state_dir() / f"backlog-notices-{_safe(session_id)}.json"


def daily_reminded_file(session_id: str) -> Path:
    return state_dir() / f"daily-reminded-{_safe(session_id)}.json"


def techdocs_marker(session_id: str, kind: str, project: str = ROOT_PROJECT) -> Path:
    """kind: 'project' (project files changed), 'docs' (docs changed), 'reminded'; per project."""
    if project == ROOT_PROJECT:
        return state_dir() / f"techdocs-{kind}-{_safe(session_id)}"
    return state_dir() / f"techdocs-{kind}-{_safe(project)}--{_safe(session_id)}"


def architecture_read_file(session_id: str) -> Path:
    return state_dir() / f"architecture-read-{_safe(session_id)}.json"


def semver_reported_file(session_id: str) -> Path:
    return state_dir() / f"semver-reported-{_safe(session_id)}.json"


def doclinks_changed_file(session_id: str) -> Path:
    """JSON list of "<project>\t<path relative to the project>" for documents changed in the session (doclinks)."""
    return state_dir() / f"doclinks-changed-{_safe(session_id)}.json"


def read_changed_docs(session_id: str) -> set[tuple[str, str]]:
    try:
        entries = json.loads(doclinks_changed_file(session_id).read_text())
    except (OSError, ValueError):
        return set()
    return {tuple(str(entry).split("\t", 1)) for entry in entries if "\t" in str(entry)}


def write_changed_docs(session_id: str, docs: set[tuple[str, str]]) -> None:
    """Store the changed documents; an empty set removes the file."""
    path = doclinks_changed_file(session_id)
    if not docs:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(f"{project}\t{relative}" for project, relative in docs)))


def public_api_file(session_id: str, kind: str, project: str = ROOT_PROJECT) -> Path:
    """kind: 'changed' (JSON list of changed public API files) or 'reminded'; per project."""
    if project == ROOT_PROJECT:
        return state_dir() / f"public-api-{kind}-{_safe(session_id)}"
    return state_dir() / f"public-api-{kind}-{_safe(project)}--{_safe(session_id)}"

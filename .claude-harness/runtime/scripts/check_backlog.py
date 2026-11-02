from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import notes_head
from backlog import BacklogItem, validate_backlog
from harness_config import ROOT_PROJECT, ConfigError, project_root
from notes_format import NOTES_DIR, check_notes_folder
from notes_hint import child_in_progress_hint
from projects import load_projects
from state import (
    delivered_notices_file,
    dirty_marker,
    notes_folder_marker,
    read_changed_notes,
    read_names,
    write_changed_notes,
    write_names,
)

GIT_TIMEOUT_SECONDS = 5


def _load_delivered(session_id: str) -> set[str]:
    try:
        return set(json.loads(delivered_notices_file(session_id).read_text()))
    except (OSError, ValueError):
        return set()


def _save_delivered(session_id: str, notices: set[str]) -> None:
    path = delivered_notices_file(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(notices)))


def _notice_key(project: str, notice: str) -> str:
    return notice if project == ROOT_PROJECT else f"{project}: {notice}"


def _committed(root: Path, relative: str) -> str | None:
    """The file as of the last commit, or None (no Git, not tracked, or Git failed)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"HEAD:./{relative}"],
            capture_output=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.decode("utf-8", "replace") if result.returncode == 0 else None


def _child_hint(items: list[BacklogItem], identifier: str) -> str | None:
    by_id = {i.identifier: i for i in items}
    item = by_id.get(identifier)
    if item is None:
        return None
    active = [i.identifier for i in items if i.parent == identifier and i.status == "In progress" and not i.deleted]
    hint = child_in_progress_hint(identifier, item.item_type, active)
    return hint.removeprefix("hint: ") if hint else None


def _check_notes(project, relatives: set[str], items: list[BacklogItem]) -> tuple[list[str], list[str], set[str]]:
    """Errors, notices, and the notes files to check again at the next stop."""
    errors: list[str] = []
    notices: list[str] = []
    again: set[str] = set()
    folder = project.path / project.config.todo_path
    for relative in sorted(relatives):
        try:
            text = (project.root / relative).read_text(encoding="utf-8")
        except OSError:
            continue
        name = Path(relative).name
        state = notes_head.state_of(text)
        if state != notes_head.CURRENT:
            again.add(relative)
            errors.append(
                f"{name}: the head (## State) is {state}. Look at it, update it if needed, then confirm it: "
                f"backlog.py {folder} --confirm-state {Path(relative).parent.name} "
                "(skills/todo/format.md, section Notes)"
            )
        if notes_head.decided_count(text) > notes_head.LONG_STATE:
            notices.append(
                f"{name}: more than {notes_head.LONG_STATE} points under - Decided: in the head; "
                "write the spec or split the item?"
            )
        child_hint = _child_hint(items, Path(relative).parent.name)
        if child_hint:
            notices.append(f"{name}: {child_hint}")
        committed = _committed(project.root, relative)
        if committed is not None and notes_head.history_rewritten(committed, text):
            notices.append(
                f"{name}: an earlier log entry was changed or removed since the last commit; "
                "the log is append-only (a deliberate correction is fine)"
            )
    return errors, notices, again


def _check_notes_folder(project) -> tuple[list[str], list[str]]:
    """Errors and notices for the notes kept as files (`<backlog folder>/notes/`), format version 2."""
    findings = check_notes_folder(project.root / project.config.todo_path / NOTES_DIR)
    errors = [str(f) for f in findings if f.error]
    if errors:
        errors.append(
            f"{NOTES_DIR}/: fix the lines above (format: skills/todo/notes-files.md; "
            f"check again with notes_files.py {project.path / project.config.todo_path} --check)"
        )
    return errors, [str(f) for f in findings if not f.error]


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    session_id = hook_input.get("session_id")
    if not session_id:
        return 0
    marker = dirty_marker(session_id)
    dirty = read_names(marker)
    if not dirty:
        return 0
    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    delivered = _load_delivered(session_id)
    changed_notes = read_changed_notes(session_id)
    folder_marker = notes_folder_marker(session_id)
    folder_changed = read_names(folder_marker)
    folder_again: set[str] = set()
    still_dirty: set[str] = set()
    notes_again: set[tuple[str, str]] = set()
    blocks: list[str] = []
    for name in sorted(dirty):
        project = projects.get(name) if projects else None
        if project is None or not project.config.enabled("todo") or project.config.todo_backend != "files":
            continue
        report = validate_backlog(project.root / project.config.todo_path)
        notes_errors, notes_notices, again = _check_notes(project, {r for p, r in changed_notes if p == name}, report.items)
        notes_again |= {(name, relative) for relative in again}
        folder_errors, folder_notices = _check_notes_folder(project) if name in folder_changed else ([], [])
        if folder_errors:
            folder_again.add(name)
        errors = report.errors + notes_errors + folder_errors
        new_notices = [
            n for n in report.notices + notes_notices + folder_notices if _notice_key(name, n) not in delivered
        ]
        # With errors the project stays marked so its backlog is checked again at the next stop.
        if errors:
            still_dirty.add(name)
        if not errors and not new_notices:
            continue
        lines = [f"Claude_Harness backlog check after your edits in {project.path / project.config.todo_path}:"]
        if errors:
            lines.append("Fix these errors:")
            lines += [f"- {e}" for e in errors]
        if new_notices:
            lines.append("Handle these notices (each is shown once per session):")
            lines += [f"- {n}" for n in new_notices]
            delivered |= {_notice_key(name, n) for n in new_notices}
        blocks.append("\n".join(lines))
    write_names(marker, still_dirty)
    # Like the dirty mark, the notes folder of a project that is not checked here (module off, other backend) is dropped.
    write_names(folder_marker, folder_again)
    # Like the dirty mark, notes of projects that are not checked here (module off, other backend) are dropped.
    write_changed_notes(session_id, notes_again)
    if not blocks or hook_input.get("stop_hook_active"):
        return 0
    _save_delivered(session_id, delivered)
    print("\n\n".join(blocks), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import json
import sys
from pathlib import PurePath

from harness_config import ConfigError, project_root
from projects import load_projects
from memos_format import MEMOS_DIR
from state import (
    dirty_marker,
    memos_folder_marker,
    read_changed_notes,
    edit_notes_marks,
    read_names,
    write_changed_notes,
    write_names,
)


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    file_path = (hook_input.get("tool_input") or {}).get("file_path")
    session_id = hook_input.get("session_id")
    if not file_path or not session_id:
        return 0

    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    project = projects.for_file(file_path) if projects else None
    # With the API backend the server checks every change; only direct file edits are checked here.
    if project is None or not project.config.enabled("todo") or project.config.todo_backend != "files":
        return 0
    relative = project.relative(file_path)
    if relative.is_relative_to(project.config.todo_path):
        # The marker lists the projects whose backlog changed in this session.
        marker = dirty_marker(session_id)
        write_names(marker, read_names(marker) | {project.name})
        if is_memos_folder_file(relative.relative_to(project.config.todo_path)):
            folder_marker = memos_folder_marker(session_id)
            write_names(folder_marker, read_names(folder_marker) | {project.name})
        if is_notes_file(relative.relative_to(project.config.todo_path)):
            notes = read_changed_notes(session_id) | {(project.name, relative.as_posix())}
            write_changed_notes(session_id, notes)
            _restart_count(session_id, project.name, relative.parent.name)
    return 0


def _restart_count(session_id: str, project: str, identifier: str) -> None:
    """A notes entry restarts the reminder's count for an active item (remind_notes.py)."""
    try:
        with edit_notes_marks(session_id) as marks:
            mark = marks.get((project, identifier))
            if mark is not None and mark["turns"] is not None:
                mark["turns"] = 0
    except OSError:
        pass


def is_memos_folder_file(path: PurePath) -> bool:
    """A file of the memos folder (`memos/…`) below the backlog folder: memos kept as files, not item notes."""
    return len(path.parts) >= 2 and path.parts[0] == MEMOS_DIR


def is_notes_file(path: PurePath) -> bool:
    """`items/<ID>/<ID>_notes.md` below the backlog folder."""
    parts = path.parts
    return len(parts) == 3 and parts[0] == "items" and parts[2] == f"{parts[1]}_notes.md"


if __name__ == "__main__":
    sys.exit(main())

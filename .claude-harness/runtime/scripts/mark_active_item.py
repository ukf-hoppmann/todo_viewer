"""PostToolUse hook on Read: reading an item's spec makes the item active (files backend).

The API backend learns the same from the helper (mark_notes_state.py). An active item is counted by the reminder
(remind_notes.py) until its notes get an entry.
"""

from __future__ import annotations

import json
import sys
from pathlib import PurePath

from harness_config import ConfigError, project_root
from projects import load_projects
from state import edit_notes_marks


def is_spec_file(path: PurePath) -> bool:
    """`items/<ID>/<ID>_spec.md` below the backlog folder."""
    parts = path.parts
    return len(parts) == 3 and parts[0] == "items" and parts[2] == f"{parts[1]}_spec.md"


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(hook_input, dict):
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
    if project is None or not project.config.enabled("todo") or project.config.todo_backend != "files":
        return 0
    relative = project.relative(file_path)
    if not relative.is_relative_to(project.config.todo_path):
        return 0
    inner = relative.relative_to(project.config.todo_path)
    if not is_spec_file(inner):
        return 0
    try:
        with edit_notes_marks(session_id) as marks:
            mark = marks.setdefault((project.name, inner.parts[1]), {"state": None, "turns": None})
            if mark["turns"] is None:
                mark["turns"] = 0
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

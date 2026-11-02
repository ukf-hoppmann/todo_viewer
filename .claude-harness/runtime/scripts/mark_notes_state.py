"""PostToolUse hook on Bash: remembers what backlog_api.py reported about the notes of backlog items (API backend).

The helper prints `[harness] notes-state <ID> <current|stale|missing>` after it wrote an item's notes and
`[harness] active <ID>` when the session starts working on an item. The hook reads those lines from the Bash answer and
stores the marks for the Stop hook (check_notes_state.py) and the reminder (remind_notes.py). It uses no network and runs
only after successful calls: a failed helper call changed nothing and leaves no mark.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from harness_config import ROOT_PROJECT, ConfigError, project_root
from projects import load_projects
from state import edit_notes_marks

HELPER = "backlog_api.py"
_LINE = re.compile(r"^\[harness\] (?P<kind>notes-state|active) (?P<id>[A-Za-z0-9_-]+-[0-9]+)(?: (?P<state>current|stale|missing))?$")
_PROJECT = re.compile(r"backlog_api\.py[\"']?\s+--project\s+(?P<name>[^\s\"']+)")
_SOURCE = re.compile(r"backlog_api\.py[\"']?\s+--source\b")


def response_text(response: Any) -> str:
    """stdout and stderr of the Bash answer (a plain string in older versions)."""
    if isinstance(response, dict):
        return "\n".join(str(response.get(key) or "") for key in ("stdout", "stderr"))
    return response if isinstance(response, str) else ""


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(hook_input, dict) or hook_input.get("tool_name") != "Bash":
        return 0
    command = (hook_input.get("tool_input") or {}).get("command")
    session_id = hook_input.get("session_id")
    if not isinstance(command, str) or HELPER not in command or not session_id or _SOURCE.search(command):
        return 0
    reported = [m for m in map(_LINE.match, response_text(hook_input.get("tool_response")).splitlines()) if m]
    if not reported:
        return 0
    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    match = _PROJECT.search(command)
    name = match["name"] if match else ROOT_PROJECT
    project = projects.get(name) if projects else None
    if project is None or not project.config.enabled("todo") or project.config.todo_backend != "api":
        return 0
    try:
        # Hooks of parallel Bash calls run at the same time: the update is locked.
        with edit_notes_marks(session_id) as marks:
            for line in reported:
                mark = marks.setdefault((name, line["id"]), {"state": None, "turns": None})
                if line["kind"] == "active":
                    if mark["turns"] is None:
                        mark["turns"] = 0
                else:
                    mark["state"] = line["state"]
                    if mark["turns"] is not None:
                        mark["turns"] = 0
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

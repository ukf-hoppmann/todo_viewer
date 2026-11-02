"""Stop hook: the notes head must be current before the turn ends (API backend).

mark_notes_state.py stores what the helper reported after each write on an item's notes. A head that is `stale` or
`missing` blocks the end of the turn until it is updated (put-state) or confirmed (confirm-state), which sets it to
`current`. The files backend is checked by check_backlog.py. No network: only the stored marks are read.
"""

from __future__ import annotations

import json
import sys

from harness_config import ROOT_PROJECT, ConfigError, project_root
from projects import load_projects
from state import read_notes_marks

BLOCKING = ("stale", "missing")


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(hook_input, dict) or hook_input.get("stop_hook_active"):
        return 0
    session_id = hook_input.get("session_id")
    if not session_id:
        return 0
    open_heads = sorted((p, i, m["state"]) for (p, i), m in read_notes_marks(session_id).items() if m["state"] in BLOCKING)
    if not open_heads:
        return 0
    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    lines = []
    for name, identifier, head in open_heads:
        project = projects.get(name) if projects else None
        if project is None or not project.config.enabled("todo") or project.config.todo_backend != "api":
            continue
        option = "" if name == ROOT_PROJECT else f"--project {name} "
        lines.append(f"- {identifier}: the head (## State) is {head} (backlog_api.py {option}state {identifier})")
    if not lines:
        return 0
    print(
        "Claude_Harness notes check: the head of these notes is not current. Look at it, update it if needed "
        "(put-state), then confirm it (confirm-state); the check passes when the helper reports it current "
        "(skills/todo/format.md, section Notes):\n" + "\n".join(lines),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

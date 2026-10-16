from __future__ import annotations

import json
import sys

from harness_config import ConfigError, project_root
from projects import load_projects
from state import dirty_marker, read_names, write_names


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
    if project.relative(file_path).is_relative_to(project.config.todo_path):
        # The marker lists the projects whose backlog changed in this session.
        marker = dirty_marker(session_id)
        write_names(marker, read_names(marker) | {project.name})
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import json
import sys

from harness_config import ConfigError, project_root
from projects import load_projects
from state import techdocs_marker
from techdocs import classify


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
    if project is None or not project.config.enabled("techdocs"):
        return 0

    kind = classify(project, file_path)
    if kind:
        marker = techdocs_marker(session_id, kind, project.name)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
    return 0


if __name__ == "__main__":
    sys.exit(main())

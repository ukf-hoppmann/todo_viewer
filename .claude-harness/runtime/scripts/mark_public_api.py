from __future__ import annotations

import json
import sys

from architecture import match_path
from harness_config import ConfigError, project_root
from projects import load_projects
from state import public_api_file


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
    if project is None or not project.config.part_enabled("architecture") or not project.config.public_api:
        return 0
    rel = project.relative(file_path)
    if rel is None or not any(match_path(pattern, rel) for pattern in project.config.public_api):
        return 0

    marker = public_api_file(session_id, "changed", project.name)
    try:
        changed = set(json.loads(marker.read_text()))
    except (OSError, ValueError, TypeError):
        changed = set()
    changed.add(rel.as_posix())
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps(sorted(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import json
import sys
from pathlib import Path

from architecture import mark_read, rules_path, scopes_dir
from harness_config import ConfigError, project_root
from projects import load_projects


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_input = hook_input.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    session_id = hook_input.get("session_id")
    if not file_path or not session_id:
        return 0

    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    project = projects.for_file(file_path) if projects else None
    if project is None or not project.config.part_enabled("architecture"):
        return 0

    config = project.config
    rel = project.relative(file_path)
    if rel != rules_path(config) and rel.parent != scopes_dir(config):
        return 0
    if not _complete_read(project.root / rel, tool_input):
        return 0
    # Stored relative to the session root, so equally named files of two projects stay apart.
    mark_read(session_id, project.path / rel)
    return 0


def _complete_read(path: Path, tool_input: dict) -> bool:
    """Only a read from the first line that covers the whole file counts."""
    offset = tool_input.get("offset")
    if offset not in (None, 0, 1):
        return False
    limit = tool_input.get("limit")
    if limit is None:
        return True
    try:
        lines = len(path.read_text(encoding="utf-8").splitlines())
    except OSError:
        return False
    return limit >= lines


if __name__ == "__main__":
    sys.exit(main())

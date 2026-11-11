from __future__ import annotations

import json
import sys

from doclinks import is_doc_file
from harness_config import ConfigError, project_root
from projects import load_projects
from state import read_changed_docs, write_changed_docs


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
    rel = project.relative(file_path) if project else None
    if project is None or rel is None or not is_doc_file(project.config, rel):
        return 0
    write_changed_docs(session_id, read_changed_docs(session_id) | {(project.name, str(rel))})
    return 0


if __name__ == "__main__":
    sys.exit(main())

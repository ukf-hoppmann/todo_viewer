from __future__ import annotations

import json
import sys
from pathlib import PurePosixPath

from doclinks import check_project, is_doc_file
from harness_config import ConfigError, project_root
from projects import load_projects
from state import read_changed_docs, write_changed_docs

MAX_REPORTED = 20


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    session_id = hook_input.get("session_id")
    if not session_id or hook_input.get("stop_hook_active"):
        return 0
    changed = read_changed_docs(session_id)
    if not changed:
        return 0
    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    if projects is None:
        return 0
    problems: list[str] = []
    for name in sorted({name for name, _ in changed}):
        project = projects.get(name)
        if project is None:
            continue
        files = [PurePosixPath(rel) for n, rel in sorted(changed) if n == name and is_doc_file(project.config, PurePosixPath(rel))]
        problems += check_project(project.root, project.config, files, project.path)
    if not problems:
        write_changed_docs(session_id, set())
        return 0
    shown = problems[:MAX_REPORTED]
    if len(problems) > MAX_REPORTED:
        shown.append(f"… {len(problems) - MAX_REPORTED} more")
    print(
        f"Claude_Harness doclinks: {len(problems)} dead link(s) in documents changed in this session. "
        "Fix the links (or the targets); relative Markdown links and #anchors must resolve:\n" + "\n".join(shown),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import json
import sys

from harness_config import README, ConfigError, project_root
from projects import Project, load_projects
from state import techdocs_marker


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    session_id = hook_input.get("session_id")
    if not session_id or hook_input.get("stop_hook_active"):
        return 0
    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    if projects is None:
        return 0
    due = [p for p in projects.projects if p.config.enabled("techdocs") and _needs_reminder(session_id, p)]
    if not due:
        return 0
    for project in due:
        reminded = techdocs_marker(session_id, "reminded", project.name)
        reminded.parent.mkdir(parents=True, exist_ok=True)
        reminded.touch()
    if not projects.has_subprojects():
        print(
            "Claude_Harness techdocs: project files changed in this session, but no technical "
            f"documentation (README.md, {due[0].config.techdocs_path}/). Load skill claude-harness:techdocs "
            "and check whether a document must be updated; if not, state briefly why. "
            "(Shown once per session.)",
            file=sys.stderr,
        )
        return 2
    listed = "; ".join(
        f"{p.name} ({p.path / README}, {p.path / p.config.techdocs_path}/)" for p in due
    )
    print(
        "Claude_Harness techdocs: project files changed in this session, but no technical "
        f"documentation of the same project: {listed}. Load skill claude-harness:techdocs and "
        "check whether a document must be updated; if not, state briefly why. "
        "(Shown once per project and session.)",
        file=sys.stderr,
    )
    return 2


def _needs_reminder(session_id: str, project: Project) -> bool:
    def marked(kind: str) -> bool:
        return techdocs_marker(session_id, kind, project.name).exists()

    return marked("project") and not marked("docs") and not marked("reminded")


if __name__ == "__main__":
    sys.exit(main())

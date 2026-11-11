from __future__ import annotations

import json
import sys

from harness_config import ConfigError, project_root
from projects import Project, load_projects
from state import public_api_file


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
    due = [(p, changed) for p in projects.projects if (changed := _due_files(session_id, p))]
    if not due:
        return 0
    for project, _ in due:
        reminded = public_api_file(session_id, "reminded", project.name)
        reminded.parent.mkdir(parents=True, exist_ok=True)
        reminded.touch()
    if not projects.has_subprojects():
        project, changed = due[0]
        print(
            f"Claude_Harness architecture: public API files changed {_summary(changed)}. "
            "Check that the architecture responsibilities, the catalog of reusable building blocks, "
            f"the interface docs in {project.config.development_path}/ and their links still match. "
            "Load skills claude-harness:architecture and claude-harness:interfaces. (Shown once per session.)",
            file=sys.stderr,
        )
        return 2
    listed = "; ".join(
        f"{p.name} ({p.path / p.config.development_path}/, {_summary(changed)})" for p, changed in due
    )
    print(
        "Claude_Harness architecture: public API files changed: "
        f"{listed}. Check that the architecture responsibilities, the catalog of reusable building blocks, "
        "the interface docs and their links of each project still match. "
        "Load skills claude-harness:architecture and claude-harness:interfaces. (Shown once per project and session.)",
        file=sys.stderr,
    )
    return 2


def _due_files(session_id: str, project: Project) -> list[str]:
    """Changed public API files of the project, or [] when it needs no reminder."""
    config = project.config
    if not config.part_enabled("architecture") or not config.public_api:
        return []
    if public_api_file(session_id, "reminded", project.name).exists():
        return []
    try:
        changed = json.loads(public_api_file(session_id, "changed", project.name).read_text())
    except (OSError, ValueError):
        return []
    return [str(entry) for entry in changed] if isinstance(changed, list) else []


def _summary(changed: list[str]) -> str:
    count = len(changed)
    return f"({count} file{'s' if count != 1 else ''}, e.g. {changed[0]})"


if __name__ == "__main__":
    sys.exit(main())

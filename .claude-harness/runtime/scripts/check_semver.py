from __future__ import annotations

import json
import sys
from pathlib import Path

from harness_config import ConfigError, project_root
from projects import load_projects
from semver import is_git_repo, status
from state import semver_reported_file

SEMVER_SCRIPT = Path(__file__).resolve().parent / "semver.py"


def _load_reported(session_id: str) -> set[str]:
    try:
        return set(json.loads(semver_reported_file(session_id).read_text()))
    except (OSError, ValueError):
        return set()


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
    with_semver = [p for p in projects.projects if p.config.enabled("semver")] if projects else []
    if not with_semver or not is_git_repo(projects.session_root):
        return 0
    reported = _load_reported(session_id)
    due = []
    for project in with_semver:
        findings = status(projects, project).findings
        # Report a state once per session so that a deliberately kept state does not block every turn.
        key = "\x1f".join([project.name, *findings])
        if findings and key not in reported:
            due.append((project, findings))
            reported.add(key)
    if not due:
        return 0
    path = semver_reported_file(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(reported)))
    if projects.has_subprojects():
        details = " ".join(f"{p.name} ({p.path}): {'; '.join(f)}." for p, f in due)
        start = "; ".join(f'python3 "{SEMVER_SCRIPT}" status --project {p.name}' for p, _ in due)
    else:
        details = "; ".join(due[0][1]) + "."
        start = f'python3 "{SEMVER_SCRIPT}" status'
    print(
        f"Claude_Harness semver: {details} Load skill claude-harness:semver and follow it "
        f"(start with: {start}).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

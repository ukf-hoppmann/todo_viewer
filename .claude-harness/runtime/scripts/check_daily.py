from __future__ import annotations

import json
import sys
from pathlib import Path

from daily import head, pending_commits, unavailable_reason
from harness_config import ROOT_PROJECT, ConfigError, project_root
from projects import load_projects
from state import daily_reminded_file

DAILY_SCRIPT = Path(__file__).resolve().parent / "daily.py"


def _load_reminded(session_id: str) -> set[str]:
    try:
        return set(json.loads(daily_reminded_file(session_id).read_text()))
    except (OSError, ValueError):
        return set()


def _save_reminded(session_id: str, heads: set[str]) -> None:
    path = daily_reminded_file(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(heads)))


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    session_id = hook_input.get("session_id")
    if not session_id or hook_input.get("stop_hook_active"):
        return 0
    root = project_root(hook_input)
    try:
        projects = load_projects(root)
    except ConfigError:
        return 0
    with_daily = [p for p in projects.projects if p.config.enabled("daily")] if projects else []
    if not with_daily or unavailable_reason(root):
        return 0
    current = head(root)
    if current is None:
        return 0
    reminded = _load_reminded(session_id)
    due = []
    for project in with_daily:
        # Remind once per HEAD and project; the root key keeps its old form.
        key = current if project.name == ROOT_PROJECT else f"{project.name}:{current}"
        commits = pending_commits(projects, project)
        if commits and key not in reminded:
            due.append((project, len(commits)))
            reminded.add(key)
    if not due:
        return 0
    _save_reminded(session_id, reminded)
    if not projects.has_subprojects():
        print(
            f"Claude_Harness daily: {due[0][1]} commit(s) on this branch are not yet "
            "recorded in the daily report. Load skill claude-harness:daily and follow it "
            f'(start with: python3 "{DAILY_SCRIPT}" pending).',
            file=sys.stderr,
        )
        return 2
    listed = "; ".join(f"{p.name} ({count}, {p.path / p.config.daily_path}/)" for p, count in due)
    commands = "; ".join(f'python3 "{DAILY_SCRIPT}" pending --project {p.name}' for p, _ in due)
    print(
        "Claude_Harness daily: commits on this branch are not yet recorded in the daily "
        f"report of: {listed}. Load skill claude-harness:daily and follow it for each project "
        f"(start with: {commands}).",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())

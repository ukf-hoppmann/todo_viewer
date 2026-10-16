from __future__ import annotations

import json
import sys

from backlog import validate_backlog
from harness_config import ROOT_PROJECT, ConfigError, project_root
from projects import load_projects
from state import delivered_notices_file, dirty_marker, read_names, write_names


def _load_delivered(session_id: str) -> set[str]:
    try:
        return set(json.loads(delivered_notices_file(session_id).read_text()))
    except (OSError, ValueError):
        return set()


def _save_delivered(session_id: str, notices: set[str]) -> None:
    path = delivered_notices_file(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(notices)))


def _notice_key(project: str, notice: str) -> str:
    return notice if project == ROOT_PROJECT else f"{project}: {notice}"


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    session_id = hook_input.get("session_id")
    if not session_id:
        return 0
    marker = dirty_marker(session_id)
    dirty = read_names(marker)
    if not dirty:
        return 0
    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    delivered = _load_delivered(session_id)
    still_dirty: set[str] = set()
    blocks: list[str] = []
    for name in sorted(dirty):
        project = projects.get(name) if projects else None
        if project is None or not project.config.enabled("todo") or project.config.todo_backend != "files":
            continue
        report = validate_backlog(project.root / project.config.todo_path)
        new_notices = [n for n in report.notices if _notice_key(name, n) not in delivered]
        # With errors the project stays marked so its backlog is checked again at the next stop.
        if not report.ok:
            still_dirty.add(name)
        if not report.errors and not new_notices:
            continue
        lines = [f"Claude_Harness backlog check after your edits in {project.path / project.config.todo_path}:"]
        if report.errors:
            lines.append("Fix these errors:")
            lines += [f"- {e}" for e in report.errors]
        if new_notices:
            lines.append("Handle these notices (each is shown once per session):")
            lines += [f"- {n}" for n in new_notices]
            delivered |= {_notice_key(name, n) for n in new_notices}
        blocks.append("\n".join(lines))
    write_names(marker, still_dirty)
    if not blocks or hook_input.get("stop_hook_active"):
        return 0
    _save_delivered(session_id, delivered)
    print("\n\n".join(blocks), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import json
import re
import sys

from architecture import (
    Usage, inherited_files, inherited_uses, load_uses, read_files, required_files, rules_path, use_pattern,
)
from harness_config import ROOT_PROJECT, ConfigError, project_root
from projects import Project, ProjectSet, load_projects

# Backlog specs are the input for implementation plans (<ID>_spec.md, <ID>_spec_<topic>.md).
_SPEC_NAME = re.compile(r"[A-Z]+-\d+_spec(_[^/]+)?\.md")


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_input = hook_input.get("tool_input") or {}
    session_id = hook_input.get("session_id")
    if not session_id:
        return 0
    try:
        projects = load_projects(project_root(hook_input))
    except ConfigError:
        return 0
    if projects is None:
        return 0
    done = read_files(session_id)
    if hook_input.get("tool_name") == "ExitPlanMode":
        missing = [
            rules for rules in _plan_rules(projects, tool_input.get("plan") or "") if rules not in done
        ]
        if missing:
            _deny(
                f"before presenting a plan, read the binding architecture rules in full with the "
                f"Read tool: {', '.join(missing)}, plus every scope listed there whose paths the plan "
                "touches. Check the plan against the rules, then present it again."
            )
        return 0
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not file_path:
        return 0
    project = projects.for_file(file_path)
    if project is None or not _has_rules(project):
        return 0
    config = project.config
    rel = project.relative(file_path)
    shown_rel = project.path / rel
    rules = (project.path / rules_path(config)).as_posix()
    if rel.is_relative_to(config.todo_path) and _SPEC_NAME.fullmatch(rel.name):
        if rules not in done:
            _deny(
                f"a spec is the input for an implementation plan. Before writing {shown_rel}, read the "
                f"binding architecture rules in full with the Read tool: {rules}, plus every scope "
                "listed there whose paths the spec touches. Align the spec with the rules, then retry."
            )
        return 0
    if config.is_harness_file(rel):
        return 0
    required = [(project.path / p).as_posix() for p in required_files(project.root, config, rel)]
    required += [p.as_posix() for p in inherited_files(projects, project)[0]]
    missing = [
        p if (projects.session_root / p).is_file() else f"{p} (missing)"
        for p in dict.fromkeys(required) if p not in done
    ]
    if missing:
        _deny(
            f"before changing {shown_rel}, read the binding architecture rules in full with the Read "
            f"tool: {', '.join(missing)}. Load skill claude-harness:architecture if not loaded "
            "yet, check your plan against the rules, then retry."
        )
        return 0
    _check_uses(projects, project, rel, _new_text(hook_input.get("tool_name"), tool_input), done)
    return 0


def _new_text(tool: str | None, tool_input: dict) -> str:
    """The text a write tool puts into the file."""
    if tool == "Write":
        texts = [tool_input.get("content")]
    elif tool == "Edit":
        texts = [tool_input.get("new_string")]
    elif tool == "MultiEdit":
        texts = [e.get("new_string") for e in tool_input.get("edits") or [] if isinstance(e, dict)]
    elif tool == "NotebookEdit":
        texts = [tool_input.get("new_source")]
    else:
        texts = []
    return "\n".join(t for t in texts if isinstance(t, str))


def _check_uses(projects: ProjectSet, project: Project, rel, text: str, done: set[str]) -> None:
    """Deny when the new text uses an identifier whose documentation was not read in full."""
    if not text:
        return
    usages = [
        Usage(u.uses, tuple((project.path / r).as_posix() for r in u.read))
        for u in load_uses(project.root, project.config, rel)[0]
    ]
    usages += inherited_uses(projects, project)[0]
    needs: dict[str, list[str]] = {}  # doc -> identifiers hit
    for usage in usages:
        for identifier in usage.uses:
            if not use_pattern(identifier).search(text):
                continue
            for doc in usage.read:
                if doc not in done and identifier not in needs.setdefault(doc, []):
                    needs[doc].append(identifier)
    needs = {doc: ids for doc, ids in needs.items() if ids}
    if not needs:
        return
    docs = [d if (projects.session_root / d).is_file() else f"{d} (missing)" for d in needs]
    ids = list(dict.fromkeys(i for found in needs.values() for i in found))
    shown_rel = project.path / rel
    detail = "" if len(needs) == 1 else " (" + "; ".join(f"{', '.join(f)}: {d}" for d, f in zip(docs, needs.values())) + ")"
    _deny(
        f"before using {', '.join(ids)} in {shown_rel}, read {', '.join(docs)} in full with the Read "
        f"tool, then retry.{detail}"
    )


def _has_rules(project: Project) -> bool:
    config = project.config
    return config.part_enabled("architecture") and (project.root / rules_path(config)).is_file()


def _plan_rules(projects: ProjectSet, plan: str) -> list[str]:
    """Rules files (relative to the session root) of the projects a plan mentions; root if none."""
    mentioned = [
        p for p in projects.projects
        if p.name != ROOT_PROJECT and re.search(rf"(?<![\w./-]){re.escape(p.path.as_posix())}(?![\w-])", plan)
    ]
    if not mentioned:
        root = projects.get(ROOT_PROJECT)
        mentioned = [root] if root else []
    return [(p.path / rules_path(p.config)).as_posix() for p in mentioned if _has_rules(p)]


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Claude_Harness architecture: {reason}",
        }
    }))


if __name__ == "__main__":
    sys.exit(main())

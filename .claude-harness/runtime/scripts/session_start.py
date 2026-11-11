from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from pathlib import Path, PurePosixPath

from architecture import inherited_files, inherited_uses, load_scopes, load_uses, reset_read, rules_path
from backlog import TODO_FILE, validate_backlog
from cloud_export import copy_problem
from cloud_sync import sync_branch
from doclinks import check_project as dead_doc_links
from techdocs import document_paths
from harness_config import (
    CLOUD_ENV,
    CONFIG_RELATIVE_PATH,
    README,
    ROOT_PROJECT,
    ConfigError,
    ConfigOutdated,
    HarnessConfig,
    project_root,
)
from projects import Project, ProjectSet, load_projects
from semver import status as semver_status
from worktree import base_ref_setting, is_git_repo

MAX_REPORTED = 5

# Skill pointers; with several projects each appears once (architecture rule 7).
TODO_HINT = "rules in skill claude-harness:todo (load it only when working with the backlog)."
NOTES_HINT = (
    "rules in skill claude-harness:todo (load it when asked to remember, remind, or look at "
    "due notes)."
)
DAILY_HINT = "rules in skill claude-harness:daily (load it when reminded or asked about daily reports)."
TECHDOCS_HINT = (
    "rules in skill claude-harness:techdocs (load it when changing documented behavior, interfaces, "
    "configuration, or architecture, or when reminded)."
)
TECHDOCS_LABEL = "Technical docs (for people)"
ARCHITECTURE_HINT = (
    "(binding; read it before planning, designing, or changing code); "
    "rules in skill claude-harness:architecture."
)
INTERFACES_LINE = (
    "Interface docs and catalog of reusable building blocks (for the AI): rules in skill "
    "claude-harness:interfaces (load it when designing, using, or changing an interface or a shared "
    "building block)."
)
DECOMPOSITION_LINE = (
    "Decomposition: rules in skill claude-harness:decomposition (load it when planning or "
    "starting an implementation, or splitting backlog items)."
)
TESTING_HINT = (
    "rules in skill claude-harness:testing (load it when writing, placing, or running tests)."
)
WORKTREE_LINE = (
    "Change workflow: rules in skill claude-harness:worktree (load it when a plan was "
    "approved or a worktree is to be merged back)."
)
SEMVER_HINT = (
    "rules in skill claude-harness:semver (load it when a change is merged, the user asks for a release, "
    "or the semver hook reminds you)."
)
BASE_REF_LINE = (
    'Worktree base: worktree.baseRef is not "head", so worktrees would branch from the '
    "default branch instead of the current one. Work locally; see skill claude-harness:worktree."
)

Show = Callable[[PurePosixPath], str]


def outdated_message(exc: ConfigOutdated) -> str:
    return f"Claude_Harness: {exc}; run /claude-harness:update to bring it up to date."


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except ValueError:
        hook_input = {}
    root = project_root(hook_input)
    session_id = hook_input.get("session_id")
    if session_id and hook_input.get("source") in ("compact", "clear"):
        # Rules read earlier may no longer be in context.
        reset_read(session_id)
    projects = _load(root)
    if isinstance(projects, str):
        print(projects)
        return 0
    root_project = projects.get(ROOT_PROJECT)
    sync_lines = cloud_sync_lines(hook_input, root_project.config, projects.session_root) if root_project else []
    if sync_lines:
        # A fast-forward may have changed the config and the documents the lines below report on.
        projects = _load(root)
        if isinstance(projects, str):
            print("\n".join([*sync_lines, projects]))
            return 0
    if projects.has_subprojects():
        lines = _several_projects(projects)
    else:
        lines = _single_project(root, projects)
    print("\n".join([*sync_lines, *lines]))
    return 0


def _load(root: Path) -> ProjectSet | str:
    """The projects, or the one line that replaces all others when there are none or the config is unusable."""
    try:
        projects = load_projects(root)
    except ConfigOutdated as exc:
        return outdated_message(exc)
    except ConfigError as exc:
        return f"Claude_Harness: invalid configuration — {exc}. Tell the user; do not guess values."
    if projects is None:
        return (
            f"Claude_Harness: plugin active but no {CONFIG_RELATIVE_PATH} in this project. "
            "Set it up with /claude-harness:init if the user wants the harness here."
        )
    return projects


def cloud_sync_lines(
    hook_input: dict, config: HarnessConfig, session_root: Path, sync: Callable[[Path], str | None] = sync_branch
) -> list[str]:
    """At the start of a cloud session with cloud.sync on: bring the branch up to date (cloud_sync.py) first."""
    if os.environ.get(CLOUD_ENV) != "true" or hook_input.get("source") != "startup" or not config.cloud_sync:
        return []
    line = sync(session_root)
    return [line] if line else []


def _single_project(root: Path, projects: ProjectSet) -> list[str]:
    show: Show = str
    project = projects.projects[0]
    config = project.config
    states = ", ".join(
        f"{name}={'on' if enabled else 'off'}" for name, enabled in sorted(config.modules.items())
    ) or "none"
    lines = [
        f"Claude_Harness: modules {states}.",
        f"Document language: {config.language} (write all harness documents in it).",
    ]
    if config.enabled("todo"):
        if config.todo_backend == "api":
            # No reachability check here: hooks do not use the network. TODO.md is optional in this mode.
            lines.append(f"Backlog: {config.todo_path} via ToDo-Viewer API ({config.todo_api_url}){_backend_note(config)}; {TODO_HINT}")
        elif not (root / config.todo_path / TODO_FILE).is_file():
            lines.append(_backlog_missing(config, show))
        else:
            lines.append(f"Backlog: {config.todo_path}/{TODO_FILE}{_backend_note(config)}; {TODO_HINT}")
            lines += _backlog_problems(root, config)
    if config.viewer_notes_enabled():
        # Static line: hooks do not use the network, so due notes are not looked up here.
        lines.append(f"Notes: via ToDo-Viewer API ({config.todo_api_url}); {NOTES_HINT}")
    elif config.notes_enabled():
        # Not looked up either: the folder is created by the first note.
        lines.append(f"Notes: {config.todo_path}/notes/ as files; {NOTES_HINT}")
    if config.enabled("daily"):
        lines.append(f"Daily reports: {config.daily_path}/; {DAILY_HINT}")
    if config.enabled("techdocs"):
        lines.append(f"{TECHDOCS_LABEL}: README.md and {config.techdocs_path}/; {TECHDOCS_HINT}")
        lines += _techdocs_missing(root, config, show)
    if config.part_enabled("architecture"):
        rules = rules_path(config)
        if not (root / rules).is_file():
            lines.append(_architecture_missing(config, show))
        else:
            lines.append(f"Architecture rules: {rules} {ARCHITECTURE_HINT}")
            lines += _scope_problems(root, config)
            lines += _inherited_problems(projects, project)
        lines.append(INTERFACES_LINE)
    lines += _doclink_problems(root, config)
    if config.part_enabled("decomposition"):
        lines.append(DECOMPOSITION_LINE)
    if config.part_enabled("testing"):
        lines.append(f"Tests: {config.tests_path}/; {TESTING_HINT}")
    if config.part_enabled("worktree"):
        lines.append(WORKTREE_LINE)
        if is_git_repo(root) and base_ref_setting(root, Path.home()) != "head":
            lines.append(BASE_REF_LINE)
    if config.enabled("semver"):
        lines.append(f"SemVer: {_semver_summary(projects, project, show)}; {SEMVER_HINT}")
    lines += _cloud_copy_lines(root, config)
    return lines


def _several_projects(projects: ProjectSet) -> list[str]:
    paths = {ROOT_PROJECT: PurePosixPath("."), **dict(projects.registry)}
    registered = ", ".join(f"{name} ({path})" for name, path in paths.items())
    lines = [
        f"Claude_Harness: projects {registered}. The project a file belongs to decides "
        "which rules, documents, and language apply; write each project's documents in its language."
    ]
    lines += [_project_line(projects, p) for p in projects.projects]
    lines += [
        f"Project {name} ({paths[name]}): {message}; its files get no harness rules."
        for name, message in projects.errors
    ]
    configs = [p.config for p in projects.projects]
    if any(c.enabled("todo") for c in configs):
        lines.append(f"Backlog: {TODO_HINT}")
    if any(c.notes_enabled() for c in configs):
        lines.append(f"Notes: {NOTES_HINT}")
    if any(c.enabled("daily") for c in configs):
        lines.append(f"Daily reports: {DAILY_HINT}")
    if any(c.enabled("techdocs") for c in configs):
        lines.append(f"{TECHDOCS_LABEL}: {TECHDOCS_HINT}")
    if any(c.part_enabled("architecture") for c in configs):
        lines.append(
            "Architecture rules: binding per project; read a project's rules before planning, designing, "
            "or changing its code; rules in skill claude-harness:architecture."
        )
        lines.append(INTERFACES_LINE)
    if any(c.part_enabled("decomposition") for c in configs):
        lines.append(DECOMPOSITION_LINE)
    if any(c.part_enabled("testing") for c in configs):
        lines.append(f"Tests: {TESTING_HINT}")
    if any(c.part_enabled("worktree") for c in configs):
        lines.append(WORKTREE_LINE)
        root = projects.session_root
        if is_git_repo(root) and base_ref_setting(root, Path.home()) != "head":
            lines.append(BASE_REF_LINE)
    if any(c.enabled("semver") for c in configs):
        lines.append(f"Release versions: {SEMVER_HINT}")
    for project in projects.projects:
        lines += [f"{project.name}: {problem}" for problem in _project_problems(projects, project)]
    return lines


def _backend_note(config: HarnessConfig) -> str:
    """Says why this backend applies when the environment, not the config file, chose it."""
    return f" (backend {config.todo_backend}: {config.todo_backend_note})" if config.todo_backend_note else ""


def _project_line(projects: ProjectSet, project: Project) -> str:
    config = project.config
    show = _shown_in(project)
    modules = ", ".join(sorted(name for name, enabled in config.modules.items() if enabled)) or "none"
    parts = [f"language {config.language}", f"modules {modules}"]
    if config.enabled("todo") and config.todo_backend == "api":
        parts.append(f"backlog {show(config.todo_path)} via API ({config.todo_api_url}){_backend_note(config)}")
    elif config.enabled("todo"):
        parts.append(f"backlog {show(config.todo_path)}/{TODO_FILE}{_backend_note(config)}")
    if config.enabled("daily"):
        parts.append(f"daily {show(config.daily_path)}/")
    if config.enabled("techdocs"):
        parts.append(f"techdocs {show(README)}, {show(config.techdocs_path)}/")
    if config.part_enabled("architecture"):
        parts.append(f"architecture {show(rules_path(config))}")
    if config.part_enabled("testing"):
        parts.append(f"tests {show(config.tests_path)}/")
    if config.enabled("semver"):
        parts.append(f"semver {_semver_summary(projects, project, show)}")
    return f"Project {project.name} ({project.path}): {'; '.join(parts)}."


def _cloud_copy_lines(root: Path, config: HarnessConfig) -> list[str]:
    """One line when the project's copy of the plugin for cloud sessions does not match cloud.export."""
    # The copy exists once per repository, at the root project (cloud.export is root-only).
    problem = copy_problem(root, config.cloud_export, Path(__file__).resolve().parent.parent)
    return [problem] if problem else []


def _project_problems(projects: ProjectSet, project: Project) -> list[str]:
    root, config, show = project.root, project.config, _shown_in(project)
    problems: list[str] = []
    if project.name == ROOT_PROJECT:
        problems += _cloud_copy_lines(root, config)
    if config.enabled("todo"):
        if config.todo_backend == "files":
            if not (root / config.todo_path / TODO_FILE).is_file():
                problems.append(_backlog_missing(config, show))
            else:
                problems += _backlog_problems(root, config)
    if config.enabled("techdocs"):
        problems += _techdocs_missing(root, config, show)
    if config.part_enabled("architecture"):
        if not (root / rules_path(config)).is_file():
            problems.append(_architecture_missing(config, show))
        else:
            problems += _scope_problems(root, config)
            problems += _inherited_problems(projects, project)
    problems += _doclink_problems(root, config, project.path)
    return problems


def _semver_summary(projects: ProjectSet, project: Project, show: Show) -> str:
    result = semver_status(projects, project)
    if result.version_text is None:
        state = "missing"
    elif result.version is None:
        state = "invalid"
    elif result.last_tag is None:
        state = f"{result.version_text}; no release tag yet"
    else:
        state = f"{result.version_text}; {len(result.unreleased or [])} unreleased commit(s) since {result.last_tag}"
    return f"{show(result.version_file)} ({state})"


def _shown_in(project: Project) -> Show:
    """Show project paths relative to the session root, where the AI works."""
    return lambda path: str(project.path / path)


def _backlog_missing(config: HarnessConfig, show: Show) -> str:
    return (
        f"Backlog: {show(config.todo_path)}/{TODO_FILE} does not exist. When the backlog "
        "becomes relevant, tell the user and ask for permission before creating it — "
        "it may just be located elsewhere."
    )


def _backlog_problems(root: Path, config: HarnessConfig) -> list[str]:
    report = validate_backlog(root / config.todo_path)
    problems = report.errors + report.notices
    if not problems:
        return []
    lines = [f"Backlog check found {len(report.errors)} errors, {len(report.notices)} notices:"]
    return lines + _limited(problems)


def _techdocs_missing(root: Path, config: HarnessConfig, show: Show) -> list[str]:
    missing = [show(p) for p in document_paths(config) if not (root / p).is_file()]
    if not missing:
        return []
    return [
        f"Missing technical docs: {', '.join(missing)}. Propose creating them from the "
        "templates when relevant; create only after approval."
    ]


def _architecture_missing(config: HarnessConfig, show: Show) -> str:
    return (
        f"Architecture rules: {show(rules_path(config))} does not exist. Propose creating it from the "
        "template when architecture becomes relevant; create only after approval."
    )


def _scope_problems(root: Path, config: HarnessConfig) -> list[str]:
    _, scope_errors = load_scopes(root, config)
    _, use_errors = load_uses(root, config)
    lines: list[str] = []
    if scope_errors:
        lines += [f"Architecture scope table has {len(scope_errors)} errors:"] + _limited(scope_errors)
    if use_errors:
        lines += [f"Architecture 'Required on use' tables have {len(use_errors)} errors:"] + _limited(use_errors)
    return lines


def _inherited_problems(projects: ProjectSet, project: Project) -> list[str]:
    errors = inherited_files(projects, project)[1] + inherited_uses(projects, project)[1]
    return [f"Inherited rules: {error}" for error in errors]


def _doclink_problems(root: Path, config: HarnessConfig, prefix: PurePosixPath = PurePosixPath(".")) -> list[str]:
    dead = dead_doc_links(root, config, prefix=prefix)
    return [f"Dead links in docs: {len(dead)}"] + _limited(dead) if dead else []


def _limited(problems: list[str]) -> list[str]:
    lines = [f"- {p}" for p in problems[:MAX_REPORTED]]
    if len(problems) > MAX_REPORTED:
        lines.append(f"- … {len(problems) - MAX_REPORTED} more")
    return lines


if __name__ == "__main__":
    sys.exit(main())

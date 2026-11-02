"""Shared client for the ToDo-Viewer's HTTP API: used by backlog_api.py and notes_api.py.

The project and the server come from the harness config of the session's project, never from arguments.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from harness_config import CONFIG_RELATIVE_PATH, ROOT_PROJECT, ConfigError, project_root
from projects import Project, load_projects
from worktree import WorktreeError, in_main_checkout

EXIT_ERROR, EXIT_USAGE, EXIT_UNREACHABLE, EXIT_NOT_REGISTERED = 1, 2, 3, 4
TIMEOUT_SECONDS = 15
CONFLICT_HINT = "read the item again and check the change before retrying; never retry blindly"


class ApiError(Exception):
    def __init__(self, message: str, exit_code: int = EXIT_ERROR):
        super().__init__(message)
        self.exit_code = exit_code


class Api:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def call(self, method: str, path: str, body: Any = None, query: dict[str, str] | None = None) -> Any:
        url = self.base_url + path + (f"?{urlencode(query)}" if query else "")
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode()
        request = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return json.loads(response.read() or b"null")
        except urllib.error.HTTPError as exc:
            raise ApiError(_http_error(exc)) from exc
        except (urllib.error.URLError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            raise ApiError(
                f"ToDo-Viewer API not reachable at {self.base_url} ({reason}). Tell the user and ask "
                "whether to start the server, work on the files instead, or stop.",
                EXIT_UNREACHABLE,
            ) from exc


def _http_error(exc: urllib.error.HTTPError) -> str:
    raw = exc.read().decode(errors="replace")
    try:
        body = json.loads(raw)
    except ValueError:
        return f"HTTP {exc.code}: {raw.strip() or exc.reason}"
    if not isinstance(body, dict) or "code" not in body:
        return f"HTTP {exc.code}: {json.dumps(body, ensure_ascii=False)}"
    message = f"HTTP {exc.code} {body['code']}: {body.get('message', '')}"
    if body.get("details"):
        message += f"\ndetails: {json.dumps(body['details'], ensure_ascii=False)}"
    if body["code"] == "version_conflict":
        message += f"\n{CONFLICT_HINT}"
    return message


def find_project(name: str, module: str = "todo") -> Project:
    """The session's project with that name; its config decides the backlog and the API URL."""
    root = project_root({"cwd": os.getcwd()})
    try:
        projects = load_projects(root)
    except ConfigError as exc:
        raise ApiError(str(exc), EXIT_USAGE) from exc
    if projects is None:
        raise ApiError(f"no {CONFIG_RELATIVE_PATH} in {root}; the harness is not set up here", EXIT_USAGE)
    project = projects.get(name)
    if project is None:
        known = ", ".join(p.name for p in projects.projects)
        raise ApiError(f"unknown project {name!r} (known: {known})", EXIT_USAGE)
    if not project.config.enabled(module):
        raise ApiError(f"module {module} is off in project {project.name}", EXIT_USAGE)
    return project


def source_folder(project: Project) -> Path:
    """The project's backlog folder in the main checkout: the server writes there, never into a worktree."""
    # No TODO.md needed: the server may keep the backlog in its database, the Markdown files are optional.
    folder = project.root / project.config.todo_path
    try:
        return in_main_checkout(folder)
    except (WorktreeError, OSError):
        # Not in a Git repository: the folder is its own source.
        return folder.resolve()


@dataclass
class Target:
    """The viewer project a command works on: its uid goes into every call, labels resolve within it."""

    api: Api
    uid: str
    name: str

    def resolve(self, label: str) -> str:
        """The uid of an element of this project by its label (archived and deleted ones included)."""
        return self.api.call("GET", f"/workspace/projects/{quote(self.uid)}/labels/{quote(label)}")["uid"]


def _mirror_matches(project: dict[str, Any], folder: Path) -> bool:
    mirror = project.get("mirror_folder")
    return bool(mirror) and Path(mirror).resolve() == folder


def own_target(api: Api, project: Project) -> Target:
    """The viewer project whose mirror folder is the project's backlog folder; never registers one."""
    folder = source_folder(project)
    for record in api.call("GET", "/workspace/projects"):
        if _mirror_matches(record, folder):
            return Target(api, record["uid"], record["name"])
    option = "" if project.name == ROOT_PROJECT else f" --project {project.name}"
    raise ApiError(
        f"backlog {folder} is not registered as a project in the ToDo-Viewer. Tell the user and ask whether to "
        f"register it; only after a yes run: backlog_api.py{option} register",
        EXIT_NOT_REGISTERED,
    )


def register_project(api: Api, project: Project) -> dict[str, Any]:
    """Register the project's backlog folder as a viewer project with a mirror; refused if it already is one."""
    folder = source_folder(project)
    for record in api.call("GET", "/workspace/projects"):
        if _mirror_matches(record, folder):
            raise ApiError(f"backlog {folder} is already registered as {record['name']!r}", EXIT_USAGE)
    # The root project is named after its main checkout (not a worktree); subprojects keep their own names.
    name = folder_name(project.root) if project.name == ROOT_PROJECT else project.name
    body = {"name": name, "mirror_folder": str(folder), "mirror_enabled": True, "auto_sync": True}
    return api.call("POST", "/workspace/projects", body)


def folder_name(root: Path) -> str:
    try:
        return in_main_checkout(root).name
    except (WorktreeError, OSError):
        return root.resolve().name


def named_target(api: Api, name: str) -> Target:
    """The viewer project with exactly this name (another project's backlog); never registers one."""
    records = api.call("GET", "/workspace/projects")
    found = [r for r in records if r.get("name") == name]
    if not found:
        known = ", ".join(str(r.get("name")) for r in records)
        raise ApiError(f"unknown source {name!r} (known: {known})", EXIT_USAGE)
    return Target(api, found[0]["uid"], found[0]["name"])


def target_for(api: Api, project: Project, source_name: str | None) -> Target:
    return own_target(api, project) if source_name is None else named_target(api, source_name)


def print_projects(api: Api) -> None:
    """One line per viewer project: its name and its mirror folder, if any."""
    print("Project | Folder")
    for record in api.call("GET", "/workspace/projects"):
        print(f"{record.get('name')} | {record.get('mirror_folder') or '-'}")


NO_PARENT = ("", "-", None)


def item_fields(target: Target, fields: dict[str, Any]) -> dict[str, Any]:
    """Backlog item fields as the server takes them: parent and dependencies by uid, required_for_parent as bool."""
    out = dict(fields)
    if "parent" in out:
        out["parent"] = None if out["parent"] in NO_PARENT else target.resolve(out["parent"])
    if "dependencies" in out:
        out["dependencies"] = [target.resolve(label) for label in out["dependencies"] or []]
    flag = out.get("required_for_parent")
    if isinstance(flag, str):
        # The backlog format writes Yes/No; the server wants true/false.
        out["required_for_parent"] = {"yes": True, "no": False}.get(flag.lower(), flag)
    return out


def version_arg(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ApiError(f"version must be the number from the last answer, got {value!r}", EXIT_USAGE) from None


def split_target(args: list[str]) -> tuple[str, str | None, list[str]]:
    """(project, source, remaining arguments) from the leading --project / --source options.

    --source names a viewer project (see the sources command) outside the session's own backlogs.
    """
    project_name, source_name = ROOT_PROJECT, None
    rest = list(args)
    while len(rest) >= 2 and rest[0] in ("--project", "--source"):
        if rest[0] == "--project":
            project_name = rest[1]
        else:
            source_name = rest[1]
        rest = rest[2:]
    if source_name is not None and project_name != ROOT_PROJECT:
        raise ApiError("--source and --project exclude each other", EXIT_USAGE)
    return project_name, source_name, rest


def stdin_json(required: bool = True) -> dict[str, Any]:
    text = sys.stdin.read()
    if not required and not text.strip():
        return {}
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ApiError(f"stdin must be a JSON object: {exc}", EXIT_USAGE) from exc
    if not isinstance(data, dict):
        raise ApiError("stdin must be a JSON object", EXIT_USAGE)
    return data


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))

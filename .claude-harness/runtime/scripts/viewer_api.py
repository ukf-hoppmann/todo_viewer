"""Shared client for the ToDo-Viewer's HTTP API: used by backlog_api.py and notes_api.py.

The project and the server come from the harness config of the session's project, never from arguments.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from harness_config import CONFIG_RELATIVE_PATH, ROOT_PROJECT, ConfigError, project_root
from projects import Project, load_projects
from worktree import WorktreeError, in_main_checkout

EXIT_ERROR, EXIT_USAGE, EXIT_UNREACHABLE = 1, 2, 3
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


def source_record(api: Api, folder: Path, project: Project) -> dict[str, Any]:
    """The ToDo-Viewer source of the project's backlog folder; registers it if missing."""
    for source in api.call("GET", "/sources"):
        # A database source has no path of its own; its Markdown folder is sync_path or markdown_path.
        paths = (source.get("path"), source.get("markdown_path"), source.get("sync_path"))
        if any(p and Path(p).resolve() == folder for p in paths):
            return source
    body = {"path": str(folder)}
    if project.name != ROOT_PROJECT:
        # Without a name the server uses the Git repository's, which subprojects share with the root.
        body["project"] = project.name
    source = api.call("POST", "/sources", body)
    print(f"registered backlog {folder} as ToDo-Viewer source {source['id']}", file=sys.stderr)
    return source


def source_id(api: Api, folder: Path, project: Project) -> str:
    return source_record(api, folder, project)["id"]


def split_target(args: list[str]) -> tuple[str, str | None, list[str]]:
    """(project, source, remaining arguments) from the leading --project / --source options.

    --source names a ToDo-Viewer source (see the sources command) outside the session's own backlogs.
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


def _source_folder_of(source: dict[str, Any]) -> str | None:
    return source.get("path") or source.get("markdown_path") or source.get("sync_path") or None


def named_source(api: Api, name: str) -> dict[str, Any]:
    """The viewer's source whose project name is exactly `name`; never registers a source."""
    sources = api.call("GET", "/sources")
    found = [s for s in sources if s.get("project") == name]
    if not found:
        known = ", ".join(str(s.get("project")) for s in sources)
        raise ApiError(f"unknown source {name!r} (known: {known})", EXIT_USAGE)
    if len(found) > 1:
        raise ApiError(f"source name {name!r} is ambiguous ({len(found)} sources)", EXIT_USAGE)
    return found[0]


def print_sources(api: Api) -> None:
    """One line per source the viewer knows: its project name and its Markdown folder, if any."""
    print("Project | Folder")
    for source in api.call("GET", "/sources"):
        print(f"{source.get('project')} | {_source_folder_of(source) or '-'}")


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
